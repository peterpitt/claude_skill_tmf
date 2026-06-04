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

    def on_bar_close(self, closed: Bar, current_position: int) -> Signal:
        """每當一根 5 分 K 收盤時呼叫，回傳訊號。"""
        ma = self.agg.ma()
        if ma is None:
            self.log.debug("21MA 尚未備齊（需 %d 根），不出訊號。", self.cfg.ma_period)
            self._remember(closed.close, ma)
            return Signal.NONE

        fvd = self.fvd.fvd()
        thr = self.cfg.fvd_entry_threshold
        prev_close, prev_ma = self.state.prev_close, self.state.prev_ma
        self._remember(closed.close, ma)

        # 需要前一根資料才能判斷「穿越」。
        if prev_close is None or prev_ma is None:
            return Signal.NONE

        crossed_up = prev_close <= prev_ma and closed.close > ma
        crossed_down = prev_close >= prev_ma and closed.close < ma

        self.log.info(
            "K收盤 close=%.0f MA21=%.1f FVD=%+d (門檻±%d) 部位=%d | up=%s down=%s",
            closed.close, ma, fvd, thr, current_position, crossed_up, crossed_down,
        )

        # 持有部位時，均線反向先出場。
        if current_position > 0 and closed.close < ma:
            return Signal.EXIT
        if current_position < 0 and closed.close > ma:
            return Signal.EXIT

        # 無部位才找進場（同向已有部位不加碼）。
        if current_position == 0:
            if crossed_up and fvd >= thr:
                self.log.info("→ 多方訊號成立（突破 21MA + 外盤動能 %+d）。", fvd)
                return Signal.ENTER_LONG
            if crossed_down and fvd <= -thr:
                self.log.info("→ 空方訊號成立（跌破 21MA + 內盤動能 %+d）。", fvd)
                return Signal.ENTER_SHORT

        return Signal.NONE

    def _remember(self, close: float, ma: Optional[float]) -> None:
        self.state.prev_close = close
        self.state.prev_ma = ma
