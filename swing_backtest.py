#!/usr/bin/env python3
r"""波段/趨勢訊號回測 — 用真實 txf_kbars.csv 逐年驗證低頻策略是否有邊際。

這支工具回應「先回測訊號」的需求：把課程裡幾個**低頻波段**策略忠實實作成
Python，跑在你自己的 K 線上，**逐年**輸出績效，看哪一個真的有跨年穩定邊際。

實作的訊號（皆為持倉跨 K 棒的波段/趨勢型）：
  - ma      均線多空排列 (SMA 25/50/100)            #11
  - macd    MACD 柱狀體零軸翻多空                     #10
  - dmi     DMI +DI/-DI 交叉（可加 ADX 強度濾網）     #14
  - eff     高效波段：Kaufman 效率比 (ER)            #51
  - flip    多空對翻：ATR 突破 + 拉回%移動停損        #50

❗誠實前提：這些是**會留倉(隔夜)**的波段策略——這正是擺脫「日內高頻摩擦必敗」的方法。
  因此本回測**不套用單日 −2890 上限**（那是日內風控，與波段留倉天生衝突；正常單日
  振幅就常超過 2890）。這裡先回答更根本的問題：**訊號本身扣成本後有沒有逐年穩定邊際？**

用法：
  python swing_backtest.py --csv "txf_kbars.csv" --symbol TMF
  python swing_backtest.py --csv "txf_kbars.csv" --symbol TMF --strategy eff --tf 240 --detail
"""
from __future__ import annotations

import argparse
import math
import os
from collections import defaultdict
from typing import Callable, Dict, List, Optional, Tuple

from tmf_trader.config import CONTRACT_SPECS, Config
from tmf_trader.kbar import Bar
from tmf_trader.session import SessionManager
from orb_backtest import DEFAULT_CSV, Result, csv_not_found_msg, load_bars, resample

# --------------------------------------------------------------------------- #
#  指標（純 Python，避免額外相依）
# --------------------------------------------------------------------------- #
def sma(vals: List[float], n: int) -> List[Optional[float]]:
    out: List[Optional[float]] = [None] * len(vals)
    s = 0.0
    for i, v in enumerate(vals):
        s += v
        if i >= n:
            s -= vals[i - n]
        if i >= n - 1:
            out[i] = s / n
    return out


def ema(vals: List[float], n: int) -> List[Optional[float]]:
    out: List[Optional[float]] = [None] * len(vals)
    k = 2 / (n + 1)
    e = None
    for i, v in enumerate(vals):
        e = v if e is None else (v - e) * k + e
        out[i] = e
    return out


def macd_hist(close: List[float], fast=12, slow=26, sig=9) -> List[Optional[float]]:
    ef = ema(close, fast)
    es = ema(close, slow)
    macd = [(ef[i] - es[i]) if ef[i] is not None and es[i] is not None else None
            for i in range(len(close))]
    macd_clean = [m if m is not None else 0.0 for m in macd]
    sigl = ema(macd_clean, sig)
    return [macd[i] - sigl[i] if macd[i] is not None else None for i in range(len(close))]


def wilder(vals: List[float], n: int) -> List[Optional[float]]:
    out: List[Optional[float]] = [None] * len(vals)
    acc = 0.0
    for i, v in enumerate(vals):
        if i < n:
            acc += v
            if i == n - 1:
                out[i] = acc / n
        else:
            out[i] = (out[i - 1] * (n - 1) + v) / n
    return out


def dmi(bars: List[Bar], length=14, lensig=17):
    n = len(bars)
    tr = [0.0] * n
    pdm = [0.0] * n
    ndm = [0.0] * n
    for i in range(1, n):
        h, l, pc = bars[i].high, bars[i].low, bars[i - 1].close
        tr[i] = max(h - l, abs(h - pc), abs(l - pc))
        up = bars[i].high - bars[i - 1].high
        dn = bars[i - 1].low - bars[i].low
        pdm[i] = up if (up > dn and up > 0) else 0.0
        ndm[i] = dn if (dn > up and dn > 0) else 0.0
    atr = wilder(tr, length)
    spdm = wilder(pdm, length)
    sndm = wilder(ndm, length)
    pdi: List[Optional[float]] = [None] * n
    ndi: List[Optional[float]] = [None] * n
    dx: List[float] = [0.0] * n
    for i in range(n):
        if atr[i] and atr[i] > 0 and spdm[i] is not None:
            pdi[i] = 100 * spdm[i] / atr[i]
            ndi[i] = 100 * sndm[i] / atr[i]
            s = pdi[i] + ndi[i]
            dx[i] = 100 * abs(pdi[i] - ndi[i]) / s if s > 0 else 0.0
    adx = wilder(dx, lensig)
    return pdi, ndi, adx


def atr_series(bars: List[Bar], n=20) -> List[Optional[float]]:
    tr = [0.0] * len(bars)
    for i in range(1, len(bars)):
        h, l, pc = bars[i].high, bars[i].low, bars[i - 1].close
        tr[i] = max(h - l, abs(h - pc), abs(l - pc))
    return wilder(tr, n)


