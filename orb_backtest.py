#!/usr/bin/env python3
r"""ORB 開盤區間突破 — 用『你自己的 txf_kbars.csv』找最佳參數並逐年回測。

這支工具就是用來回答「整體營利如何」的：它讀真實 K 線、套上你的所有規則
（早/夜盤各自開盤區間、每盤最多 4 次、單日 -2890 鎖單、收盤前強平），
然後輸出總績效 + 逐年績效 + 參數最佳化。

用法（在你本機 Windows 上跑）：
    # 1) 直接看預設參數的逐年表現
    python orb_backtest.py --csv "C:\Users\User\Desktop\codex\codexclaw\txf_kbars.csv" --symbol TMF

    # 2) 跑參數最佳化（grid search，依風報比排序，挑最穩健的）
    python orb_backtest.py --csv "C:\Users\User\Desktop\codex\codexclaw\txf_kbars.csv" --symbol TMF --optimize

CSV 欄位自動辨識（永豐 api.kbars 匯出常見格式）：
    時間：ts(奈秒) / Date / datetime / Datetime / time
    價量：Open High Low Close Volume（大小寫皆可）
時間預設視為『台北當地時間』。若你的 ts 是 UTC，加 --ts-utc。

❗本工具只用 K 線，不含 FVD/逐筆內外盤；ORB 策略本來就不需要它，
  所以這份回測對 ORB 是『完整、可信』的（這正是改用 ORB 的主因）。
"""
from __future__ import annotations

import argparse
import csv
import math
import os
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from tmf_trader.config import CONTRACT_SPECS, TZ, Config
from tmf_trader.kbar import Bar
from tmf_trader.session import SessionManager, SessionType
from tmf_trader.strategy_orb import Decision, ORBStrategy, Signal

DEFAULT_CSV = r"C:\Users\User\Desktop\codex\codexclaw\txf_kbars.csv"


# =========================================================================== #
#  讀取 K 線 CSV（容錯永豐 kbars 格式）
# =========================================================================== #
def _to_dt(val: str, ts_utc: bool) -> datetime:
    s = str(val).strip()
    # 數字時間戳（ts）
    if s.replace(".", "", 1).isdigit() and ("-" not in s) and ("/" not in s) and (":" not in s):
        x = float(s)
        if x > 1e17:      # 奈秒
            sec = x / 1e9
        elif x > 1e14:    # 微秒
            sec = x / 1e6
        elif x > 1e11:    # 毫秒
            sec = x / 1e3
        else:             # 秒
            sec = x
        naive = datetime(1970, 1, 1) + timedelta(seconds=sec)  # = utcfromtimestamp
        if ts_utc:
            return naive.replace(tzinfo=timezone.utc).astimezone(TZ)
        return TZ.localize(naive)  # 視為台北當地時間（永豐多數情況）
    # 字串時間
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M:%S",
                "%Y/%m/%d %H:%M", "%Y-%m-%dT%H:%M:%S"):
        try:
            return TZ.localize(datetime.strptime(s, fmt))
        except ValueError:
            continue
    dt = datetime.fromisoformat(s)
    return dt if dt.tzinfo else TZ.localize(dt)


def _pick(row: dict, *names) -> Optional[str]:
    for n in names:
        for k in row:
            if k and k.strip().lower() == n.lower():
                return row[k]
    return None


def load_bars(path: str, ts_utc: bool = False) -> List[Bar]:
    bars: List[Bar] = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tval = _pick(row, "ts", "datetime", "Datetime", "Date", "time", "Time")
            if tval is None:
                continue
            try:
                dt = _to_dt(tval, ts_utc)
                o = float(_pick(row, "Open", "open"))
                h = float(_pick(row, "High", "high"))
                l = float(_pick(row, "Low", "low"))
                c = float(_pick(row, "Close", "close"))
                v = int(float(_pick(row, "Volume", "volume") or 0))
            except (TypeError, ValueError):
                continue
            bars.append(Bar(dt, o, h, l, c, v))
    bars.sort(key=lambda b: b.start)
    return bars


def resample(bars: List[Bar], minutes: int) -> List[Bar]:
    """把原始 K 線（可能是 1 分）重新取樣成 N 分 K，依時鐘對齊。"""
    if not bars:
        return []
    out: List[Bar] = []
    cur: Optional[Bar] = None
    cur_key = None
    for b in bars:
        key = (b.start.date(), b.start.hour, (b.start.minute // minutes))
        if cur is None or key != cur_key:
            if cur is not None:
                out.append(cur)
            start = b.start.replace(minute=(b.start.minute // minutes) * minutes,
                                    second=0, microsecond=0)
            cur = Bar(start, b.open, b.high, b.low, b.close, b.volume)
            cur_key = key
        else:
            cur.high = max(cur.high, b.high)
            cur.low = min(cur.low, b.low)
            cur.close = b.close
            cur.volume += b.volume
    if cur is not None:
        out.append(cur)
    return out


# =========================================================================== #
#  績效結果
# =========================================================================== #
@dataclass
class Result:
    label: str = ""
    net_pnl: float = 0.0
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    n_trades: int = 0
    n_wins: int = 0
    max_drawdown: float = 0.0
    cb_days: int = 0
    costs: float = 0.0
    trade_pnls: List[float] = field(default_factory=list)

    @property
    def win_rate(self): return self.n_wins / self.n_trades if self.n_trades else 0.0
    @property
    def profit_factor(self): return self.gross_profit / self.gross_loss if self.gross_loss > 0 else float("inf")
    @property
    def recovery(self):
        if self.max_drawdown > 0:
            return self.net_pnl / self.max_drawdown
        return float("inf") if self.net_pnl > 0 else 0.0
    @property
    def expectancy(self): return self.net_pnl / self.n_trades if self.n_trades else 0.0
    @property
    def avg_win(self):
        w = [p for p in self.trade_pnls if p > 0]; return sum(w)/len(w) if w else 0.0
    @property
    def avg_loss(self):
        ll = [p for p in self.trade_pnls if p <= 0]; return sum(ll)/len(ll) if ll else 0.0
    @property
    def sharpe(self):
        n = len(self.trade_pnls)
        if n < 2: return 0.0
        m = sum(self.trade_pnls)/n
        sd = math.sqrt(sum((x-m)**2 for x in self.trade_pnls)/(n-1))
        return (m/sd*math.sqrt(n)) if sd > 0 else 0.0


# =========================================================================== #
#  ORB 回測器（bar-based，套用全部風控規則）
# =========================================================================== #
class ORBBacktester:
    def __init__(self, cfg: Config, slippage_pts: float = 1.0, cost_per_side_twd: float = 15.0):
        self.cfg = cfg
        self.slip = slippage_pts
        self.cost = cost_per_side_twd
        self.pv = cfg.order_spec.point_value

    def run(self, bars: List[Bar]) -> Result:
        cfg = self.cfg
        sm = SessionManager(cfg)
        strat = ORBStrategy(cfg, sm)
        res = Result(label=self._desc())

        # 部位狀態
        pos = 0
        entry = 0.0
        stop = 0.0
        target = 0.0
        best_excursion = 0.0  # 進場後最有利價（移動停損用）
        risk_pts = 0.0

        # 損益 / 風控
        realized = 0.0
        equity_peak = 0.0
        day_key = None
        day_start_realized = 0.0
        locked = False
        broke_today = False

        def close_pos(price: float, why: str):
            nonlocal pos, realized
            if pos == 0:
                return
            fill = price - self.slip if pos > 0 else price + self.slip
            pnl = (fill - entry) * pos * self.pv - self.cost  # 平倉這邊的成本
            realized += pnl
            res.trade_pnls.append(pnl)
            res.n_trades += 1
            if pnl > 0:
                res.n_wins += 1; res.gross_profit += pnl
            else:
                res.gross_loss += -pnl
            nonlocal equity_peak
            equity_peak = max(equity_peak, realized)
            res.max_drawdown = max(res.max_drawdown, equity_peak - realized)
            pos = 0

        def open_pos(direction: int, price: float, stop_price: float):
            nonlocal pos, entry, stop, target, best_excursion, risk_pts, realized
            fill = price + self.slip if direction > 0 else price - self.slip
            entry = fill
            pos = direction * cfg.order_quantity
            stop = stop_price
            risk_pts = abs(entry - stop_price)
            if cfg.orb_take_profit_R > 0 and risk_pts > 0:
                target = entry + direction * risk_pts * cfg.orb_take_profit_R
            else:
                target = 0.0
            best_excursion = entry
            realized -= self.cost  # 進場這邊的成本
            res.costs += self.cost * 2  # 來回成本（進+出）記錄用

        for bar in bars:
            now = bar.start
            sess = sm.current_session(now)

            # 換交易日 → 重置每日鎖單與基準
            dk = sm._trading_day_key(now)
            if dk != day_key:
                day_key = dk
                day_start_realized = realized
                locked = False
                broke_today = False

            if sess == SessionType.NONE:
                if pos != 0:
                    close_pos(bar.open, "session_end")
                continue

            # --- 先用這根 K 棒的高低檢查既有部位的停損/停利（盤中觸發）---
            if pos != 0:
                if pos > 0:
                    # 移動停損：達 1R 後把停損推到成本，再追蹤
                    if cfg.orb_use_trailing and bar.high >= entry + risk_pts:
                        best_excursion = max(best_excursion, bar.high)
                        stop = max(stop, entry, best_excursion - risk_pts)
                    hit_stop = bar.low <= stop
                    hit_tgt = target > 0 and bar.high >= target
                    if hit_stop:                      # 保守：同棒兩者都到，先停損
                        close_pos(stop, "stop")
                    elif hit_tgt:
                        close_pos(target, "target")
                else:
                    if cfg.orb_use_trailing and bar.low <= entry - risk_pts:
                        best_excursion = min(best_excursion, bar.low)
                        stop = min(stop, entry, best_excursion + risk_pts)
                    hit_stop = bar.high >= stop
                    hit_tgt = target > 0 and bar.low <= target
                    if hit_stop:
                        close_pos(stop, "stop")
                    elif hit_tgt:
                        close_pos(target, "target")

            # --- 每日斷路器：已實現+未實現 <= -2890 → 平倉並鎖單 ---
            if not locked:
                unreal = 0.0
                if pos != 0:
                    unreal = (bar.close - entry) * pos * self.pv
                day_pnl = (realized - day_start_realized) + unreal
                if day_pnl <= -cfg.daily_max_loss_twd:
                    if pos != 0:
                        close_pos(bar.close, "circuit_breaker")
                    locked = True
                    if not broke_today:
                        res.cb_days += 1; broke_today = True
                    continue

            if locked:
                continue

            # --- 收盤前強制平倉窗：平倉且不再進場 ---
            bar_end = now + timedelta(minutes=cfg.kbar_minutes)
            if sm.in_force_close_window(bar_end):
                if pos != 0:
                    close_pos(bar.close, "force_close")
                # 仍讓策略更新 OR/VWAP，但不會進場（下方 can_enter 會擋）
                strat.on_bar(bar, pos, now)
                continue

            # --- 餵策略，取得決策 ---
            dec = strat.on_bar(bar, pos, now)

            if dec.signal == Signal.EXIT and pos != 0:
                close_pos(bar.close, dec.reason)
            elif dec.signal in (Signal.ENTER_LONG, Signal.ENTER_SHORT) and pos == 0:
                if sm.can_enter(now):   # 早/夜盤各自最多 4 次
                    direction = 1 if dec.signal == Signal.ENTER_LONG else -1
                    open_pos(direction, bar.close, dec.stop_price)
                    sm.record_entry(now)

        # 收尾
        if pos != 0:
            close_pos(bars[-1].close, "eod")
        res.net_pnl = realized
        return res

    def _desc(self) -> str:
        c = self.cfg
        return (f"{c.order_symbol} ORB OR{c.or_minutes}m buf{c.orb_breakout_buffer_points:.0f} "
                f"vwap{int(c.orb_use_vwap_filter)} stop{c.per_trade_stop_points:.0f} "
                f"TP{c.orb_take_profit_R}R trail{int(c.orb_use_trailing)}")


# =========================================================================== #
#  逐年回測
# =========================================================================== #
def by_year(bars: List[Bar]) -> Dict[int, List[Bar]]:
    g: Dict[int, List[Bar]] = defaultdict(list)
    for b in bars:
        g[b.start.year].append(b)
    return dict(sorted(g.items()))


def run_yearly(cfg: Config, bars: List[Bar]) -> Tuple[Result, Dict[int, Result]]:
    overall = ORBBacktester(cfg).run(bars)
    per_year = {y: ORBBacktester(cfg).run(yb) for y, yb in by_year(bars).items()}
    return overall, per_year


# =========================================================================== #
#  最佳化
# =========================================================================== #
def make_cfg(symbol: str, or_min: int, buf: float, vwap: bool,
             stop: float, tp_r: float, trail: bool) -> Config:
    c = Config()
    c.strategy = "orb"
    c.order_symbol = symbol
    c.or_minutes = or_min
    c.orb_breakout_buffer_points = buf
    c.orb_use_vwap_filter = vwap
    c.per_trade_stop_points = stop
    c.orb_take_profit_R = tp_r
    c.orb_use_trailing = trail
    return c


def optimize(symbol: str, bars: List[Bar], min_trades: int = 30):
    grid = []
    for or_min in (15, 30, 45):
        for buf in (1, 3, 6):
            for vwap in (True, False):
                for stop in (20, 30, 45):
                    for tp_r in (1.5, 2.5):
                        for trail in (True, False):
                            grid.append((or_min, buf, vwap, stop, tp_r, trail))
    results = []
    for (or_min, buf, vwap, stop, tp_r, trail) in grid:
        cfg = make_cfg(symbol, or_min, buf, vwap, stop, tp_r, trail)
        try:
            cfg.validate()
        except Exception:
            continue
        r = ORBBacktester(cfg).run(bars)
        results.append((cfg, r))

    def score(item):
        _, r = item
        if r.n_trades < min_trades or r.net_pnl <= 0:
            return -1e9 + r.net_pnl
        return r.recovery * 2.0 + min(r.profit_factor, 5.0) + r.sharpe * 0.5

    results.sort(key=score, reverse=True)
    return results


# =========================================================================== #
#  報表
# =========================================================================== #
def fmt_result(r: Result) -> str:
    return (f"淨利 {r.net_pnl:>10,.0f} | 交易 {r.n_trades:>4d} | 勝率 {r.win_rate*100:4.1f}% | "
            f"PF {min(r.profit_factor,99):4.2f} | MDD {r.max_drawdown:>9,.0f} | "
            f"恢復 {r.recovery:5.2f} | 斷路 {r.cb_days}天")


def print_full(cfg: Config, overall: Result, per_year: Dict[int, Result], pv: int):
    print("\n" + "=" * 78)
    print(f" ORB 回測結果   契約={cfg.order_symbol}({pv}元/點)   參數={overall.label}")
    print("=" * 78)
    print(f" 【全期間】 {fmt_result(overall)}")
    print(f"   期望值/筆 {overall.expectancy:,.0f} (均盈 {overall.avg_win:,.0f}/均虧 {overall.avg_loss:,.0f})  Sharpe {overall.sharpe:.2f}")
    print(" 【逐年】")
    print(f"   {'年份':<6}{'淨利':>11}{'交易':>6}{'勝率':>7}{'PF':>6}{'最大回落':>11}{'恢復':>7}{'斷路日':>7}")
    print("   " + "-" * 64)
    for y, r in per_year.items():
        print(f"   {y:<6}{r.net_pnl:>11,.0f}{r.n_trades:>6}{r.win_rate*100:>6.1f}%"
              f"{min(r.profit_factor,99):>6.2f}{r.max_drawdown:>11,.0f}{r.recovery:>7.2f}{r.cb_days:>7}")
    # 誠實提示
    pos_years = sum(1 for r in per_year.values() if r.net_pnl > 0)
    print("   " + "-" * 64)
    print(f"   獲利年數: {pos_years}/{len(per_year)}")


# =========================================================================== #
def main():
    ap = argparse.ArgumentParser(description="ORB 開盤區間突破 — 真實 K 線回測與最佳化")
    ap.add_argument("--csv", default=DEFAULT_CSV, help="K 線 CSV 路徑")
    ap.add_argument("--symbol", default="TMF", choices=list(CONTRACT_SPECS.keys()))
    ap.add_argument("--resample", type=int, default=5, help="重新取樣成幾分 K (預設 5)")
    ap.add_argument("--ts-utc", action="store_true", help="CSV 時間戳為 UTC（預設視為台北時間）")
    ap.add_argument("--optimize", action="store_true", help="grid search 找最佳風報比參數")
    ap.add_argument("--cost", type=float, default=15.0, help="單邊成本 TWD（手續費+稅，預設 15）")
    ap.add_argument("--slippage", type=float, default=1.0, help="單邊滑價點數（預設 1）")
    args = ap.parse_args()

    if not os.path.exists(args.csv):
        print(f"❌ 找不到檔案：{args.csv}")
        print("   我（雲端沙盒）無法存取你本機 Windows 的路徑。請在你本機執行此腳本，")
        print("   或用 --csv 指定可存取的路徑，或把 CSV 上傳給我。")
        return 2

    print(f"讀取 {args.csv} …")
    raw = load_bars(args.csv, ts_utc=args.ts_utc)
    if not raw:
        print("❌ 沒讀到任何 K 棒，請檢查欄位名稱（需含 時間 + OHLC + Volume）。")
        return 2
    bars = resample(raw, args.resample)
    span = f"{bars[0].start:%Y-%m-%d} ~ {bars[-1].start:%Y-%m-%d}"
    print(f"原始 {len(raw):,} 根 → 重取樣 {args.resample}分K {len(bars):,} 根   期間 {span}")
    pv = CONTRACT_SPECS[args.symbol].point_value
    print(f"下單契約 {args.symbol} ({pv} 元/點)   成本 {args.cost}/邊   滑價 {args.slippage} 點/邊\n")

    if args.optimize:
        print("執行最佳化中（grid search，可能需數十秒）…")
        results = optimize(args.symbol, bars)
        print(f"\n{'排名':<4}{'OR':>4}{'buf':>5}{'VWAP':>6}{'停損':>6}{'TP':>6}{'trail':>7}"
              f"{'淨利':>11}{'PF':>6}{'MDD':>10}{'恢復':>7}{'勝率':>7}{'筆數':>6}{'斷路':>6}")
        print("-" * 96)
        for i, (cfg, r) in enumerate(results[:15], 1):
            print(f"{i:<4}{cfg.or_minutes:>4}{cfg.orb_breakout_buffer_points:>5.0f}"
                  f"{('Y' if cfg.orb_use_vwap_filter else 'N'):>6}{cfg.per_trade_stop_points:>6.0f}"
                  f"{cfg.orb_take_profit_R:>6.1f}{('Y' if cfg.orb_use_trailing else 'N'):>7}"
                  f"{r.net_pnl:>11,.0f}{min(r.profit_factor,99):>6.2f}{r.max_drawdown:>10,.0f}"
                  f"{r.recovery:>7.2f}{r.win_rate*100:>6.1f}%{r.n_trades:>6}{r.cb_days:>6}")
        best_cfg, _ = results[0]
        overall, per_year = run_yearly(best_cfg, bars)
        print_full(best_cfg, overall, per_year, pv)
        print("\n→ 建議寫入 tmf_trader/config.py：")
        print(f"     strategy='orb'  or_minutes={best_cfg.or_minutes}  "
              f"orb_breakout_buffer_points={best_cfg.orb_breakout_buffer_points:.0f}")
        print(f"     orb_use_vwap_filter={best_cfg.orb_use_vwap_filter}  "
              f"per_trade_stop_points={best_cfg.per_trade_stop_points:.0f}  "
              f"orb_take_profit_R={best_cfg.orb_take_profit_R}  "
              f"orb_use_trailing={best_cfg.orb_use_trailing}")
    else:
        cfg = make_cfg(args.symbol, 30, 3, True, 30, 1.8, True)
        overall, per_year = run_yearly(cfg, bars)
        print_full(cfg, overall, per_year, pv)
        print("\n（想自動找最佳參數，加 --optimize）")

    print("\n⚠️ 提醒：回測有前視/滑價/成本估計誤差，過去績效不代表未來。"
          "上線前請逐年都過關、先模擬單，再用最小口數實單。")


if __name__ == "__main__":
    main()
