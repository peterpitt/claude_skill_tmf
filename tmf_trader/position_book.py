"""內部部位簿。

為什麼不只靠 api.list_positions()？
  - 主機查詢有延遲，斷路器需要『毫秒級』的損益估算。
  - 自己用成交回報維護一份 source of truth，再定期與主機對帳，
    才能在風控執行緒裡安全地即時加總損益。

設計：當沖、淨部位制（同一商品只持單一方向）。
  - position > 0 表多單口數，< 0 表空單口數。
  - avg_price 為目前淨部位的加權平均成本。
  - realized_pnl_twd 為當日已實現損益（含手續費可自行擴充）。
"""
from __future__ import annotations

import threading
from dataclasses import dataclass


@dataclass
class _Fill:
    action: str   # "Buy" / "Sell"
    price: float
    qty: int


class PositionBook:
    def __init__(self, point_value: int):
        self._point_value = point_value
        self._lock = threading.RLock()
        self.position: int = 0          # 淨口數，正多負空
        self.avg_price: float = 0.0     # 加權平均成本
        self.realized_pnl_twd: float = 0.0
        self.last_price: float = 0.0    # 最新成交價，用於估未實現損益

    # ------------------------------------------------------------------ #
    def update_last_price(self, price: float) -> None:
        if price and price > 0:
            with self._lock:
                self.last_price = price

    # ------------------------------------------------------------------ #
    def on_fill(self, action: str, price: float, qty: int) -> None:
        """成交回報進來時更新部位與已實現損益。

        以「先抵消反向部位、再建立同向部位」的方式處理，
        抵消的部分結算為已實現損益。
        """
        if qty <= 0 or price <= 0:
            return
        with self._lock:
            signed = qty if action == "Buy" else -qty
            self._apply(signed, price)
            self.last_price = price

    def _apply(self, signed_qty: int, price: float) -> None:
        pos = self.position
        # 同向加碼或從零開始：更新加權平均。
        if pos == 0 or (pos > 0) == (signed_qty > 0):
            new_pos = pos + signed_qty
            if new_pos != 0:
                self.avg_price = (
                    abs(pos) * self.avg_price + abs(signed_qty) * price
                ) / abs(new_pos)
            self.position = new_pos
            return

        # 反向：先平倉抵消，超出的部分反手建倉。
        closing = min(abs(pos), abs(signed_qty))
        direction = 1 if pos > 0 else -1
        # 平掉 closing 口的已實現損益。
        self.realized_pnl_twd += (
            (price - self.avg_price) * direction * closing * self._point_value
        )
        remaining = abs(signed_qty) - closing
        new_pos = pos + signed_qty
        self.position = new_pos
        if new_pos == 0:
            self.avg_price = 0.0
        elif remaining > 0:
            # 反手後新部位成本即為這次成交價。
            self.avg_price = price

    # ------------------------------------------------------------------ #
    def unrealized_pnl_twd(self, price: float | None = None) -> float:
        with self._lock:
            if self.position == 0:
                return 0.0
            p = price if price and price > 0 else self.last_price
            if not p:
                return 0.0
            direction = 1 if self.position > 0 else -1
            return (p - self.avg_price) * direction * abs(self.position) * self._point_value

    def total_pnl_twd(self, price: float | None = None) -> float:
        with self._lock:
            return self.realized_pnl_twd + self.unrealized_pnl_twd(price)

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "position": self.position,
                "avg_price": self.avg_price,
                "last_price": self.last_price,
                "realized": round(self.realized_pnl_twd, 1),
                "unrealized": round(self.unrealized_pnl_twd(), 1),
                "total": round(self.total_pnl_twd(), 1),
            }

    def reconcile(self, broker_position: int, broker_avg_price: float) -> bool:
        """與主機回報的部位對帳；不一致時以主機為準並回報 True。"""
        with self._lock:
            if broker_position != self.position:
                self.position = broker_position
                self.avg_price = broker_avg_price if broker_position != 0 else 0.0
                return True
            return False
