---
name: intent-classification
description: 系統技能（對應 Athena 的 Mission Classification）。把使用者訊息分類到正確的 Model：回測分析 / 策略移植 / 實盤諮詢 / 自主研究。tmf-router 用它做第一層路由。不做業務、只分類與轉派。
type: system
athena_equivalent: Mission Classification
---

# 意圖分類（路由用）

## 職責
讀使用者訊息，輸出一個目標 Model 標籤與信心分數；不回答業務問題。

## 分類表
| 使用者在說… | → Model |
|---|---|
| 「回測 / 績效 / 參數 / 哪個週期好 / 這策略賺嗎」 | `tmf-backtest-analyst` |
| 「把 Pine 變 Python / 移植 / 實作某指標策略」 | `pine-porter` |
| 「可以上線嗎 / 斷路器 / 時段 / 契約金額 / 風控」 | `tmf-live-ops-guard` |
| 「幫我想個新策略方向 / 自己去研究 / 反覆試」 | `tmf-strategy-researcher` |
| 模糊、跨多類 | 回問一句釐清，或預設 `tmf-backtest-analyst` |

## 輸出格式
`{"target_model": "...", "confidence": 0.0-1.0, "reason": "一句話"}`

## 邊界
- 若訊息涉及**送真錢單**，一律先強制附掛 `scope-boundary-guard`，再路由。
