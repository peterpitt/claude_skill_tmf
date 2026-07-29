#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""update_kbars.py — 用 Shioaji API 抓最新 TXF K 線，增量合併進你的回測 CSV。

目的：讓 D1 的回測資料「持續更新」。你平常只要跑一次：

    python update_kbars.py

它會自動：
  1. 讀你現有的 CSV（用與回測腳本相同的自動偵測邏輯，見 orb_backtest.resolve_default_csv）
  2. 找出裡面最後一根 K 的日期，只向 Shioaji 要「那天之後」的新資料（增量、省流量）
  3. 抓 1 分 K → 重新取樣成與你檔案相同的週期（預設 5 分）
  4. 與舊資料合併、依時間去重排序（重疊區間以新抓的為準，等於順手修正）
  5. 先把舊檔備份成 <檔名>.bak，再寫回同一個檔

因為所有回測腳本都讀同一個檔，更新完直接重跑回測就是最新結果。

【只需要 API 金鑰，不需要 CA 憑證】
查歷史/近期 K 線屬於「市場資料查詢」，只要 SHIOAJI_API_KEY + SHIOAJI_SECRET_KEY 登入即可，
不必 CA 憑證（憑證只有「下真單」才要）。本腳本從頭到尾不下任何單。

【Shioaji 歷史 K 線的先天限制】
免費 kbars 只能取「近期」（約數月～一年，且有流量上限）。所以本工具的定位是
「每天/每週增量補新」，不是一次拉五年。你手上那份 5 年歷史請留著當基底，之後靠這支往後接。

用法範例：
    python update_kbars.py                          # 增量更新自動偵測到的 CSV
    python update_kbars.py --csv D:\data\txf.csv     # 指定檔案
    python update_kbars.py --start 2026-06-01        # 強制從某日開始抓
    python update_kbars.py --minutes 5 --contract TXFR1
    python update_kbars.py --dry-run                 # 只抓、只印摘要，不寫檔
