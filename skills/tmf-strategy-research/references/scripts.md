# 回測腳本速查

五支腳本都吃真實 K 線 CSV、**次根開盤成交（無前視）**、可設成本/滑價。
預設下單契約 `TMF`（NT$10/點）。CSV 欄位：`datetime,Open,High,Low,Close,Volume`；
時間戳預設視為台北時間（`orb_backtest.py` 可用 `--ts-utc` 改）。

> 📂 **CSV 自動偵測（換檔即更新，免改程式）**：`orb_backtest.py` 的 `resolve_default_csv()`
> 依序找檔——(1) 環境變數 `TXF_CSV` 指定的完整路徑；(2) 專案資料夾裡的慣用檔名
> `txf_kbars.csv` / `TXFR1_5min_5years.csv`；(3) 專案資料夾裡檔名含 `TXF`/`5min`/`kbar` 的 CSV；
> (4) 專案裡剛好只有一個 CSV 時直接用。所以**把最新 K 線 CSV 放進專案資料夾、或設 `TXF_CSV`，
> 之後覆寫同一個檔就會自動更新**，不必再改任何腳本。仍可用 `--csv` 臨時指定別的檔。

## 用哪一支？

| 想驗證的東西 | 用這支 | 為什麼 |
|---|---|---|
| 低頻波段訊號哪個好、哪個時間框架好 | `swing_backtest.py` | 5 個波段訊號 × 多週期逐年比較 |
| 高效波段要不要加濾網、15m vs 30m | `combo_backtest.py` | 把課程濾網(41/42/43/35)逐一套上去比 |
| 日內開盤區間突破（研究用，已知逐年虧） | `orb_backtest.py` | 純 K 線可 100% 回測，含 grid search |
| 時間過濾型前高/前低突破（日內 +−2890 斷路） | `prevhl_backtest.py` | 移動停利/固定停損兩種出場 |
| 舊版 21MA+FVD、或驗引擎/合成市場穩健性 | `backtest.py` | 與實盤同一套元件；含最佳化與跨種子穩健性 |

## 指令範例

```bash
# 波段訊號逐年比較（策略鍵：ma / macd / dmi / eff / flip；tf 可給分鐘數或 daily 或 all）
python swing_backtest.py --csv /path/txf_kbars.csv --symbol TMF               # 全部策略 × 全部週期
python swing_backtest.py --csv /path/txf_kbars.csv --strategy eff --tf 30 --detail   # 高效波段 30m 逐年明細

# 高效波段 × 濾網/動態出場，15m vs 30m
python combo_backtest.py --csv /path/txf_kbars.csv --symbol TMF

# ORB 日內（mode: fade 逆勢 / breakout 追突破；--optimize 跑 grid search）
python orb_backtest.py --csv /path/txf_kbars.csv --symbol TMF --mode breakout --optimize
python orb_backtest.py --csv /path/txf_kbars.csv --resample 5 --ts-utc          # CSV 為 UTC 時戳時

# 前高/前低突破（--exit: breakout_stop / trail / both）
python prevhl_backtest.py --csv /path/txf_kbars.csv --exit both --stop 40

# 舊版 MA+FVD / 引擎穩健性（無 --csv 時用合成市場，僅驗引擎不代表真實邊際）
python backtest.py --csv /path/txf_kbars.csv --symbol TMF --optimize
python backtest.py --symbol TMF --days 60 --optimize                            # 合成市場（勿當真實結論）
```

## 共同旗標

| 旗標 | 預設 | 說明 |
|---|---|---|
| `--csv` | 作者本機路徑 | 真實 K 線 CSV，**務必自行指定** |
| `--symbol` | `TMF` | `TMF`(NT$10) / `MXF`(NT$50) / `TXF`(NT$200)；風控金額會依每點價值換算 |
| `--cost` | `15.0` | 單邊成本 TWD（手續費+稅） |
| `--slippage` | `1.0` | 單邊滑價點數 |

改成本/滑價做敏感度分析很有用：若一個策略把成本設 0 才會賺，它就是輸的（真實無法零成本）。

## 讀輸出時盯這幾個數

- **獲利年數**（例 6/7）：比總淨利更能說明穩健度。
- **恢復係數**（淨利 ÷ 最大回落）：>2 才算像樣；越高越能扛回落。
- **最大回落 MDD**：換算成佔 7 萬本金的 %。逼近本金就是爆倉風險，再高的淨利都要否決。
- **PF 獲利因子**：<1 代表沒邊際（含成本後）。
- **交易筆數**：太少（如 <100 或某年個位數）→ 樣本不足、結論不可信。
