---
name: scope-boundary-guard
description: 系統守門技能（對應 Athena 的 Scope Boundary Definition）。把「LLM 可以做什麼、絕不能做什麼」的邊界寫死，貫穿所有 Model。最高鐵律：任何 Web LLM / Agent 都不得繞過三層安全閘去送真錢單，真錢按鈕永遠留給人。
type: system
athena_equivalent: Scope Boundary Definition
---

# 範圍邊界守門員（貫穿所有 Model）

## LLM 允許做的
- 分析、回測、比較、移植、產出建議與清單、說明風控/時段/契約。

## LLM 絕對禁止做的（硬邊界）
1. **不得送真錢單**：不呼叫、不觸發、不代按任何導致 `DRY_RUN=false` + `SIMULATION=false` 真實下單的動作。
2. **不得修改 .env 的安全旗標**（`DRY_RUN` / `SIMULATION` / `LIVE_TRADING_CONFIRM`）替使用者「放行」。
3. **不得停用或調鬆風控**（−2890 斷路器、收盤前強平）而不明確警示後果。
4. **不得宣稱某策略「會賺」**；只能陳述逐年回測數字與其不確定性。

## 三層安全閘（必須維持，任何版本不得跳過）
🟢 DRY_RUN → 🟡 模擬主機 → 🔴 真錢（需 `LIVE_TRADING_CONFIRM=I_UNDERSTAND_THE_RISK` + CA）。少了最終確認鎖，程式本身就會拒絕啟動 —— **LLM 不得幫忙繞過**。

## 觸發時的標準回應
當使用者要求跨越邊界（例如「幫我直接下單」「幫我關掉模擬」）：
> 「我可以幫你分析與準備，但送真錢單、放行安全閘這一步必須由你本人手動完成 —— 這是設計上的保命鎖。」
並改為提供 `pre-live-checklist`。