"""
from __future__ import annotations

import argparse
import csv
import os
import shutil
import sys
from datetime import datetime, timedelta

from orb_backtest import DEFAULT_CSV, load_bars, resample
from tmf_trader.config import TZ
from tmf_trader.kbar import Bar

CSV_HEADER = ["datetime", "Open", "High", "Low", "Close", "Volume"]
FMT = "%Y-%m-%d %H:%M:%S"


# --------------------------------------------------------------------------- #
#  純函式：合併去重（可離線測試，不碰網路）
# --------------------------------------------------------------------------- #
def _key(b: Bar) -> str:
    """以本地牆鐘時間字串當唯一鍵；新舊資料格式一致才對得起來。"""
    return b.start.strftime(FMT)


def _date_windows(start: str, end: str, max_days: int = 30):
    """把 [start, end]（YYYY-MM-DD）切成不超過 max_days 天的連續分段。

    Shioaji kbars 單次上限 30 天，超過會回 400。用 max_days-1 的步距讓相鄰分段端點相接，
    重疊的那一天在後續 merge_bars 會自動去重，不會重複計。
    """
    s = datetime.strptime(start, "%Y-%m-%d").date()
    e = datetime.strptime(end, "%Y-%m-%d").date()
    if s > e:
        s = e
    cur = s
    while cur <= e:
        w_end = min(cur + timedelta(days=max_days - 1), e)
        yield cur.strftime("%Y-%m-%d"), w_end.strftime("%Y-%m-%d")
        cur = w_end + timedelta(days=1)


def infer_minutes(bars: list[Bar], default: int = 5) -> int:
    """從現有 CSV 推斷 K 線週期（分鐘）：讓 1 分檔保持 1 分、5 分檔保持 5 分。

    取相鄰 K 棒的時間差、濾掉跨盤/跨日的大跳空（>60 分），用出現最多次的間隔當週期。
    這樣使用者的檔案是幾分 K，更新後就還是幾分 K，不會被硬改成 5 分。
    """
    if len(bars) < 3:
        return default
    from collections import Counter
    gaps = Counter()
    for a, b in zip(bars, bars[1:]):
        diff = round((b.start - a.start).total_seconds() / 60)
        if 0 < diff <= 60:
            gaps[diff] += 1
    return gaps.most_common(1)[0][0] if gaps else default


def merge_bars(existing: list[Bar], fresh: list[Bar]) -> list[Bar]:
    """合併舊 + 新，依時間去重（重疊區間以 fresh 為準）、時間排序。

    以 fresh 覆蓋 existing 的用意：券商對「當日盤中先給、盤後修正」的 K 棒偶爾會微調，
    重抓的重疊區間視為更正確，所以讓新的贏。
    """
    merged: dict[str, Bar] = {}
    for b in existing:
        merged[_key(b)] = b
    for b in fresh:          # 後放的覆蓋先放的 → 新資料勝
        merged[_key(b)] = b
    return [merged[k] for k in sorted(merged)]


def write_csv(path: str, bars: list[Bar]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(CSV_HEADER)
        for b in bars:
            w.writerow([
                b.start.strftime(FMT),
                f"{b.open:g}", f"{b.high:g}", f"{b.low:g}", f"{b.close:g}",
                int(b.volume),
            ])


# --------------------------------------------------------------------------- #
#  Shioaji 抓取（需金鑰；無金鑰/未安裝時給清楚訊息）
# --------------------------------------------------------------------------- #
def fetch_fresh_bars(cat: str, contract_code: str, start: str, end: str,
                     minutes: int, simulation: bool) -> list[Bar]:
    try:
        import shioaji as sj
    except ImportError:
        sys.exit("❌ 尚未安裝 shioaji：請先 `pip install shioaji`（更新資料才需要，回測本身不需要）。")

    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # 沒裝 dotenv 也行，只要環境變數已設好

    key = os.getenv("SHIOAJI_API_KEY", "").strip()
    secret = os.getenv("SHIOAJI_SECRET_KEY", "").strip()
    if not key or not secret:
        sys.exit("❌ 找不到金鑰：請在 .env 或環境變數設定 SHIOAJI_API_KEY 與 SHIOAJI_SECRET_KEY。\n"
                 "   （只需這兩把 API 金鑰即可查 K 線，不需要 CA 憑證。）")

    print(f"登入 Shioaji（simulation={simulation}）… 只查資料、不下單")
    api = sj.Shioaji(simulation=simulation)
    api.login(api_key=key, secret_key=secret)
    one_min: list[Bar] = []
    epoch = datetime(1970, 1, 1)
    try:
        cat_obj = getattr(api.Contracts.Futures, cat)
        contract = cat_obj[contract_code]
        if contract is None:
            sys.exit(f"❌ 找不到契約 {cat}/{contract_code}（近月連續請用 TXFR1）。")

        # Shioaji kbars 單次上限 30 天，故切成 ≤30 天的分段逐段抓、再串起來。
        # 某一段失敗（例如超出免費歷史範圍）不中斷整體：警告後跳過，保住抓得到的部分。
        for w_start, w_end in _date_windows(start, end, max_days=30):
            print(f"抓取 {cat}/{contract_code} K 線：{w_start} → {w_end}")
            try:
                kb = api.kbars(contract, start=w_start, end=w_end)
            except Exception as e:      # noqa: BLE001 — 分段容錯，逐段回報
                print(f"  ⚠️  這段抓取失敗，跳過：{e}")
                continue
            d = {**kb}                  # keys: ts/Open/High/Low/Close/Volume/Amount
            ts = list(d.get("ts", []))
            if not ts:
                continue
            o, h, l, c, v = (list(d["Open"]), list(d["High"]), list(d["Low"]),
                             list(d["Close"]), list(d["Volume"]))
            for i in range(len(ts)):
                # Shioaji 的 ts 為奈秒，牆鐘即台北當地時間 —— 與 orb_backtest._to_dt
                # 對數字時戳的處理一致（建 naive 後視為台北）。
                naive = epoch + timedelta(seconds=float(ts[i]) / 1e9)
                one_min.append(Bar(TZ.localize(naive), float(o[i]), float(h[i]),
                                   float(l[i]), float(c[i]), int(float(v[i]))))
    finally:
        try:
            api.logout()
        except Exception:
            pass

    if not one_min:
        print("⚠️  整個區間沒有回傳任何 K 線（可能全部超出免費歷史範圍，或都非交易日）。")
        return []

    one_min.sort(key=lambda b: b.start)
    fresh = resample(one_min, minutes) if minutes > 1 else one_min
    print(f"取得 {len(one_min)} 根原始 1 分 K → 重新取樣成 {len(fresh)} 根 {minutes} 分 K")
    return fresh


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description="用 Shioaji 增量更新回測用 K 線 CSV")
    ap.add_argument("--csv", default=DEFAULT_CSV, help="要更新的 CSV（預設自動偵測）")
    ap.add_argument("--contract", default="TXFR1", help="契約代碼（近月連續，預設 TXFR1）")
    ap.add_argument("--cat", default="TXF", help="契約類別（預設 TXF）")
    ap.add_argument("--minutes", type=int, default=0,
                    help="重新取樣週期；0=自動比對現有 CSV 的週期（1 分檔存 1 分、5 分檔存 5 分）")
    ap.add_argument("--start", default=None, help="強制起始日 YYYY-MM-DD（預設：接續 CSV 最後一天）")
    ap.add_argument("--overlap-days", type=int, default=3,
                    help="接續抓取時往回多抓幾天以防漏單/修正（預設 3）")
    ap.add_argument("--simulation", action="store_true", help="登入模擬主機（預設登入正式主機查資料）")
    ap.add_argument("--dry-run", action="store_true", help="只抓、印摘要，不寫檔")
    ap.add_argument("--no-backup", action="store_true", help="寫檔前不建立 .bak 備份")
    args = ap.parse_args()

    existing = load_bars(args.csv) if os.path.exists(args.csv) else []
    minutes = args.minutes if args.minutes > 0 else infer_minutes(existing)
    if existing:
        last = existing[-1].start
        print(f"現有 CSV：{args.csv}\n  {len(existing)} 根，最後一根 {last:%Y-%m-%d %H:%M}")
        if args.minutes == 0:
            print(f"  自動判定週期：{minutes} 分 K（更新後維持同週期）")
    else:
        if args.minutes == 0:
            minutes = 5
        print(f"現有 CSV 不存在或為空：{args.csv}（將建立新檔，週期 {minutes} 分）")

    # 決定抓取起始日
    if args.start:
        start = args.start
    elif existing:
        start = (existing[-1].start - timedelta(days=args.overlap_days)).strftime("%Y-%m-%d")
    else:
        # 空檔又沒指定起始 → 保守抓近 30 天，避免一次要求超出免費範圍
        start = (datetime.now(TZ) - timedelta(days=30)).strftime("%Y-%m-%d")
        print(f"  未指定 --start 且無現有資料 → 預設抓近 30 天（{start} 起）")
    end = datetime.now(TZ).strftime("%Y-%m-%d")

    fresh = fetch_fresh_bars(args.cat, args.contract, start, end,
                             minutes, args.simulation)
    if not fresh:
        print("沒有新資料可合併，結束。")
        return 0

    merged = merge_bars(existing, fresh)
    added = len(merged) - len(existing)
    print(f"合併後共 {len(merged)} 根（淨增 {added} 根）；"
          f"涵蓋 {merged[0].start:%Y-%m-%d} ~ {merged[-1].start:%Y-%m-%d}")

    if args.dry_run:
        print("（--dry-run：未寫檔）")
        return 0

    if existing and not args.no_backup:
        bak = args.csv + ".bak"
        shutil.copy2(args.csv, bak)
        print(f"已備份舊檔 → {bak}")
    write_csv(args.csv, merged)
    print(f"✅ 已更新 {args.csv}。直接重跑回測即為最新資料。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
