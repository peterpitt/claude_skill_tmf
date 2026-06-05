#!/usr/bin/env python3
r"""高效波段 × 降摩擦濾網/動態出場 — 比較 15 分 vs 30 分。

把課程模組 41(虧損冷靜期) / 42(去除頻繁交易) / 43(熱門交易時段) / 35(ATR動態停損)
逐一、以及全部一起，套到「高效波段(效率比)」訊號上，於 15m 與 30m 各跑一次真實資料
逐年回測，比較哪一種組合的『風報比 + 保本能力』最好。

成交：訊號於本根收盤產生、下一根開盤成交（無前視）；ATR 停損停利為盤中掛單觸發。
"""
from __future__ import annotations

import argparse
import os
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from tmf_trader.config import CONTRACT_SPECS, Config
from tmf_trader.filters import AntiFrequency, HotHours, LossCooldown, atr_stop_target
from tmf_trader.kbar import Bar
from orb_backtest import DEFAULT_CSV, Result, load_bars, resample
from swing_backtest import atr_series, efficiency_ratio

# 預設熱門時段：早盤全段 + 夜盤前段(15:00-23:00)，避開凌晨薄量。
HOT_WINDOWS = [(8, 45, 13, 45), (15, 0, 23, 0)]


def run_combo(bars: List[Bar], pv: int, *, n=20, eff=0.5,
              use_hot=False, use_cooldown=False, use_antifreq=False, use_atr=False,
              cooldown_bars=10, range_bars=200, max_trades=3,
              atr_len=20, atr_stop_mult=2.0, atr_target_mult=4.0,
              slippage=1.0, cost=15.0) -> Result:
    close = [b.close for b in bars]
    er = efficiency_ratio(close, n)
    atr = atr_series(bars, atr_len)

    hot = HotHours(HOT_WINDOWS) if use_hot else None
    cooldown = LossCooldown(cooldown_bars) if use_cooldown else None
    antifreq = AntiFrequency(range_bars, max_trades) if use_antifreq else None

    res = Result()
    realized = 0.0
    peak = 0.0
    pos = 0
    entry = 0.0
    stop = 0.0
    target = 0.0
    pending: Optional[Tuple] = None  # ('enter',dir) / ('exit',)

    def close_at(price, idx):
        nonlocal pos, realized, peak
        if pos == 0:
            return
        fill = price - slippage if pos > 0 else price + slippage
        pnl = (fill - entry) * pos * pv - cost
        realized += pnl
        res.trade_pnls.append(pnl)
        res.n_trades += 1
        if pnl > 0:
            res.n_wins += 1; res.gross_profit += pnl
        else:
            res.gross_loss += -pnl
        peak = max(peak, realized)
        res.max_drawdown = max(res.max_drawdown, peak - realized)
        if cooldown:
            cooldown.on_trade_closed(idx, pnl)
        pos = 0

    def filters_allow(idx, bar) -> bool:
        if hot and not hot.allows(bar.start):
            return False
        if cooldown and not cooldown.allows(idx):
            return False
        if antifreq and not antifreq.allows(idx):
            return False
        return True

    prev_er = None
    for i in range(len(bars)):
        bar = bars[i]

        # 1) 執行上一根決定的委託（本根開盤成交）
        if pending is not None:
            px = bar.open
            kind = pending[0]
            if kind == "exit":
                close_at(px, i)
            elif kind == "enter":
                d = pending[1]
                if pos != 0:
                    close_at(px, i)
                entry = px + (slippage if d > 0 else -slippage)
                pos = d
                realized -= cost
                if antifreq:
                    antifreq.on_entry(i)
                if use_atr and atr[i] is not None:
                    stop, target = atr_stop_target(entry, atr[i], d, atr_stop_mult, atr_target_mult)
                else:
                    stop, target = 0.0, 0.0
            pending = None

        # 2) ATR 停損/停利（盤中掛單，當根高低觸發；同根都中先停損）
        if pos != 0 and use_atr and stop:
            if pos > 0:
                if bar.low <= stop:
                    close_at(stop, i)
                elif target and bar.high >= target:
                    close_at(target, i)
            else:
                if bar.high >= stop:
                    close_at(stop, i)
                elif target and bar.low <= target:
                    close_at(target, i)

        # 3) 由本根收盤的效率比產生『下一根要做的事』
        e = er[i]
        desired = None
        if e is not None:
            if pos == 0:
                if prev_er is not None and prev_er <= eff < e and filters_allow(i, bar):
                    desired = ("enter", 1)
                elif prev_er is not None and prev_er >= -eff > e and filters_allow(i, bar):
                    desired = ("enter", -1)
            else:
                if pos > 0 and e < 0:
                    desired = ("exit",)
                elif pos < 0 and e > 0:
                    desired = ("exit",)
            prev_er = e
        pending = desired

    if pos != 0:
        close_at(bars[-1].close, len(bars) - 1)
    res.net_pnl = realized
    return res


