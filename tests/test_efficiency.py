"""高效波段(效率比)策略 + AntiFrequency 濾網 單元測試。

執行： python tests/test_efficiency.py
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta

import pytz

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tmf_trader.config import Config  # noqa: E402
from tmf_trader.filters import AntiFrequency, HotHours, LossCooldown, atr_stop_target  # noqa: E402
from tmf_trader.kbar import Bar  # noqa: E402
from tmf_trader.strategy_efficiency import EfficiencyStrategy  # noqa: E402

TZ = pytz.timezone("Asia/Taipei")


def _cfg(**kw):
    c = Config()
    c.strategy = "efficiency"
    c.order_symbol = "TMF"
    c.er_length = 10
    c.er_threshold = 0.5
    c.use_antifreq = False
    for k, v in kw.items():
        setattr(c, k, v)
    return c


def _bar(p):
    return Bar(TZ.localize(datetime(2024, 6, 3, 9, 0)), p, p, p, p, 100)


# --------------------------------------------------------------------------- #
def test_efficiency_long_on_strong_uptrend():
    """一路單向上漲 → 效率比接近 1，應觸發做多。"""
    s = EfficiencyStrategy(_cfg())
    target = 0
    # 先給一段盤整暖機，再給乾淨上漲
    price = 20000
    for _ in range(12):
        target = s.on_bar(_bar(price), target)  # 持平，ER≈0
    for i in range(12):
        price += 10
        target = s.on_bar(_bar(price), target)
    assert target == 1


def test_efficiency_short_on_strong_downtrend():
    s = EfficiencyStrategy(_cfg())
    target = 0
    price = 20000
    for _ in range(12):
        target = s.on_bar(_bar(price), target)
    for i in range(12):
        price -= 10
        target = s.on_bar(_bar(price), target)
    assert target == -1


def test_efficiency_exit_when_er_crosses_zero():
    """持多後，價格反轉使 ER<0 → 應回到空手。"""
    s = EfficiencyStrategy(_cfg())
    target = 0
    price = 20000
    for _ in range(12):
        target = s.on_bar(_bar(price), target)
    for _ in range(12):
        price += 10
        target = s.on_bar(_bar(price), target)
    assert target == 1
    # 現在持多(position=+1)，價格一路下跌使 ER 轉負
    pos = 1
    for _ in range(15):
        price -= 12
        target = s.on_bar(_bar(price), pos)
        if target == 0:
            break
    assert target == 0


def test_efficiency_no_signal_in_chop():
    """純盤整（來回）效率比接近 0，不應進場。"""
    s = EfficiencyStrategy(_cfg())
    target = 0
    base = 20000
    for i in range(40):
        p = base + (10 if i % 2 == 0 else -10)
        target = s.on_bar(_bar(p), target)
    assert target == 0


# --------------------------------------------------------------------------- #
#  濾網元件
# --------------------------------------------------------------------------- #
def test_antifrequency_limits_entries():
    af = AntiFrequency(range_bars=100, max_trades=3)
    for b in (10, 20, 30):
        assert af.allows(b)
        af.on_entry(b)
    # 第 4 次在區間內 → 擋下
    assert af.allows(50) is False
    # 超過 range 後（首筆 10 已超出 200? range=100，bar=130 時 10 已離開窗 130-100=30）
    assert af.allows(131) is True  # 只剩 20,30 在窗內 → 仍 < 3


def test_loss_cooldown():
    cd = LossCooldown(cooldown_bars=10)
    cd.on_trade_closed(exit_bar_index=100, pnl=-500)  # 虧損
    assert cd.allows(105) is False
    assert cd.allows(110) is True
    cd.on_trade_closed(exit_bar_index=120, pnl=+300)  # 獲利不冷靜
    assert cd.allows(121) is True


def test_hot_hours():
    hh = HotHours([(8, 45, 13, 45), (15, 0, 23, 0)])
    assert hh.allows(TZ.localize(datetime(2024, 6, 3, 9, 0))) is True
    assert hh.allows(TZ.localize(datetime(2024, 6, 3, 14, 0))) is False  # 午休
    assert hh.allows(TZ.localize(datetime(2024, 6, 3, 16, 0))) is True
    assert hh.allows(TZ.localize(datetime(2024, 6, 3, 2, 0))) is False   # 凌晨薄量


def test_atr_stop_target():
    stop, target = atr_stop_target(entry=20000, atr=50, direction=1,
                                   stop_mult=2.0, target_mult=4.0)
    assert stop == 20000 - 100
    assert target == 20000 + 200


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
