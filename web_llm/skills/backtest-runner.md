---
name: backtest-runner
description: 用「與實盤完全相同的元件鏈」對台指期資料跑逐年回測並輸出風報比。當使用者要回測某策略、比較週期、驗證某參數、或問「這策略績效如何」時使用。需要一份 K 線 CSV（datetime,Open,High,Low,Close,Volume）與一個契約代碼。
source: backtest.py, orb_backtest.py, swing_backtest.py, combo_backtest.py
---

# 回測執行器

## 何時使用
- 「幫我回測 X 策略」「跑一下 backtest.py」「30 分跟 15 分哪個好」「這參數逐年如何」。

## 選對腳本
| 目的 | 腳本 |
|---|---|
| 一般 tick/合成市場 + grid search | `backtest.py --symbol TMF --optimize` |
| ORB 日內、逐年 + 64 組網格 | `orb_backtest.py --csv <csv> --symbol TMF --optimize` |
| 低頻波段訊號（效率比/DMI/MACD/均線）逐年 | `swing_backtest.py --csv <csv> --symbol TMF` |
| 高效波段 × 濾網/出場 15m vs 30m | `combo_backtest.py --csv <csv> --symbol TMF` |

## 鐵律
1. **回測與實盤同源**：tick → `KBarAggregator → FVDTracker → Strategy → PositionBook → SessionManager`，並重放斷路器/停損/強制平倉。不得另寫一份簡化回測。
2. **次根開盤成交、無前視**；成本每邊約 15 元 + 滑價 1 點/邊，務必套用（歸零只用於診斷）。
3. **一定要逐年看**，不能只看全期間總和 —— 逐年才看得出穩不穩。

## 輸出（固定欄位）
勝率、PF（獲利因子）、淨利(以 TMF $10/點計)、最大回落、恢復係數(淨利/回落)、交易筆數、**獲利年數 n/7**。

## 交棒
- 得到「最佳一組」後，交給 `robustness-validator` 做跨樣本檢驗，**別直接相信單一結果**。
- 任何「有邊際」的結論交給 `evidence-grounding-review` 核對數字。