def by_year(bars):
    g = defaultdict(list)
    for b in bars:
        g[b.start.year].append(b)
    return dict(sorted(g.items()))


def eval_combo(bars, pv, slippage, cost, **flags) -> Tuple[Result, int, int]:
    overall = run_combo(bars, pv, slippage=slippage, cost=cost, **flags)
    py = {y: run_combo(yb, pv, slippage=slippage, cost=cost, **flags)
          for y, yb in by_year(bars).items()}
    pos_years = sum(1 for r in py.values() if r.net_pnl > 0)
    return overall, pos_years, len(py)


CONFIGS = [
    ("基準(只有效率比訊號)",        dict()),
    ("+43 熱門時段",               dict(use_hot=True)),
    ("+42 去除頻繁交易",            dict(use_antifreq=True)),
    ("+41 虧損冷靜期",             dict(use_cooldown=True)),
    ("+35 ATR動態停損停利",         dict(use_atr=True)),
    ("全部濾網(41+42+43)",         dict(use_hot=True, use_antifreq=True, use_cooldown=True)),
    ("全部(41+42+43+35)",          dict(use_hot=True, use_antifreq=True, use_cooldown=True, use_atr=True)),
]


def main():
    ap = argparse.ArgumentParser(description="高效波段 × 濾網/出場 比較 (15m vs 30m)")
    ap.add_argument("--csv", default=DEFAULT_CSV)
    ap.add_argument("--symbol", default="TMF", choices=list(CONTRACT_SPECS.keys()))
    ap.add_argument("--cost", type=float, default=15.0)
    ap.add_argument("--slippage", type=float, default=1.0)
    args = ap.parse_args()

    if not os.path.exists(args.csv):
        print(f"❌ 找不到檔案：{args.csv}（雲端無法存取本機路徑，請本機執行或 --csv 指定）")
        return 2

    pv = CONTRACT_SPECS[args.symbol].point_value
    print(f"讀取 {args.csv} …")
    raw = load_bars(args.csv)
    print(f"原始 {len(raw):,} 根   契約 {args.symbol}({pv}元/點)  成本 {args.cost}/邊 滑價 {args.slippage}點/邊")
    print(f"熱門時段濾網窗口：{HOT_WINDOWS}")

    for tf in (15, 30):
        bars = resample(raw, tf)
        print(f"\n{'='*92}\n  時間框架 = {tf} 分  ({len(bars):,} 根)\n{'='*92}")
        print(f"{'組合':<26}{'淨利':>11}{'PF':>6}{'最大回落':>11}{'恢復':>7}"
              f"{'勝率':>7}{'交易':>7}{'獲利年':>8}")
        print("-" * 92)
        for label, flags in CONFIGS:
            r, pos_y, tot_y = eval_combo(bars, pv, args.slippage, args.cost, **flags)
            print(f"{label:<24}{r.net_pnl:>11,.0f}{min(r.profit_factor,99):>6.2f}"
                  f"{r.max_drawdown:>11,.0f}{r.recovery:>7.2f}{r.win_rate*100:>6.1f}%"
                  f"{r.n_trades:>7}{pos_y:>5}/{tot_y}")

    print("\n判讀提示：『恢復』(淨利/最大回落) 越高越保本；對 70,000 本金，"
          "最大回落最好 < ~23,000(≈33%)。濾網的目的不是衝高淨利，而是**砍交易次數、"
          "壓低回落、提升恢復係數**。")


if __name__ == "__main__":
    main()
