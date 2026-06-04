"""5 分 K 棒合成 + 21MA。

由 TXF 的逐筆 tick 自行合成 K 棒，不依賴主機 K 線，
這樣早盤/夜盤切換、跨日都能完全掌握。
"""
from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .config import TZ


@dataclass
class Bar:
    start: datetime  # 該 K 棒起始時間（已對齊到 N 分鐘）
    open: float
    high: float
    low: float
    close: float
    volume: int

    def __repr__(self) -> str:
        return (
            f"Bar({self.start:%H:%M} O={self.open} H={self.high} "
            f"L={self.low} C={self.close} V={self.volume})"
        )


class KBarAggregator:
    """把 tick 累積成固定分鐘 K 棒，並維護收盤價的移動平均。

    使用方式：
        agg = KBarAggregator(5, 21)
        closed = agg.add_tick(ts, price, vol)   # 跨棒時回傳「剛收掉的上一根」
        if closed: ...用 agg.ma() 與 closed 做訊號...
    """

    def __init__(self, minutes: int, ma_period: int):
        self._minutes = minutes
        self._ma_period = ma_period
        self._lock = threading.RLock()
        self._cur: Optional[Bar] = None
        self._closes: deque[float] = deque(maxlen=ma_period)
        self._closed_bars: deque[Bar] = deque(maxlen=max(ma_period * 2, 100))

    # ------------------------------------------------------------------ #
    def _bucket_start(self, ts: datetime) -> datetime:
        """把時間對齊到 N 分鐘的起點。"""
        if ts.tzinfo is None:
            ts = TZ.localize(ts)
        minute = (ts.minute // self._minutes) * self._minutes
        return ts.replace(minute=minute, second=0, microsecond=0)

    def add_tick(self, ts: datetime, price: float, volume: int) -> Optional[Bar]:
        """餵一筆 tick。若進入新 K 棒，回傳剛收掉的上一根，否則 None。"""
        if price is None or price <= 0:
            return None
        with self._lock:
            start = self._bucket_start(ts)
            closed = None

            if self._cur is None:
                self._cur = Bar(start, price, price, price, price, volume)
                return None

            if start > self._cur.start:
                # 跨棒：把目前這根收掉。
                closed = self._cur
                self._closes.append(closed.close)
                self._closed_bars.append(closed)
                self._cur = Bar(start, price, price, price, price, volume)
            else:
                b = self._cur
                b.high = max(b.high, price)
                b.low = min(b.low, price)
                b.close = price
                b.volume += volume
            return closed

    # ------------------------------------------------------------------ #
    def ma(self) -> Optional[float]:
        """已收 K 棒的 21MA；資料不足回 None。"""
        with self._lock:
            if len(self._closes) < self._ma_period:
                return None
            return sum(self._closes) / len(self._closes)

    def last_closed(self) -> Optional[Bar]:
        with self._lock:
            return self._closed_bars[-1] if self._closed_bars else None

    def current_price(self) -> Optional[float]:
        with self._lock:
            return self._cur.close if self._cur else None

    def ready(self) -> bool:
        with self._lock:
            return len(self._closes) >= self._ma_period
