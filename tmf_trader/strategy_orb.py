"""開盤區間突破策略 (Opening Range Breakout, ORB) — 早盤 / 夜盤通用。

為什麼選 ORB？
--------------
1. **完全 bar-based、可被 K 線完整回測**：不依賴逐筆內外盤(FVD)，
   你手上的 txf_kbars.csv 能 100% 驗證它（這是相對前一版最大的優勢）。
2. **指數期貨少數有長期實證支持的日內邊際**：開盤後 N 分鐘形成的區間，
   被『帶量、且站在當盤 VWAP 正確一側』地突破時，常有延續性。
3. **天生符合你的規則**：早盤(08:45)、夜盤(15:00)各自獨立開盤 → 各自一套
   開盤區間與出手次數；每盤最多 4 次；當日 -2890 鎖單。

訊號邏輯（每根 K 棒收盤評估一次）
--------------------------------
  開盤後 `or_minutes` 分鐘內：只記錄區間高低 (OR_high / OR_low)，不進場。
  區間成形後：
    做多：收盤 > OR_high + buffer，且（若開啟）收盤站上當盤 VWAP、且區間不過寬。
    做空：收盤 < OR_low  - buffer，且（若開啟）收盤跌破當盤 VWAP、且區間不過寬。
  進場時回傳建議停損價（區間另一側 與 固定點數 取較近者，保護單筆風險）。

出場（停損/停利/強平）由呼叫端（回測器或實盤 trader）負責執行，
本模組只負責「何時進場、停損設哪」與「反向突破→出場」。
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .kbar import Bar
from .session import SessionManager, SessionType


class Signal(Enum):
    NONE = 0
    ENTER_LONG = 1
    ENTER_SHORT = 2
    EXIT = 3


@dataclass
class Decision:
    signal: Signal = Signal.NONE
    stop_price: Optional[float] = None   # 進場時建議的初始停損價
    reason: str = ""


@dataclass
class _SessionState:
    key: tuple                      # (交易日, 時段)
    or_high: float = float("-inf")
    or_low: float = float("inf")
    or_locked: bool = False         # 開盤區間是否已封存
    vwap_pv: float = 0.0            # Σ(典型價×量)
    vwap_v: float = 0.0            # Σ量
    bars_seen: int = 0

    @property
    def or_width(self) -> float:
        if self.or_high == float("-inf"):
            return float("inf")
        return self.or_high - self.or_low

    def vwap(self) -> Optional[float]:
        return (self.vwap_pv / self.vwap_v) if self.vwap_v > 0 else None


class ORBStrategy:
    def __init__(self, cfg, session: SessionManager, logger: Optional[logging.Logger] = None):
        self.cfg = cfg
        self.session = session
        self.log = logger or _NullLog()
        self._st: Optional[_SessionState] = None

    # ------------------------------------------------------------------ #
    def on_bar(self, bar: Bar, position: int, now) -> Decision:
        """餵一根『已收盤』的 K 棒，回傳決策。

        bar.start 應為該 K 棒起始時間；now 為該 K 棒收盤時間（用於時段判斷）。
        """
        sess = self.session.current_session(now)
        if sess == SessionType.NONE:
            return Decision(Signal.NONE)

        key = (self.session._trading_day_key(now), sess)
        if self._st is None or self._st.key != key:
            self._st = _SessionState(key=key)  # 新時段：重置開盤區間與 VWAP

        st = self._st
        st.bars_seen += 1

        # VWAP 累積（典型價 = (H+L+C)/3）。
        typ = (bar.high + bar.low + bar.close) / 3.0
        st.vwap_pv += typ * max(bar.volume, 1)
        st.vwap_v += max(bar.volume, 1)

        mins = self.session.minutes_since_open(now)
        mins = mins if mins is not None else 0.0

        # --- 開盤區間建立期：只記錄高低，不進場 ---
        if mins < self.cfg.or_minutes:
            st.or_high = max(st.or_high, bar.high)
            st.or_low = min(st.or_low, bar.low)
            return Decision(Signal.NONE, reason="building_OR")

        # 區間建立完成後第一次封存。
        if not st.or_locked:
            st.or_locked = True
            self.log.info("[ORB] %s 開盤區間封存 H=%.0f L=%.0f 寬=%.0f",
                          sess.value, st.or_high, st.or_low, st.or_width)

        if st.or_high == float("-inf"):
            return Decision(Signal.NONE, reason="no_OR")

        # --- 反向突破出場（持倉時優先）---
        if position > 0 and bar.close < st.or_low:
            return Decision(Signal.EXIT, reason="break_back_below_OR")
        if position < 0 and bar.close > st.or_high:
            return Decision(Signal.EXIT, reason="break_back_above_OR")

        if position != 0:
            return Decision(Signal.NONE)

        # --- 過濾過寬區間（已大幅移動，追高風險大）---
        if self.cfg.orb_max_or_points > 0 and st.or_width > self.cfg.orb_max_or_points:
            return Decision(Signal.NONE, reason="OR_too_wide")

        buf = self.cfg.orb_breakout_buffer_points
        vwap = st.vwap()
        long_break = bar.close > st.or_high + buf
        short_break = bar.close < st.or_low - buf

        # VWAP 趨勢濾網。
        if self.cfg.orb_use_vwap_filter and vwap is not None:
            long_ok = bar.close >= vwap
            short_ok = bar.close <= vwap
        else:
            long_ok = short_ok = True

        if long_break and long_ok:
            stop = self._calc_stop(entry=bar.close, or_opposite=st.or_low, is_long=True)
            return Decision(Signal.ENTER_LONG, stop_price=stop, reason="break_up")
        if short_break and short_ok:
            stop = self._calc_stop(entry=bar.close, or_opposite=st.or_high, is_long=False)
            return Decision(Signal.ENTER_SHORT, stop_price=stop, reason="break_down")

        return Decision(Signal.NONE)

    # ------------------------------------------------------------------ #
    def _calc_stop(self, entry: float, or_opposite: float, is_long: bool) -> float:
        """初始停損：取『區間另一側』與『固定點數停損』中較近的一邊，控制單筆風險。"""
        fixed = self.cfg.per_trade_stop_points
        if is_long:
            stop_fixed = entry - fixed
            return max(stop_fixed, or_opposite)   # 較近(較高)者
        else:
            stop_fixed = entry + fixed
            return min(stop_fixed, or_opposite)   # 較近(較低)者


class _NullLog:
    def debug(self, *a, **k): pass
    def info(self, *a, **k): pass
    def warning(self, *a, **k): pass
    def error(self, *a, **k): pass
    def critical(self, *a, **k): pass
