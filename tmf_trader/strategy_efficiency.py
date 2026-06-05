"""高效波段策略（Kaufman 效率比, Efficiency Ratio）— 波段/留倉型。

為什麼是它
----------
用你真實的 txf_kbars.csv 逐年回測（swing_backtest.py / combo_backtest.py）後，
這是少數**扣成本後逐年穩定有邊際**的訊號：30 分 K、效率比 + 去除頻繁交易濾網，
與「日內高頻必被摩擦磨死」形成鮮明對比。

效率比定義
----------
    ER = (close - close[N]) / Σ|close[i] - close[i-1]|, i = (現在-N+1 .. 現在)
  分子＝N 根的『直線位移』，分母＝N 根的『總路徑長』。
  ER 接近 ±1 表單向順暢（高效率趨勢）；接近 0 表來回盤整（低效率）。

訊號（每根『已收』K 棒評估一次，回傳目標部位方向 +1/-1/0）
--------------------------------------------------------
  空手時：ER 由下向上穿越 +eff → 做多；由上向下穿越 −eff → 做空（並過 AntiFrequency 濾網）。
  持多時：ER < 0 → 出場（回到空手）。   持空時：ER > 0 → 出場。
  ❗刻意**不加固定停損**：回測證實硬停損會打斷『跌破 0 才順勢出場』的邏輯、反而變差。

本模組只決定『目標部位方向』，實際下單/平倉由 trader 以目標部位調節（target-position）執行。
"""
from __future__ import annotations

import logging
from collections import deque
from typing import Optional

from .filters import AntiFrequency
from .kbar import Bar


class EfficiencyStrategy:
    def __init__(self, cfg, logger: Optional[logging.Logger] = None):
        self.cfg = cfg
        self.log = logger or _NullLog()
        self.n = cfg.er_length
        self.eff = cfg.er_threshold
        self._closes: deque[float] = deque(maxlen=self.n + 1)
        self._prev_er: Optional[float] = None
        self._bar = 0
        self._af = AntiFrequency(cfg.antifreq_range_bars, cfg.antifreq_max_trades) \
            if cfg.use_antifreq else None

    # ------------------------------------------------------------------ #
    def on_bar(self, bar: Bar, position: int) -> int:
        """餵一根已收 K 棒，回傳『目標部位方向』 +1 多 / -1 空 / 0 空手。"""
        self._bar += 1
        self._closes.append(bar.close)
        cur = 1 if position > 0 else -1 if position < 0 else 0

        if len(self._closes) < self.n + 1:
            self._prev_er = None
            return cur  # 資料不足，維持現狀

        er = self._efficiency_ratio()
        target = cur

        if cur == 0:
            crossed_up = self._prev_er is not None and self._prev_er <= self.eff < er
            crossed_dn = self._prev_er is not None and self._prev_er >= -self.eff > er
            if crossed_up and self._allow_entry():
                target = 1
                self._record_entry()
                self.log.info("[ER] 多方訊號 ER=%.2f（穿越 +%.2f）", er, self.eff)
            elif crossed_dn and self._allow_entry():
                target = -1
                self._record_entry()
                self.log.info("[ER] 空方訊號 ER=%.2f（穿越 -%.2f）", er, self.eff)
        elif cur > 0 and er < 0:
            target = 0
            self.log.info("[ER] 多單出場 ER=%.2f（跌破 0）", er)
        elif cur < 0 and er > 0:
            target = 0
            self.log.info("[ER] 空單出場 ER=%.2f（突破 0）", er)

        self._prev_er = er
        return target

    # ------------------------------------------------------------------ #
    def _efficiency_ratio(self) -> float:
        cs = list(self._closes)            # 長度 = n+1
        straight = cs[-1] - cs[0]
        total = sum(abs(cs[k] - cs[k - 1]) for k in range(1, len(cs)))
        return straight / total if total > 0 else 0.0

    def _allow_entry(self) -> bool:
        return self._af.allows(self._bar) if self._af else True

    def _record_entry(self) -> None:
        if self._af:
            self._af.on_entry(self._bar)


class _NullLog:
    def debug(self, *a, **k): pass
    def info(self, *a, **k): pass
    def warning(self, *a, **k): pass
    def error(self, *a, **k): pass
    def critical(self, *a, **k): pass
