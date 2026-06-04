"""TXF 報價處理：tick → K 棒；tick → FVD（內外盤委託動能）。

FVD 定義（本系統採用）
---------------------
逐筆成交的 tick_type 可判斷主動方向：
    tick_type == 1 → 外盤成交（主動買，推升）
    tick_type == 2 → 內盤成交（主動賣，打壓）
    tick_type == 0 → 無法判定

FVD = 最近 N 秒內 (外盤量 - 內盤量) 的累積值。
    FVD > 0 表買方動能占優；FVD < 0 表賣方動能占優。

另外保留最新一檔 BidAsk 的委買/委賣總量比，作為輔助參考。
"""
from __future__ import annotations

import threading
from collections import deque
from datetime import datetime, timedelta
from typing import Optional

from .config import TZ


class FVDTracker:
    def __init__(self, window_seconds: int):
        self._window = timedelta(seconds=window_seconds)
        self._lock = threading.RLock()
        # 每筆: (時間, 帶號量) 外盤+ 內盤-
        self._events: deque[tuple[datetime, int]] = deque()
        self._bid_total: int = 0   # 最新委買總量
        self._ask_total: int = 0   # 最新委賣總量

    def add_tick(self, ts: datetime, volume: int, tick_type: int) -> None:
        if volume <= 0:
            return
        if ts.tzinfo is None:
            ts = TZ.localize(ts)
        with self._lock:
            if tick_type == 1:        # 外盤（主動買）
                self._events.append((ts, volume))
            elif tick_type == 2:      # 內盤（主動賣）
                self._events.append((ts, -volume))
            else:
                return
            self._evict(ts)

    def add_bidask(self, bid_total: int, ask_total: int) -> None:
        with self._lock:
            self._bid_total = bid_total
            self._ask_total = ask_total

    def _evict(self, now: datetime) -> None:
        cutoff = now - self._window
        while self._events and self._events[0][0] < cutoff:
            self._events.popleft()

    def fvd(self, now: Optional[datetime] = None) -> int:
        """回傳目前視窗內的內外盤動能淨值。"""
        with self._lock:
            if now is None:
                now = datetime.now(TZ)
            self._evict(now)
            return sum(v for _, v in self._events)

    def book_imbalance(self) -> float:
        """委買/委賣失衡比：>0 偏買、<0 偏賣，範圍約 [-1, 1]。"""
        with self._lock:
            total = self._bid_total + self._ask_total
            if total <= 0:
                return 0.0
            return (self._bid_total - self._ask_total) / total
