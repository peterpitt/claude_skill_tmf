"""風控斷路器（獨立執行緒）。

這是整個系統的『保命裝置』，刻意獨立於主交易邏輯之外運作：
即使主訊號流程卡住或出錯，這個執行緒仍會持續監控損益。

職責：
  每 risk_poll_seconds 秒：
    1. 加總「已實現損益 + 未平倉浮動損益」。
    2. 當日累計虧損達 daily_max_loss_twd → 觸發斷路器（只觸發一次）：
         a. 市價平倉所有未平倉部位。
         b. 撤銷所有未成交委託。
         c. 寫 log，並設定『當日下單權限關閉』旗標，主程序據此停手。

設計重點：
  - 斷路器只會 latch 一次，避免重複送平倉單。
  - 觸發後 tripped 旗標維持 True 直到隔日（由主程序在換日時 reset）。
  - 平倉動作交給注入的 callback，與 broker 解耦，方便測試。
"""
from __future__ import annotations

import logging
import threading
from datetime import datetime
from typing import Callable, Optional

from .config import TZ, Config
from .position_book import PositionBook


class CircuitBreaker:
    def __init__(
        self,
        cfg: Config,
        book: PositionBook,
        flatten_all: Callable[[str], None],
        cancel_all: Callable[[], None],
        logger: logging.Logger,
        get_price: Optional[Callable[[], float]] = None,
    ):
        self.cfg = cfg
        self.book = book
        self._flatten_all = flatten_all
        self._cancel_all = cancel_all
        self.log = logger
        self._get_price = get_price

        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._tripped = threading.Event()    # 斷路器是否已觸發
        self._trading_day: str = self._today_key()
        self._worst_pnl: float = 0.0         # 當日最差損益（觀測用）

    # ------------------------------------------------------------------ #
    @property
    def tripped(self) -> bool:
        return self._tripped.is_set()

    def _today_key(self) -> str:
        dt = datetime.now(TZ)
        # 凌晨 0~5 點仍屬前一交易日的夜盤。
        if dt.time() < self.cfg.night_close:
            from datetime import timedelta
            return (dt.date() - timedelta(days=1)).isoformat()
        return dt.date().isoformat()

    def reset_for_new_day(self) -> None:
        """換日重置：恢復下單權限、清掉觸發狀態。由主程序在新交易日呼叫。"""
        self._tripped.clear()
        self._worst_pnl = 0.0
        self._trading_day = self._today_key()
        self.book.realized_pnl_twd = 0.0
        self.log.info("【風控】換日重置，恢復當日下單權限。交易日=%s", self._trading_day)

    # ------------------------------------------------------------------ #
    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="CircuitBreaker", daemon=True)
        self._thread.start()
        self.log.info(
            "【風控】斷路器已啟動：當日虧損上限 %.0f TWD，每 %.1fs 檢查一次。",
            self.cfg.daily_max_loss_twd, self.cfg.risk_poll_seconds,
        )

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)

    # ------------------------------------------------------------------ #
    def _run(self) -> None:
        while not self._stop.wait(self.cfg.risk_poll_seconds):
            try:
                self._check_once()
            except Exception as e:  # noqa: BLE001  風控絕不能因例外而停擺
                self.log.error("【風控】檢查時發生例外（已忽略續跑）: %s", e)

    def _check_once(self) -> None:
        # 自動換日（凌晨 05:00 之後、或新的一天早盤）。
        if self._today_key() != self._trading_day and not self.tripped:
            self.reset_for_new_day()

        price = self._get_price() if self._get_price else None
        total = self.book.total_pnl_twd(price)
        if total < self._worst_pnl:
            self._worst_pnl = total

        if self.tripped:
            return

        # daily_max_loss_twd <= 0 表示停用斷路器（波段模式可能如此設定）。
        if self.cfg.daily_max_loss_twd <= 0:
            return

        # 觸發條件：累計虧損達門檻（total 為負，故比較 <= -limit）。
        if total <= -self.cfg.daily_max_loss_twd:
            self._trip(total)

    def _trip(self, total_pnl: float) -> None:
        self._tripped.set()
        snap = self.book.snapshot()
        self.log.critical(
            "============ 風控斷路器觸發 ============\n"
            "  當日累計損益 = %.1f TWD（門檻 -%.0f）\n"
            "  部位快照 = %s\n"
            "  動作：市價平倉 → 撤銷掛單 → 鎖定當日下單權限",
            total_pnl, self.cfg.daily_max_loss_twd, snap,
        )
        # 1. 市價平倉所有部位。
        try:
            self._flatten_all("CIRCUIT_BREAKER")
        except Exception as e:  # noqa: BLE001
            self.log.critical("【風控】平倉失敗！請人工介入！%s", e)
        # 2. 撤銷所有掛單。
        try:
            self._cancel_all()
        except Exception as e:  # noqa: BLE001
            self.log.critical("【風控】撤單失敗！請人工介入！%s", e)
        # 3. 旗標已設，主程序會停止下單。
        self.log.critical("============ 斷路器處置完成，今日停止交易 ============")
