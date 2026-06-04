# claude_skill_tmf — 台指期自動當沖系統 (TMF / MXF)

以 **Shioaji（永豐金）API** 開發、可在本地 **tmux** 穩定運行的台指期當沖機器人。
訊號取自**大台 TXF**，實際下單於**微型/小型台指**，並內建一個**獨立於主程序的風控斷路器**。

> ⚠️ **這是會動到真錢的程式。預設一律 `DRY_RUN`（只算訊號、不送單）。**
> 在你完全讀懂每一行、跑過模擬、並確認風控行為前，**請勿**切到真錢實單。
> 期貨為槓桿商品，可能虧損超過本金。本專案僅供研究，作者不對任何虧損負責。

---

## ⚠️ 重要：MXF 還是 TMF？（攸關你的風控數字）

你的需求寫「微型台指期 (MXF)」，但台灣期交所上這是**兩個不同契約**：

| 代碼 | 中文 | 每點價值 | 2,890 元 ≈ 幾點 |
|------|------|---------:|----------------:|
| `TXF` | 臺股期貨（大台） | NT$200 | — (僅作訊號) |
| `MXF` | 小型臺指（小台） | NT$50 | ≈ 57 點 |
| `TMF` | **微型臺指（微台）** | **NT$10** | ≈ 289 點 |

- 「微型」對應的其實是 **TMF**，每點僅 NT$10，部位風險最小。
- 本專案資料夾名為 `tmf`、需求又強調「微型」，故 **預設下單契約 = `TMF`**。
- 若你確定要下**小台 MXF**，把 `tmf_trader/config.py` 的 `order_symbol` 改成 `"MXF"`
  （或設環境變數 `ORDER_SYMBOL=MXF`）。風控、停損金額會依每點價值**自動換算**。

對 **70,000 元** 的本金，預設 TMF（單筆停損 ≈200 元、當日斷路 2,890 元 ≈ 全額的 4.1%）
是相對保命的配置。

---

## 策略邏輯

- **訊號分離**：訂閱 **TXF** 即時 Tick + BidAsk，自行合成 **5 分 K 線**。
- **進場條件**（每根 5 分 K 收盤評估一次，避免盤中假突破）：
  - 多：收盤**由下而上突破 21MA**，且 **FVD（內外盤委託動能）≥ +門檻**。
  - 空：收盤**由上而下跌破 21MA**，且 **FVD ≤ −門檻**。
  - **FVD** = 最近 N 秒「外盤成交量 − 內盤成交量」的累積（`tick_type` 1=外盤/2=內盤）。
- **出場**：均線反向、單筆停損（預設 20 點）、或收盤前強制平倉。
- **實際下單**：訊號確認後對 **TMF/MXF 當月**送出**範圍市價（IOC）**，平倉用市價確保出得掉。

## 時段切割

| 時段 | 時間 | 進場上限 |
|------|------|----------|
| 早盤 | 08:45 – 13:45 | 4 次（獨立計算） |
| 夜盤 | 15:00 – 隔日 05:00 | 4 次（獨立計算） |

- 收盤前 **15 分鐘**：強制平倉所有部位、撤單、停止新進場，**絕不留倉**。

## 風控斷路器（保命核心）

獨立 `threading.Thread`，每秒加總「**已實現 + 未平倉浮動損益**」。
當日累計虧損達 **2,890 元** 立即且只觸發一次：

1. **市價平倉**所有未平倉部位
2. **撤銷**所有未成交委託
3. 寫入 **CRITICAL log**，並**鎖定當日下單權限**直到下一交易日（換日自動重置）

斷路器以 `try/except` 包覆，**絕不因例外停擺**；觸發動作以 callback 注入，與券商層解耦、可測試。

---

## 安裝與執行

```bash
# 1. 安裝相依
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. 設定金鑰
cp .env.example .env
#   編輯 .env：填 API key / secret；先保持 DRY_RUN=true、SIMULATION=true

# 3. 自我檢查（不連線、不下單）
python main.py --check

# 4. 跑單元測試（驗證損益/斷路器/時段邏輯）
python tests/test_core.py

# 5. tmux 常駐執行
chmod +x run.sh
./run.sh          # 在 tmux session 'tmf' 啟動（crash 自動重啟）
./run.sh attach   # 連入觀看即時 log
./run.sh stop     # 停止
```

### 三層安全閘（由寬到嚴）

| 模式 | `.env` 設定 | 行為 |
|------|------------|------|
| 🟢 DRY_RUN | `DRY_RUN=true` | 只算訊號、印出「將要下單」，**不送單**（預設） |
| 🟡 模擬主機 | `DRY_RUN=false` `SIMULATION=true` | 送永豐**模擬**主機（假錢，不需 CA） |
| 🔴 真錢實單 | `DRY_RUN=false` `SIMULATION=false` + `LIVE_TRADING_CONFIRM=I_UNDERSTAND_THE_RISK` | 真錢，需 CA 憑證 |

少了最終確認鎖，程式會**拒絕**用真錢啟動。

---

## 專案結構

```
main.py                進入點（--check 可只驗設定）
run.sh                 tmux 常駐 / 連入 / 停止
requirements.txt
.env.example           設定範本（複製成 .env）
tmf_trader/
  config.py            風控門檻、時段、契約規格（所有關鍵數字集中於此）
  logger.py            檔案 + 終端機 log（Asia/Taipei 時戳）
  broker.py            Shioaji 登入 / 契約 / 下單 / 撤單 / 查部位
  position_book.py     內部部位簿：成交回報即時算已實現/未實現損益
  market_data.py       FVD 內外盤動能 + 委買賣失衡
  kbar.py              5 分 K 合成 + 21MA
  strategy.py          進出場訊號
  session.py           早/夜盤、出手次數、強制平倉窗
  risk.py              獨立執行緒風控斷路器
  trader.py            主協調器（串接全部 + 三道下單閘）
tests/test_core.py     損益 / 斷路器 / 時段 單元測試
```

## 調整參數

全部在 `tmf_trader/config.py`：`order_symbol`、`order_quantity`、`ma_period`、
`fvd_window_seconds`、`fvd_entry_threshold`、`daily_max_loss_twd`、
`per_trade_stop_points`、`max_entries_per_session`、`force_close_minutes_before`。

啟動時 `config.validate()` 會擋掉危險組態（例如單筆停損金額大於當日斷路器）。

## 上線前檢查清單

- [ ] `python tests/test_core.py` 全綠
- [ ] `--check` 顯示的契約 / 每點價值 / 停損金額符合預期
- [ ] 先在 🟡 模擬主機跑滿一個完整早盤 + 夜盤
- [ ] 手動驗證：強制平倉窗確實平倉、斷路器確實鎖單
- [ ] 確認 `.env`、`*.pfx` 未被提交（已列入 `.gitignore`）
- [ ] 真錢首次務必用**最小口數**，並全程盯盤
