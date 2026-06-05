#!/usr/bin/env python3
r"""時間過濾型『前高/前低突破』日內回測（不留倉 + 單日 −2890）。

回應需求：
  早盤：10:00 之後，突破參考高→做多、跌破參考低→做空。
  夜盤：美股開盤後 30 分鐘（≈22:00 夏令）之後，同樣突破/跌破參考高低。
  全程**不留倉**（收盤前 15 分強制平倉）、早夜盤獨立出手上限、單日累計虧損
  達 −2890 即鎖單。

『前高/前低』兩種常見定義都測，讓資料決定：
  --ref openrange : 參考 = 本盤『時間窗(開盤→cutoff)』的高低（開盤區間突破）。
  --ref prevday   : 參考 = 前一交易日的最高/最低。

出場：對向突破、單筆停損(--stop 點)、或收盤前強平、或 −2890 鎖單。
成交：5 分 K 收盤觸發、隔根開盤成交（無前視）；停損為盤中掛單。
"""
from __future__ import annotations

import argparse
import os
from collections import defaultdict
from datetime import time, timedelta
from typing import Dict, List, Optional, Tuple

from tmf_trader.config import CONTRACT_SPECS, Config
from tmf_trader.kbar import Bar
from tmf_trader.session import SessionManager, SessionType
from orb_backtest import DEFAULT_CSV, Result, load_bars, resample


def trading_day_hl(bars: List[Bar], sm: SessionManager) -> Dict[str, Tuple[float, float]]:
    """每個交易日(早+夜歸屬)的最高/最低，供 prevday 參考。"""
    hl: Dict[str, List[float]] = {}
    for b in bars:
        k = sm._trading_day_key(b.start)
        if k not in hl:
            hl[k] = [b.high, b.low]
        else:
            hl[k][0] = max(hl[k][0], b.high)
            hl[k][1] = min(hl[k][1], b.low)
    return {k: (v[0], v[1]) for k, v in hl.items()}


def run(bars: List[Bar], cfg: Config, pv: int, *, ref="openrange",
        day_cutoff=time(10, 0), night_cutoff=time(22, 0),
        stop_points=40.0, slippage=1.0, cost=15.0) -> Result:
    sm = SessionManager(cfg)
    res = Result()
    realized = 0.0; peak = 0.0
    pos = 0; entry = 0.0; stop = 0.0

    day_keys = sorted({sm._trading_day_key(b.start) for b in bars})
    prev_key = {day_keys[i]: day_keys[i - 1] for i in range(1, len(day_keys))}
    tdhl = trading_day_hl(bars, sm) if ref == "prevday" else {}

    # 每盤狀態
    cur_sig: Optional[Tuple[str, SessionType]] = None
    ref_hi = float("-inf"); ref_lo = float("inf")
    entries = 0
    # 每日斷路器
    cur_day = None; day_base = 0.0; locked = False; broke = False

    def close_at(price):
        nonlocal pos, realized, peak
        if pos == 0:
            return
        fill = price - slippage if pos > 0 else price + slippage
        pnl = (fill - entry) * pos * pv - cost
        realized += pnl
        res.trade_pnls.append(pnl); res.n_trades += 1
        if pnl > 0: res.n_wins += 1; res.gross_profit += pnl
        else: res.gross_loss += -pnl
        peak = max(peak, realized)
        res.max_drawdown = max(res.max_drawdown, peak - realized)
        pos = 0

    def open_at(price, d):
        nonlocal pos, entry, stop, realized
        entry = price + (slippage if d > 0 else -slippage)
        pos = d
        realized -= cost
        stop = entry - d * stop_points if stop_points > 0 else 0.0

    def cutoff_for(sess, b):
        return day_cutoff if sess == SessionType.DAY else night_cutoff

    pending = None  # ('enter',d)/('exit',)
    n = len(bars)
    for i in range(n):
        b = bars[i]
        sess = sm.current_session(b.start)
        tkey = sm._trading_day_key(b.start)

        # 換交易日 → 斷路器歸零
        if tkey != cur_day:
            cur_day = tkey; day_base = realized; locked = False; broke = False

        # 執行掛單（隔根開盤）
        if pending is not None:
            if sess != SessionType.NONE:
                px = b.open
                if pending[0] == "exit":
                    close_at(px)
                else:
                    if pos != 0: close_at(px)
                    open_at(px, pending[1]); entries += 1
            pending = None

        if sess == SessionType.NONE:
            if pos != 0: close_at(b.open);
            continue

        # 換盤 → 重置參考與出手數
        sig = (tkey, sess)
        if sig != cur_sig:
            cur_sig = sig; entries = 0
            if ref == "prevday":
                pk = prev_key.get(tkey)
                if pk and pk in tdhl:
                    ref_hi, ref_lo = tdhl[pk]
                else:
                    ref_hi, ref_lo = float("-inf"), float("inf")
            else:
                ref_hi, ref_lo = float("-inf"), float("inf")

        cutoff = cutoff_for(sess, b)
        # cutoff 前：openrange 累積參考高低
        before_cutoff = b.start.time() < cutoff if sess == SessionType.DAY else \
            (b.start.time() >= cfg.night_open and b.start.time() < cutoff)
        if ref == "openrange" and before_cutoff:
            ref_hi = max(ref_hi, b.high); ref_lo = min(ref_lo, b.low)

        # 盤中停損
        if pos != 0 and stop:
            if (pos > 0 and b.low <= stop) or (pos < 0 and b.high >= stop):
                close_at(stop)

        # 斷路器
        if not locked:
            unreal = (b.close - entry) * pos * pv if pos != 0 else 0.0
            if (realized - day_base) + unreal <= -cfg.daily_max_loss_twd:
                if pos != 0: close_at(b.close)
                locked = True
                if not broke: res.cb_days += 1; broke = True
                continue
        if locked:
            continue

        # 收盤前強平窗
        bar_end = b.start + timedelta(minutes=cfg.kbar_minutes)
        if sm.in_force_close_window(bar_end):
            if pos != 0: close_at(b.close)
            continue

        # 進場：cutoff 之後、參考已成形、未達出手上限
        can_enter = (not before_cutoff) and ref_hi > float("-inf") and \
            entries < cfg.max_entries_per_session
        if pos == 0 and can_enter:
            if b.close > ref_hi:
                pending = ("enter", 1)
            elif b.close < ref_lo:
                pending = ("enter", -1)
        # 對向突破出場
        elif pos > 0 and b.close < ref_lo:
            pending = ("exit",)
        elif pos < 0 and b.close > ref_hi:
            pending = ("exit",)

    if pos != 0:
        close_at(bars[-1].close)
    res.net_pnl = realized
    return res


