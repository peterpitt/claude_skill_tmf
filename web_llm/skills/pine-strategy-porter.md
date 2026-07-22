---
name: pine-strategy-porter
description: 把 TradingView Pine v5 策略忠實移植成可回測的 Python，接進本系統的元件鏈。當使用者說「把這個 Pine 策略變成 Python」「這 54 個策略哪些值得移植」「幫我實作某指標策略」時使用。附 54 策略的 TMF 適用性分級。
source: pine_strategies/ (54 個 .pine + README.md)
---

# Pine 策略移植器

## 何時使用
- 「把 51 高效波段移植成 Python」「這 Pine 能接進系統嗎」「哪些策略值得測」。

## 適用性分級（pine_strategies/README.md）
- 🟢 **值得移植/回測**：51 高效波段、50 多空對翻、11 均線多空排列、10 MACD、14 DMI（低頻波段）；出場模組 31–40；濾網 41–48。
- 🟡 **可移植但邊際存疑**：08 RSI、09 KD、13 CDP、20 箱型、52 日內（多為高頻，摩擦風險高）。
- 🔴 **不適用**：01–07（純語法教學）、23/24/54（價差套利，需第二檔報價，本系統單檔不支援）。

## 移植守則
1. **無前視**：訊號用「已收盤的 K」，成交用「次根開盤」。
2. **接進同一條鏈**：移植後必須能被 `swing_backtest.py` / `combo_backtest.py` 逐年回測，不可另寫簡化版。
3. **標註 Pine 原檔換行遺失問題**：來源 Word 遺失段內換行，貼進 TradingView 前需逐行校對；移植時以邏輯為準、不照抄壞行。

## 交棒
移植完成 → `backtest-runner` 逐年跑 → `robustness-validator` 把關 → `evidence-grounding-review` 核對邊際宣稱。

## 一句話
這份課程的價值在**出場(D)＋濾網(E)**這些降摩擦模組，不在多數會被摩擦磨死的高頻進場指標。