def efficiency_ratio(close: List[float], n=20) -> List[Optional[float]]:
    out: List[Optional[float]] = [None] * len(close)
    for i in range(n, len(close)):
        straight = close[i] - close[i - n]
        total = sum(abs(close[j] - close[j - 1]) for j in range(i - n + 1, i + 1))
        out[i] = (straight / total) if total > 0 else 0.0
    return out


# --------------------------------------------------------------------------- #
#  訊號 → 目標部位序列 (+1 多 / -1 空 / 0 空手)
# --------------------------------------------------------------------------- #
def sig_ma(bars, p=(25, 50, 100)) -> List[int]:
    close = [b.close for b in bars]
    s, m, l = sma(close, p[0]), sma(close, p[1]), sma(close, p[2])
    pos = [0] * len(bars)
    cur = 0
    for i in range(len(bars)):
        if s[i] is None or m[i] is None or l[i] is None:
            pos[i] = 0
            continue
        if s[i] > m[i] > l[i]:
            cur = 1
        elif s[i] < m[i] < l[i]:
            cur = -1
        pos[i] = cur
    return pos


def sig_macd(bars) -> List[int]:
    hist = macd_hist([b.close for b in bars])
    pos = [0] * len(bars)
    cur = 0
    for i in range(len(bars)):
        if hist[i] is None:
            continue
        if hist[i] > 0:
            cur = 1
        elif hist[i] < 0:
            cur = -1
        pos[i] = cur
    return pos


def sig_dmi(bars, length=14, lensig=17, adx_gap=0) -> List[int]:
    pdi, ndi, adx = dmi(bars, length, lensig)
    pos = [0] * len(bars)
    cur = 0
    for i in range(len(bars)):
        if pdi[i] is None:
            continue
        strong = (adx[i] is not None and adx[i] >= adx_gap) if adx_gap > 0 else True
        if strong:
            if pdi[i] > ndi[i]:
                cur = 1
            elif pdi[i] < ndi[i]:
                cur = -1
        pos[i] = cur
    return pos


def sig_eff(bars, n=20, eff=0.5) -> List[int]:
    er = efficiency_ratio([b.close for b in bars], n)
    pos = [0] * len(bars)
    cur = 0
    prev = None
    for i in range(len(bars)):
        e = er[i]
        if e is None:
            prev = e
            continue
        if cur == 0:
            if prev is not None and prev <= eff < e:
                cur = 1
            elif prev is not None and prev >= -eff > e:
                cur = -1
        elif cur > 0 and e < 0:
            cur = 0
        elif cur < 0 and e > 0:
            cur = 0
        pos[i] = cur
        prev = e
    return pos


def sig_flip(bars, n=20, gap=1.0, mult=2.0) -> List[int]:
    atr = atr_series(bars, n)
    pos = [0] * len(bars)
    cur = 0
    for i in range(1, len(bars)):
        if atr[i] is None:
            continue
        c, c1, o1 = bars[i].close, bars[i - 1].close, bars[i - 1].open
        a = atr[i] * mult
        up_body = (c1 - o1) / o1 if o1 else 0
        dn_body = (o1 - c1) / o1 if o1 else 0
        if cur <= 0 and c > c1 + a and up_body > gap * 0.01:
            cur = 1
        elif cur >= 0 and c < c1 - a and dn_body > gap * 0.01:
            cur = -1
        pos[i] = cur
    return pos


STRATS: Dict[str, Tuple[str, Callable]] = {
    "ma":   ("均線多空排列(25/50/100)", sig_ma),
    "macd": ("MACD柱狀零軸翻", sig_macd),
    "dmi":  ("DMI +DI/-DI交叉", sig_dmi),
    "eff":  ("高效波段(效率比)", sig_eff),
    "flip": ("多空對翻(ATR突破)", sig_flip),
}


# --------------------------------------------------------------------------- #
#  回測：目標部位模型（換方向才換倉，留倉跨 K）
# --------------------------------------------------------------------------- #
def backtest(bars: List[Bar], target: List[int], pv: int,
             slippage=1.0, cost=15.0) -> Result:
    res = Result()
    realized = 0.0
    peak = 0.0
    pos = 0
    entry = 0.0

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

    for i in range(len(bars)):
        t = target[i]
        if t != pos:
            # 保守、無前視：訊號於本根收盤產生，於『下一根開盤』成交。
            px = bars[i + 1].open if i + 1 < len(bars) else bars[i].close
            close_at(px, i)
            if t != 0:
                entry = px + (slippage if t > 0 else -slippage)
                realized -= cost
            pos = t
    if pos != 0:
        close_at(bars[-1].close, len(bars) - 1)
    res.net_pnl = realized
    return res


def by_year(bars: List[Bar]):
    g = defaultdict(list)
    for b in bars:
        g[b.start.year].append(b)
    return dict(sorted(g.items()))


