"""核心邏輯單元測試（不需 shioaji、不需網路）。

聚焦在『會影響真錢』的三塊：
  1. 部位簿損益計算（PositionBook）
  2. 風控斷路器觸發（CircuitBreaker）
  3. 時段與出手次數（SessionManager）

執行： python -m pytest tests/ -v   或   python tests/test_core.py
"""
from __future__ import annotations

import os
import sys
import time
from datetime import datetime

import pytz

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tmf_trader.config import Config  # noqa: E402
from tmf_trader.logger import setup_logger  # noqa: E402
from tmf_trader.position_book import PositionBook  # noqa: E402
from tmf_trader.risk import CircuitBreaker  # noqa: E402
from tmf_trader.session import SessionManager, SessionType  # noqa: E402

TZ = pytz.timezone("Asia/Taipei")


# --------------------------------------------------------------------------- #
#  PositionBook
# --------------------------------------------------------------------------- #
def test_long_roundtrip_profit():
    book = PositionBook(point_value=10)  # TMF
    book.on_fill("Buy", 20000, 1)
    assert book.position == 1
    assert book.avg_price == 20000
    book.on_fill("Sell", 20050, 1)       # +50 點
    assert book.position == 0
    assert abs(book.realized_pnl_twd - 50 * 10) < 1e-6


def test_short_roundtrip_loss():
    book = PositionBook(point_value=50)  # MXF
    book.on_fill("Sell", 20000, 1)
    book.on_fill("Buy", 20030, 1)        # 空單被軋 30 點
    assert book.position == 0
    assert abs(book.realized_pnl_twd - (-30 * 50)) < 1e-6


def test_unrealized_pnl():
    book = PositionBook(point_value=10)
    book.on_fill("Buy", 20000, 2)
    assert book.unrealized_pnl_twd(20010) == 10 * 10 * 2  # +10點 x 10 x 2口


def test_avg_price_on_scale_in():
    book = PositionBook(point_value=10)
    book.on_fill("Buy", 20000, 1)
    book.on_fill("Buy", 20100, 1)
    assert book.position == 2
    assert abs(book.avg_price - 20050) < 1e-6


def test_reverse_through_zero():
    book = PositionBook(point_value=10)
    book.on_fill("Buy", 20000, 1)
    book.on_fill("Sell", 20020, 3)   # 平 1 口(+20點) 後反手空 2 口 @20020
    assert book.position == -2
    assert abs(book.realized_pnl_twd - 20 * 10) < 1e-6
    assert abs(book.avg_price - 20020) < 1e-6


# --------------------------------------------------------------------------- #
#  CircuitBreaker
# --------------------------------------------------------------------------- #
def test_circuit_breaker_trips_on_loss():
    cfg = Config()
    cfg.order_symbol = "TMF"
    cfg.daily_max_loss_twd = 2890
    cfg.risk_poll_seconds = 0.05
    log = setup_logger("logs", name="test")
    book = PositionBook(cfg.order_spec.point_value)

    flattened = {"called": False}
    cancelled = {"called": False}

    def flatten(reason):
        flattened["called"] = True
        book.position = 0  # 模擬平倉

    def cancel():
        cancelled["called"] = True

    cb = CircuitBreaker(cfg, book, flatten, cancel, log, get_price=lambda: book.last_price)

    # 建立一個會超過斷路器的虧損部位（TMF $10/點，需 -289 點才 -2890）。
    book.on_fill("Buy", 20000, 1)
    book.update_last_price(19700)   # -300 點 = -3000 TWD < -2890

    cb.start()
    time.sleep(0.3)
    cb.stop()

    assert cb.tripped is True
    assert flattened["called"] is True
    assert cancelled["called"] is True


def test_circuit_breaker_does_not_trip_within_limit():
    cfg = Config()
    cfg.order_symbol = "TMF"
    cfg.daily_max_loss_twd = 2890
    cfg.risk_poll_seconds = 0.05
    log = setup_logger("logs", name="test2")
    book = PositionBook(cfg.order_spec.point_value)
    cb = CircuitBreaker(cfg, book, lambda r: None, lambda: None, log,
                        get_price=lambda: book.last_price)

    book.on_fill("Buy", 20000, 1)
    book.update_last_price(19900)   # -100 點 = -1000 TWD，未達門檻

    cb.start()
    time.sleep(0.2)
    cb.stop()
    assert cb.tripped is False


# --------------------------------------------------------------------------- #
#  SessionManager
# --------------------------------------------------------------------------- #
def _dt(h, m):
    return TZ.localize(datetime(2026, 6, 4, h, m))


def test_session_classification():
    sm = SessionManager(Config())
    assert sm.current_session(_dt(9, 0)) == SessionType.DAY
    assert sm.current_session(_dt(13, 50)) == SessionType.NONE
    assert sm.current_session(_dt(16, 0)) == SessionType.NIGHT
    assert sm.current_session(_dt(2, 0)) == SessionType.NIGHT      # 凌晨夜盤
    assert sm.current_session(_dt(6, 0)) == SessionType.NONE


def test_force_close_window():
    sm = SessionManager(Config())
    # 早盤 13:45 收，前 15 分鐘 = 13:30 起為強制平倉窗。
    assert sm.in_force_close_window(_dt(13, 29)) is False
    assert sm.in_force_close_window(_dt(13, 31)) is True
    assert sm.is_tradable(_dt(13, 31)) is False


def test_entry_count_per_session_independent():
    cfg = Config()
    cfg.max_entries_per_session = 4
    sm = SessionManager(cfg)

    day = _dt(9, 0)
    for i in range(4):
        assert sm.can_enter(day) is True
        sm.record_entry(day)
    assert sm.can_enter(day) is False   # 早盤用完 4 次

    night = _dt(16, 0)
    assert sm.can_enter(night) is True  # 夜盤獨立重新計算


# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    funcs = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for fn in funcs:
        try:
            fn()
            print(f"PASS  {fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL  {fn.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            print(f"ERROR {fn.__name__}: {e}")
    print(f"\n{passed}/{len(funcs)} 通過")
    sys.exit(0 if passed == len(funcs) else 1)
