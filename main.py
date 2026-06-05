#!/usr/bin/env python3
"""TMF/MXF 台指期自動當沖系統 — 進入點。

用法：
    python main.py            # 依 .env 設定執行（預設 DRY_RUN）
    python main.py --check    # 只檢查設定與時段，不連線、不下單

安全預設：未設定 .env 時一律 DRY_RUN，不會送出任何真實委託。
"""
from __future__ import annotations

import argparse
import sys

from dotenv import load_dotenv

from tmf_trader.config import Config
from tmf_trader.logger import setup_logger
from tmf_trader.trader import Trader


def main() -> int:
    parser = argparse.ArgumentParser(description="TMF/MXF 台指期自動當沖系統")
    parser.add_argument("--check", action="store_true", help="只檢查設定與時段，不連線")
    args = parser.parse_args()

    load_dotenv()
    # 最終上線設定：TMF 1 口、高效波段(30分)留倉版；再以 .env 覆寫安全閘與金鑰。
    cfg = Config.from_env(base=Config.tmf_swing())
    log = setup_logger(cfg.log_dir)

    try:
        cfg.validate()
    except ValueError as e:
        log.error("設定檢查失敗: %s", e)
        return 2

    # 最後一道防線：想跑真錢卻沒解開確認鎖 → 擋下。
    if not cfg.dry_run and not cfg.simulation and cfg.live_confirm != "I_UNDERSTAND_THE_RISK":
        log.error(
            "偵測到『正式主機 + 非 DRY_RUN』，但未解開最終確認鎖。\n"
            "若你真的要用真錢交易，請在 .env 設定 "
            "LIVE_TRADING_CONFIRM=I_UNDERSTAND_THE_RISK。\n"
            "為保護資金，本次拒絕啟動。"
        )
        return 3

    if args.check:
        from tmf_trader.session import SessionManager
        sm = SessionManager(cfg)
        now = sm.now()
        log.info("設定檢查通過。")
        log.info("現在時間=%s 時段=%s 可進場=%s 強制平倉窗=%s",
                 now.strftime("%Y-%m-%d %H:%M:%S"),
                 sm.current_session(now).value, sm.can_enter(now),
                 sm.in_force_close_window(now))
        log.info("下單契約=%s 每點=%d 元 單筆停損≈%.0f 元 斷路器=%.0f 元",
                 cfg.order_symbol, cfg.order_spec.point_value,
                 cfg.per_trade_stop_twd(), cfg.daily_max_loss_twd)
        return 0

    trader = Trader(cfg, log)
    try:
        trader.start()
    except Exception as e:  # noqa: BLE001
        log.exception("系統發生未預期錯誤，嘗試安全關閉: %s", e)
        try:
            trader.shutdown()
        except Exception:  # noqa: BLE001
            pass
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