def run_strategy(name: str, bars: List[Bar], pv: int, slippage, cost,
                 **kw) -> Tuple[Result, Dict[int, Result]]:
    fn = STRATS[name][1]
    overall = backtest(bars, fn(bars, **kw), pv, slippage, cost)
    per_year = {}
    for y, yb in by_year(bars).items():
        per_year[y] = backtest(yb, fn(yb, **kw), pv, slippage, cost)
    return overall, per_year


# --------------------------------------------------------------------------- #
def daily_resample(bars: List[Bar], cfg: Config) -> List[Bar]:
    """以『交易日』(早盤+夜盤歸屬) 聚合成日 K。"""
    sm = SessionManager(cfg)
    groups: Dict[str, List[Bar]] = defaultdict(list)
    for b in bars:
        groups[sm._trading_day_key(b.start)].append(b)
    out = []
    for k in sorted(groups):
        g = groups[k]
        out.append(Bar(g[0].start, g[0].open, max(x.high for x in g),
                       min(x.low for x in g), g[-1].close, sum(x.volume for x in g)))
    return out


def fmt(r: Result) -> str:
    return (f"淨利 {r.net_pnl:>10,.0f} | 交易 {r.n_trades:>4d} | 勝率 {r.win_rate*100:4.1f}% | "
            f"PF {min(r.profit_factor,99):4.2f} | MDD {r.max_drawdown:>9,.0f} | 恢復 {r.recovery:5.2f}")


def main():
    ap = argparse.ArgumentParser(description="波段訊號逐年回測")
    ap.add_argument("--csv", default=DEFAULT_CSV)
    ap.add_argument("--symbol", default="TMF", choices=list(CONTRACT_SPECS.keys()))
    ap.add_argument("--strategy", default="all", choices=["all"] + list(STRATS))
    ap.add_argument("--tf", default="all", help="時間框架(分鐘) 或 daily 或 all")
    ap.add_argument("--detail", action="store_true", help="印出最佳組合的逐年明細")
    ap.add_argument("--cost", type=float, default=15.0)
    ap.add_argument("--slippage", type=float, default=1.0)
    args = ap.parse_args()

    if not os.path.exists(args.csv):
        print(csv_not_found_msg(args.csv))
        return 2

    cfg = Config(); cfg.order_symbol = args.symbol
    pv = CONTRACT_SPECS[args.symbol].point_value
    print(f"讀取 {args.csv} …")
    raw = load_bars(args.csv)
    print(f"原始 {len(raw):,} 根   契約 {args.symbol}({pv}元/點)  成本 {args.cost}/邊 滑價 {args.slippage}點/邊")

    tfs = ["30", "60", "120", "240", "daily"] if args.tf == "all" else [args.tf]
    strat_names = list(STRATS) if args.strategy == "all" else [args.strategy]

    # 預先準備各時間框架的 bars
    tf_bars = {}
    for tf in tfs:
        tf_bars[tf] = daily_resample(raw, cfg) if tf == "daily" else resample(raw, int(tf))

    print(f"\n{'策略':<24}{'TF':>6}{'淨利':>11}{'PF':>6}{'MDD':>10}{'恢復':>7}{'交易':>6}{'獲利年':>8}")
    print("-" * 80)
    best = None
    for sn in strat_names:
        for tf in tfs:
            bars = tf_bars[tf]
            if len(bars) < 120:
                continue
            overall, per_year = run_strategy(sn, bars, pv, args.slippage, args.cost)
            pos_years = sum(1 for r in per_year.values() if r.net_pnl > 0)
            tot_years = len(per_year)
            print(f"{STRATS[sn][0]:<22}{tf:>6}{overall.net_pnl:>11,.0f}"
                  f"{min(overall.profit_factor,99):>6.2f}{overall.max_drawdown:>10,.0f}"
                  f"{overall.recovery:>7.2f}{overall.n_trades:>6}{pos_years:>5}/{tot_years}")
            score = (pos_years / tot_years, overall.recovery)
            if overall.net_pnl > 0 and (best is None or score > best[0]):
                best = (score, sn, tf, overall, per_year)

    if best is None:
        print("\n結論：在所有測試組合中，**沒有任何一個達到全期間正報酬**。")
        print("（與日內 ORB 一致：這些訊號在 TXF 扣成本後沒有可靠邊際。）")
        return 0

    _, sn, tf, overall, per_year = best
    print("\n" + "=" * 72)
    print(f"🏆 最佳組合：{STRATS[sn][0]}  TF={tf}")
    print(f"   全期間 {fmt(overall)}")
    print(f"   期望值/筆 {overall.expectancy:,.0f}  Sharpe {overall.sharpe:.2f}")
    if args.detail or True:
        print("   逐年：")
        for y, r in per_year.items():
            print(f"     {y}  {fmt(r)}")
        pos = sum(1 for r in per_year.values() if r.net_pnl > 0)
        print(f"   獲利年數：{pos}/{len(per_year)}")
    print("\n⚠️ 留倉策略，未套用單日 −2890 上限（與波段天生衝突）。"
          "若要上線仍需加：移動停損、單筆風險上限、口數控制；並先模擬。")


if __name__ == "__main__":
    main()
