"""統一 logging：同時輸出到終端機（tmux 看得到）與每日 log 檔。

交易系統的 log 等同黑盒子，斷路器、下單、成交都必須留痕。
"""
from __future__ import annotations

import logging
import os
import sys
from datetime import datetime

from .config import TZ


class _TaipeiFormatter(logging.Formatter):
    """讓 log 時間戳一律使用 Asia/Taipei。"""

    def formatTime(self, record, datefmt=None):  # noqa: N802 (logging API 命名)
        dt = datetime.fromtimestamp(record.created, TZ)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.strftime("%Y-%m-%d %H:%M:%S")


def setup_logger(log_dir: str = "logs", name: str = "tmf") -> logging.Logger:
    """建立（或取得）全域 logger。重複呼叫不會重複加 handler。"""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    fmt = _TaipeiFormatter(
        "%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 終端機
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    # 檔案（每天一檔）
    os.makedirs(log_dir, exist_ok=True)
    today = datetime.now(TZ).strftime("%Y%m%d")
    fh = logging.FileHandler(os.path.join(log_dir, f"trade_{today}.log"), encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger
