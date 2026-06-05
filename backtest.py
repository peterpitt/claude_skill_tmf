"""回測引擎 — 直接重放『實盤同一套程式碼』。

重點：本回測不是重寫一份策略，而是把 tick 餵進與實盤完全相同的
  KBarAggregator / FVDTracker / Strategy / PositionBook / SessionManager
以及同一條風控斷路器規則，確保回測行為 == 實盤行為。

資料來源兩種：
  (A) --csv 你自己的真實 5 分 K（建議：由 Shioaji api.kbars 匯出）。
      欄位：datetime,Open,High,Low,Close,Volume
      因 CSV 無逐筆內外盤，FVD 以「bar 收盤在區間位置 × 量」做 proxy（已標註）。
  (B) 內建合成市場（Monte-Carlo，可重現）：用來驗證引擎與比較參數排名，
      ❗不是歷史資料、不代表真實獲利，僅供風報比『相對』最佳化。

成交假設：市價/範圍市價 → 當下 tick 價 ± 滑價；含每邊手續費+稅成本。
"""
from __future__ import annotations

import argparse
import csv
import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Iterable, List, Optional, Tuple

import pytz

from tmf_trader.config import TZ, CONTRACT_SPECS, Config
from tmf_trader.kbar import KBarAggregator
from tmf_trader.market_data import FVDTracker
from tmf_trader.position_book import PositionBook
from tmf_trader.session import SessionManager, SessionType
from tmf_trader.strategy import Signal, Strategy

Tick = Tuple[datetime, float, int, int]  # (時間, 價格, 量, tick_type 1外/2內/0未定)


# =========================================================================== #
#  合成市場（Monte-Carlo）
# =========================================================================== #
class SyntheticMarket:
    """產生可重現的逐筆 tick，含日內趨勢/盤整切換與內外盤動能。

    刻意設計成『跨日漂移為零均值』——不偷塞多頭紅利，
    策略的邊際必須來自日內動能延續，盤整日就該被巴。
    """

    def __init__(self, days: int = 40, base_price: float = 21000.0,
                 ticks_per_bar: int = 60, seed: int = 20260605):
        self.days = days
        self.base = base_price
        self.tpb = ticks_per_bar
        self.rng = random.Random(seed)

    def _session_bars(self, day0: datetime) -> List[Tuple[datetime, datetime]]:
        """回傳當日早盤+夜盤的每根 5 分 K 起始時間。"""
        bars = []
        # 早盤 08:45 - 13:45
        t = day0.replace(hour=8, minute=45, second=0, microsecond=0)
        end = day0.replace(hour=13, minute=45)
        while t < end:
            bars.append(t); t += timedelta(minutes=5)
        # 夜盤 15:00 - 隔日 05:00
        t = day0.replace(hour=15, minute=0)
        end = day0.replace(hour=15, minute=0) + timedelta(hours=14)
        while t < end:
            bars.append(t); t += timedelta(minutes=5)
        return bars

    def generate(self) -> List[Tick]:
        ticks: List[Tick] = []
        price = self.base
        day0 = TZ.localize(datetime(2026, 1, 5, 0, 0))  # 起始（週一）
        regime_left = 0
        drift = 0.0
        vol = 12.0
        for d in range(self.days):
            day = day0 + timedelta(days=d)
            if day.weekday() >= 5:  # 跳過週末
                continue
            for bstart in self._session_bars(day):
                # регime 切換：趨勢 vs 盤整，持續數根。
                if regime_left <= 0:
                    regime_left = self.rng.randint(4, 16)
                    r = self.rng.random()
                    if r < 0.40:      # 趨勢
                        drift = self.rng.choice([-1, 1]) * self.rng.uniform(1.5, 4.0)
                        vol = self.rng.uniform(8, 14)
                    else:             # 盤整
                        drift = 0.0
                        vol = self.rng.uniform(10, 18)
                regime_left -= 1

                bar_ret = self.rng.gauss(drift, vol)
                open_p = price
                close_p = max(1.0, open_p + bar_ret)
                d_sign = 1 if close_p >= open_p else -1
                # 外盤機率隨 bar 方向偏移（內外盤動能與價格同向但有雜訊）。
                p_out = 0.5 + d_sign * min(0.30, abs(bar_ret) / (vol * 4 + 1e-9))

                for i in range(self.tpb):
                    frac = (i + 1) / self.tpb
                    # 價格從 open 線性走向 close + 雜訊。
                    p = open_p + (close_p - open_p) * frac + self.rng.gauss(0, vol * 0.25)
                    p = round(max(1.0, p))
                    ts = bstart + timedelta(seconds=int(300 * frac))
                    vol_tick = self.rng.randint(1, 6)
                    ttype = 1 if self.rng.random() < p_out else 2
                    ticks.append((ts, float(p), vol_tick, ttype))
                price = close_p
        return ticks


# =========================================================================== #
#  CSV 載入（真實資料）→ 由 K 棒近似出 tick
# =========================================================================== #
def load_csv_as_ticks(path: str, ticks_per_bar: int = 8) -> List[Tick]:
    """讀 5 分 K CSV，合成近似 tick。

    FVD proxy：用收盤在 [low, high] 的位置決定外盤比例
      （收在高檔→偏外盤、收在低檔→偏內盤），量平均分配。
    """
    ticks: List[Tick] = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dt = _parse_dt(row.get("datetime") or row.get("Datetime") or row.get("ts"))
            o = float(row.get("Open") or row.get("open"))
            h = float(row.get("High") or row.get("high"))
            l = float(row.get("Low") or row.get("low"))
            c = float(row.get("Close") or row.get("close"))
            v = int(float(row.get("Volume") or row.get("volume") or 0))
            rng = max(1e-9, h - l)
            close_pos = (c - l) / rng           # 0=收最低, 1=收最高
            p_out = 0.5 + (close_pos - 0.5)      # 0~1
            per = max(1, v // ticks_per_bar)
            path_pts = [o, (o + h) / 2, h, (h + l) / 2, l, (l + c) / 2, c, c][:ticks_per_bar]
            for i, p in enumerate(path_pts):
                ts = dt + timedelta(seconds=int(300 * (i + 1) / ticks_per_bar))
                ttype = 1 if random.random() < p_out else 2
                ticks.append((ts, float(round(p)), per, ttype))
    ticks.sort(key=lambda x: x[0])
    return ticks


def _parse_dt(s: str) -> datetime:
    s = s.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M"):
        try:
            return TZ.localize(datetime.strptime(s, fmt))
        except ValueError:
            continue
    # ISO fallback
    dt = datetime.fromisoformat(s)
    return dt if dt.tzinfo else TZ.localize(dt)


# =========================================================================== #
#  回測器
# =========================================================================== #
@dataclass
class BTResult:
    cfg_desc: str
    net_pnl: float = 0.0
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    n_trades: int = 0
    n_wins: int = 0
    max_drawdown: float = 0.0
    cb_days: int = 0           # 斷路器觸發天數
    costs: float = 0.0
    trade_pnls: List[float] = field(default_factory=list)

    @property
    def win_rate(self) -> float:
        return self.n_wins / self.n_trades if self.n_trades else 0.0

    @property
    def profit_factor(self) -> float:
        return self.gross_profit / self.gross_loss if self.gross_loss > 0 else float("inf")

    @property
    def recovery_factor(self) -> float:
        """淨利 / 最大回落 — 乾淨的風報比指標。"""
        return self.net_pnl / self.max_drawdown if self.max_drawdown > 0 else (
            float("inf") if self.net_pnl > 0 else 0.0)

    @property
    def expectancy(self) -> float:
        return self.net_pnl / self.n_trades if self.n_trades else 0.0

    @property
    def avg_win(self) -> float:
        w = [p for p in self.trade_pnls if p > 0]
        return sum(w) / len(w) if w else 0.0

    @property
    def avg_loss(self) -> float:
        ll = [p for p in self.trade_pnls if p <= 0]
        return sum(ll) / len(ll) if ll else 0.0

    @property
    def sharpe_like(self) -> float:
        """每筆損益的 Sharpe 近似（無風險利率設 0）。"""
        n = len(self.trade_pnls)
        if n < 2:
            return 0.0
        mean = sum(self.trade_pnls) / n
        var = sum((x - mean) ** 2 for x in self.trade_pnls) / (n - 1)
        sd = math.sqrt(var)
        return (mean / sd * math.sqrt(n)) if sd > 0 else 0.0


class Backtester:
    def __init__(self, cfg: Config, slippage_pts: float = 1.0, cost_per_side_twd: float = 15.0):
        self.cfg = cfg
        self.slippage = slippage_pts
        self.cost = cost_per_side_twd
        self.pv = cfg.order_spec.point_value

    def run(self, ticks: Iterable[Tick]) -> BTResult:
        cfg = self.cfg
        agg = KBarAggregator(cfg.kbar_minutes, cfg.ma_period)
        fvd = FVDTracker(cfg.fvd_window_seconds)
        book = PositionBook(self.pv)
        sm = SessionManager(cfg)
        strat = Strategy(cfg, agg, fvd, _NullLog())

        res = BTResult(cfg_desc=self._desc())
        equity_peak = 0.0
        last_flat_realized = 0.0

        # 每日斷路器狀態
        cur_day_key: Optional[str] = None
        day_start_realized = 0.0
        locked = False  # 當日是否已斷路

        def trading_day(dt) -> str:
            return sm._trading_day_key(dt)

        def fill(action: str, qty: int, price: float):
            slip = self.slippage if action == "Buy" else -self.slippage
            book.on_fill(action, price + slip, qty)
            book.realized_pnl_twd -= self.cost * qty
            res.costs += self.cost * qty

        def record_trade_if_flat():
            nonlocal last_flat_realized, equity_peak
            if book.position == 0:
                tp = book.realized_pnl_twd - last_flat_realized
                last_flat_realized = book.realized_pnl_twd
                res.trade_pnls.append(tp)
                res.n_trades += 1
                if tp > 0:
                    res.n_wins += 1
                    res.gross_profit += tp
                else:
                    res.gross_loss += -tp
                # drawdown on realized equity
                eq = book.realized_pnl_twd
                equity_peak = max(equity_peak, eq)
                res.max_drawdown = max(res.max_drawdown, equity_peak - eq)

        def flatten(price: float):
            if book.position == 0:
                return
            action = "Sell" if book.position > 0 else "Buy"
            fill(action, abs(book.position), price)
            record_trade_if_flat()

        for ts, price, vtick, ttype in ticks:
            # 換交易日 → 重置斷路器/當日基準
            dk = trading_day(ts)
            if dk != cur_day_key:
                cur_day_key = dk
                day_start_realized = book.realized_pnl_twd
                locked = False

            fvd.add_tick(ts, vtick, ttype)
            book.update_last_price(price)

            # --- 當日斷路器（同步重放實盤規則）---
            if not locked:
                day_pnl = (book.realized_pnl_twd - day_start_realized) + book.unrealized_pnl_twd(price)
                if day_pnl <= -cfg.daily_max_loss_twd:
                    flatten(price)
                    locked = True
                    res.cb_days += 1
                    continue

            # --- 單筆停損 ---
            if book.position != 0:
                if book.unrealized_pnl_twd(price) <= -cfg.per_trade_stop_twd():
                    flatten(price)

            # --- 收盤前強制平倉窗 ---
            if sm.in_force_close_window(ts):
                if book.position != 0:
                    flatten(price)

            # --- K 棒收盤 → 訊號 ---
            closed = agg.add_tick(ts, price, vtick)
            if closed is not None:
                if locked:
                    continue
                sig = strat.on_bar_close(closed, book.position, ts)
                if sig == Signal.EXIT and book.position != 0:
                    flatten(price)
                elif sig in (Signal.ENTER_LONG, Signal.ENTER_SHORT):
                    if book.position == 0 and sm.can_enter(ts):
                        action = "Buy" if sig == Signal.ENTER_LONG else "Sell"
                        fill(action, cfg.order_quantity, price)
                        sm.record_entry(ts)

        # 收尾平倉
        if book.position != 0:
            last_price = book.last_price
            flatten(last_price)

        res.net_pnl = book.realized_pnl_twd
        return res

    def _desc(self) -> str:
        c = self.cfg
        return (f"{c.order_symbol} K{c.kbar_minutes} MA{c.ma_period} "
                f"FVD±{c.fvd_entry_threshold}/{c.fvd_window_seconds}s "
                f"stop{c.per_trade_stop_points}pt")


class _NullLog:
    """回測時噤聲（策略內部 log 會太吵）。"""
    def debug(self, *a, **k): pass
    def info(self, *a, **k): pass
    def warning(self, *a, **k): pass
    def error(self, *a, **k): pass
    def critical(self, *a, **k): pass


# =========================================================================== #
#  最佳化（grid search，依風報比排序）
# =========================================================================== #
def make_cfg(order_symbol: str, ma: int, fvd_thr: int, stop_pts: float,
             fvd_win: int = 60) -> Config:
    c = Config()
    c.order_symbol = order_symbol
    c.ma_period = ma
    c.fvd_entry_threshold = fvd_thr
    c.per_trade_stop_points = stop_pts
    c.fvd_window_seconds = fvd_win
    return c


def optimize(ticks: List[Tick], order_symbol: str,
             min_trades: int = 20) -> Tuple[List[Tuple[Config, BTResult]], Tuple[Config, BTResult]]:
    grid_ma = [13, 21, 34]
    grid_fvd = [10, 20, 30, 45]
    grid_stop = [12, 20, 30]
    results: List[Tuple[Config, BTResult]] = []
    for ma in grid_ma:
        for fv in grid_fvd:
            for st in grid_stop:
                cfg = make_cfg(order_symbol, ma, fv, st)
                try:
                    cfg.validate()
                except Exception:
                    continue
                r = Backtester(cfg).run(ticks)
                results.append((cfg, r))

    def score(item):
        _, r = item
        if r.n_trades < min_trades or r.net_pnl <= 0:
            return -1e9 + r.net_pnl  # 不合格者排後面但仍有序
        # 風報比綜合分：恢復係數為主，profit factor 與 sharpe 加權。
        pf = min(r.profit_factor, 5.0)
        return r.recovery_factor * 2.0 + pf + r.sharpe_like * 0.5

    results.sort(key=score, reverse=True)
    best = results[0]
    return results, best


def robustness(top_cfgs: List[Config], seeds: List[int], days: int,
               symbol: str) -> List[Tuple[Config, dict]]:
    """把候選參數丟到多個隨機種子的合成市場，挑『跨種子穩定』而非單一最幸運者。

    回傳每個 cfg 的跨種子統計（中位淨利、最差淨利、正報酬種子比例、平均恢復係數）。
    """
    out = []
    for cfg in top_cfgs:
        nets, recs, cb = [], [], 0
        for s in seeds:
            ticks = SyntheticMarket(days=days, seed=s).generate()
            r = Backtester(cfg).run(ticks)
            nets.append(r.net_pnl)
            recs.append(r.recovery_factor if r.recovery_factor != float("inf") else 0)
            cb += r.cb_days
        nets_sorted = sorted(nets)
        median = nets_sorted[len(nets_sorted) // 2]
        out.append((cfg, {
            "median_net": median,
            "worst_net": min(nets),
            "best_net": max(nets),
            "pos_ratio": sum(1 for n in nets if n > 0) / len(nets),
            "avg_recovery": sum(recs) / len(recs),
            "total_cb_days": cb,
        }))
    # 以「中位淨利為主、最差淨利為輔」排序，獎勵穩健。
    out.sort(key=lambda x: (x[1]["median_net"] + x[1]["worst_net"]), reverse=True)
    return out


# =========================================================================== #
#  報表
# =========================================================================== #
def print_result(r: BTResult, header: str = "") -> None:
    if header:
        print(f"\n=== {header} ===")
    print(f"  設定          : {r.cfg_desc}")
    print(f"  淨損益        : {r.net_pnl:>12,.0f} TWD   (含成本 -{r.costs:,.0f})")
    print(f"  交易次數      : {r.n_trades:>5d}   勝率 {r.win_rate*100:5.1f}%")
    print(f"  獲利因子 PF   : {r.profit_factor:>8.2f}")
    print(f"  最大回落 MDD  : {r.max_drawdown:>12,.0f} TWD")
    print(f"  恢復係數      : {r.recovery_factor:>8.2f}   (淨利/MDD, 越高越好)")
    print(f"  期望值/筆     : {r.expectancy:>10,.0f} TWD   (均盈 {r.avg_win:,.0f} / 均虧 {r.avg_loss:,.0f})")
    print(f"  Sharpe(近似)  : {r.sharpe_like:>8.2f}")
    print(f"  斷路器觸發    : {r.cb_days} 天")


def print_table(results: List[Tuple[Config, BTResult]], top: int = 10) -> None:
    print(f"\n{'排名':<4}{'MA':>4}{'FVD':>5}{'停損':>6}{'淨損益':>12}{'PF':>7}"
          f"{'MDD':>10}{'恢復':>7}{'勝率':>7}{'筆數':>6}{'斷路':>6}")
    print("-" * 80)
    for i, (cfg, r) in enumerate(results[:top], 1):
        print(f"{i:<4}{cfg.ma_period:>4}{cfg.fvd_entry_threshold:>5}"
              f"{cfg.per_trade_stop_points:>6.0f}{r.net_pnl:>12,.0f}"
              f"{min(r.profit_factor,99):>7.2f}{r.max_drawdown:>10,.0f}"
              f"{r.recovery_factor:>7.2f}{r.win_rate*100:>6.1f}%{r.n_trades:>6}{r.cb_days:>6}")


# =========================================================================== #
def main():
    ap = argparse.ArgumentParser(description="TMF/MXF 回測與參數最佳化")
    ap.add_argument("--csv", help="真實 5 分 K CSV 路徑（無則用合成市場）")
    ap.add_argument("--symbol", default="TMF", choices=list(CONTRACT_SPECS.keys()))
    ap.add_argument("--days", type=int, default=40, help="合成市場天數")
    ap.add_argument("--seed", type=int, default=20260605)
    ap.add_argument("--optimize", action="store_true", help="執行 grid search 最佳化")
    args = ap.parse_args()

    if args.csv:
        print(f"載入真實資料: {args.csv}")
        ticks = load_csv_as_ticks(args.csv)
        src = f"CSV({args.csv})"
    else:
        print(f"⚠️  使用『合成市場』(seed={args.seed}, {args.days} 交易日) — 非歷史資料，僅供引擎驗證與參數相對排名。")
        ticks = SyntheticMarket(days=args.days, seed=args.seed).generate()
        src = f"SYNTHETIC(seed={args.seed},{args.days}d)"
    print(f"資料筆數(ticks): {len(ticks):,}  下單契約: {args.symbol} ({CONTRACT_SPECS[args.symbol].point_value}元/點)\n")

    # 基準（目前預設參數）
    base_cfg = make_cfg(args.symbol, 21, 30, 20)
    base = Backtester(base_cfg).run(ticks)
    print_result(base, f"基準（出廠預設）  資料={src}")

    if args.optimize:
        print("\n執行最佳化中（grid search）…")
        results, (best_cfg, best) = optimize(ticks, args.symbol)
        print_table(results, top=12)
        print_result(best, "🏆 最佳風報比參數")
        print("\n→ 建議 config.py 設定：")
        print(f"     ma_period            = {best_cfg.ma_period}")
        print(f"     fvd_entry_threshold  = {best_cfg.fvd_entry_threshold}")
        print(f"     per_trade_stop_points= {best_cfg.per_trade_stop_points:.0f}")


if __name__ == "__main__":
    main()
