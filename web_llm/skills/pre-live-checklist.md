---
name: pre-live-checklist
description: 從模擬到真錢實單前的逐項安全檢查清單。當使用者說「我可以上線了嗎」「正式下單前要檢查什麼」「可以關掉 DRY_RUN 嗎」時使用。本技能只產生清單並要求使用者自己逐項確認，永遠不代按真錢、不說「你可以上了」。
source: README.md（上線前檢查清單、三層安全閘）
---

# 上線前檢查清單（只檢查，不放行）

## 何時使用
- 「可以上線嗎」「關掉模擬前要確認什麼」「真錢前檢查」。

## 三層安全閘（由寬到嚴，來自 README）
| 模式 | .env 設定 | 行為 |
|---|---|---|
| 🟢 DRY_RUN | `DRY_RUN=true` | 只算訊號、印「將下單」，不送單（預設） |
| 🟡 模擬主機 | `DRY_RUN=false` `SIMULATION=true` | 送永豐模擬主機（假錢，不需 CA） |
| 🔴 真錢實單 | `DRY_RUN=false` `SIMULATION=false` + `LIVE_TRADING_CONFIRM=I_UNDERSTAND_THE_RISK` | 真錢，需 CA 憑證 |

## 逐項清單
- [ ] `python tests/test_core.py` 全綠
- [ ] `python main.py --check` 顯示的契約/每點價值/停損金額符合預期
- [ ] 策略已用**真實 `txf_kbars.csv` 逐年回測**、且 `evidence-grounding-review` 通過
- [ ] 已通過 `robustness-validator` 跨樣本檢驗（非單樣本冠軍）
- [ ] 在 🟡 模擬主機跑滿一個完整早盤 + 夜盤
- [ ] 手動驗證：強制平倉窗確實平倉、−2890 斷路器確實鎖單
- [ ] `.env`、`*.pfx` 未被提交（`.gitignore` 已含）
- [ ] 真錢首次用**最小口數**且全程盯盤

## 邊界（絕對遵守）
- 本技能**只**輸出清單並請使用者自行勾選，**不**替使用者判斷「你準備好了」，**不**修改 .env、**不**送任何真錢單。
- 只要有任一項未確認，一律回覆「尚不建議上線」。
