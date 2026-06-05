"""進出場訊號邏輯。

訊號源：TXF 5 分 K 的 21MA + FVD（內外盤委託動能）。
下單標的：MXF/TMF（由 config 決定）。

進場（每根 5 分 K 收盤時評估一次，避免盤中假突破）：
    做多：上一根收盤『由下往上』突破 21MA，且 FVD >= +門檻（買方動能確認）。
    做空：上一根收盤『由上往下』跌破 21MA，且 FVD <= -門檻（賣方動能確認）。

出場：
    反向訊號、單筆停損、收盤前強制平倉（後兩者由其他模組處理）。
    本模組只負責「進場」與「均線反向出場」訊號。
"""
from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .kbar import Bar, KBarAggregator
from .market_data import FVDTracker


class Signal(Enum):
    NONE = 0
    ENTER_LONG = 1
    ENTER_SHORT = 2
    EXIT = 3        # 均線反向 → 出場（不反手，反手交給下一根訊號）


@dataclass
class StrategyState:
    prev_close: Optional[float] = None
    prev_ma: Optional[float] = None


class Strategy:
    def __init__(self, cfg, agg: KBarAggregator, fvd: FVDTracker, logger: logging.Logger):
        self.cfg = cfg
        self.agg = agg
        self.fvd = fvd
        self.log = logger
        self.state = StrategyState()
        # 保留近期 MA 值以計算斜率。
        self._ma_hist: deque[float] = deque(maxlen=cfg.ma_slope_lookback + 1)

    def on_bar_close(self, closed: Bar, current_position: int, now=None) -> Signal:
        """每當一根 5 分 K 收盤時呼叫，回傳訊號。

        now: 該根 K 棒收盤的時間戳。務必傳入，FVD 會以此時間查詢視窗；
             實盤可省略（約等於現在時間），回測則必須傳模擬時間，
             否則 FVD 會用真實 now 把歷史 tick 全部清掉而恆為 0。
        """
        ma = self.agg.ma()
        if ma is None:
            self.log.debug("21MA 尚未備齊（需 %d 根），不出訊號。", self.cfg.ma_period)
            self._remember(closed.close, ma)
            return Signal.NONE

        fvd = self.fvd.fvd(now)
        thr = self.cfg.fvd_entry_threshold
        buf = self.cfg.entry_ma_buffer_points
        prev_close, prev_ma = self.state.prev_close, self.state.prev_ma

        # 均線斜率（以 lookback 根前的 MA 比較）。
        ma_slope = None
        if len(self._ma_hist) > self.cfg.ma_slope_lookback:
            ma_slope = ma - self._ma_hist[0]
        self._ma_hist.append(ma)

        self._remember(closed.close, ma)

        # 持有部位時，均線反向先出場（含緩衝，避免在均線上下抖動被掃）。
        if current_position > 0 and closed.close < ma - buf:
            return Signal.EXIT
        if current_position < 0 and closed.close > ma + buf:
            return Signal.EXIT

        # 需要前一根資料才能判斷「穿越」。
        if prev_close is None or prev_ma is None:
            return Signal.NONE

        # 站穩均線：突破需超過緩衝點數。
        crossed_up = prev_close <= prev_ma and closed.close > ma + buf
        crossed_down = prev_close >= prev_ma and closed.close < ma - buf

        # 斜率濾網：只順 MA 斜率方向進場。
        slope_ok_long = (not self.cfg.use_ma_slope_filter) or (ma_slope is not None and ma_slope > 0)
        slope_ok_short = (not self.cfg.use_ma_slope_filter) or (ma_slope is not None and ma_slope < 0)

        self.log.info(
            "K收盤 close=%.0f MA=%.1f slope=%s FVD=%+d(門檻±%d) 部位=%d up=%s down=%s",
            closed.close, ma, f"{ma_slope:+.1f}" if ma_slope is not None else "NA",
            fvd, thr, current_position, crossed_up, crossed_down,
        )

        # 無部位才找進場（同向已有部位不加碼）。
        if current_position == 0:
            if crossed_up and fvd >= thr and slope_ok_long:
                self.log.info("→ 多方訊號（站穩MA+外盤動能%+d+MA上揚）。", fvd)
                return Signal.ENTER_LONG
            if crossed_down and fvd <= -thr and slope_ok_short:
                self.log.info("→ 空方訊號（跌破MA+內盤動能%+d+MA下彎）。", fvd)
                return Signal.ENTER_SHORT

        return Signal.NONE

    def _remember(self, close: float, ma: Optional[float]) -> None:
        self.state.prev_close = close
        self.state.prev_ma = ma