def by_year(bars):
    g = defaultdict(list)
    for b in bars: g[b.start.year].append(b)
    return dict(sorted(g.items()))


def fmt(r: Result):
    return (f"淨利 {r.net_pnl:>10,.0f} | 交易 {r.n_trades:>4d} | 勝率 {r.win_rate*100:4.1f}% | "
            f"PF {min(r.profit_factor,99):4.2f} | MDD {r.max_drawdown:>9,.0f} | 恢復 {r.recovery:5.2f} | 斷路 {r.cb_days}天")


def main():
    ap = argparse.ArgumentParser(description="時間過濾型前高/前低突破（日內+−2890）回測")
    ap.add_argument("--csv", default=DEFAULT_CSV)
    ap.add_argument("--symbol", default="TMF", choices=list(CONTRACT_SPECS.keys()))
    ap.add_argument("--stop", type=float, default=40.0, help="單筆停損點數(0=不設,只靠強平/−2890)")
    ap.add_argument("--cost", type=float, default=15.0)
    ap.add_argument("--slippage", type=float, default=1.0)
    args = ap.parse_args()
    if not os.path.exists(args.csv):
        print(f"❌ 找不到檔案：{args.csv}（雲端無法存取本機路徑，請本機執行或 --csv 指定）"); return 2

    cfg = Config(); cfg.order_symbol = args.symbol; cfg.kbar_minutes = 5
    pv = CONTRACT_SPECS[args.symbol].point_value
    print(f"讀取 {args.csv} …")
    bars = resample(load_bars(args.csv), 5)
    print(f"5分K {len(bars):,} 根  契約 {args.symbol}({pv}元/點)  停損 {args.stop}點  成本 {args.cost}/邊 滑價 {args.slippage}")
    print(f"規則：早盤 10:00 後、夜盤 22:00 後突破進場；不留倉、收盤前 15 分強平、單日 −{cfg.daily_max_loss_twd:.0f} 鎖單；早夜各最多 {cfg.max_entries_per_session} 次。")

    for ref in ("openrange", "prevday"):
        label = "開盤區間(早08:45-10:00/夜15:00-22:00)" if ref == "openrange" else "前一交易日高低"
        overall = run(bars, cfg, pv, ref=ref, stop_points=args.stop,
                      slippage=args.slippage, cost=args.cost)
        py = {y: run(yb, cfg, pv, ref=ref, stop_points=args.stop,
                     slippage=args.slippage, cost=args.cost) for y, yb in by_year(bars).items()}
        pos = sum(1 for r in py.values() if r.net_pnl > 0)
        print(f"\n{'='*78}\n  參考＝{label}\n{'='*78}")
        print(f"  全期間 {fmt(overall)}")
        for y, r in py.items():
            print(f"    {y}  {fmt(r)}")
        print(f"  獲利年數：{pos}/{len(py)}")

    print("\n判讀：『斷路 N 天』>0 代表 −2890 真的會被觸發（單日確實守得住 2890）。"
          "重點仍是『扣成本後逐年是否為正』。")


if __name__ == "__main__":
    main()
