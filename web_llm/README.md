# 把 `claude_skill_tmf` 打造成一個 Web LLM（Skills + Models）

> 對照你截圖裡的 **Ericsson Athena** 平台：左圖是 *Skill Creator* 列出一堆原子技能
> （`5gc-alarm-report`、`Drop Call Analyzer`、`Mission Classification`…），右圖是
> *Models* 列出 35 個由「技能 + 知識庫 + 基礎推理模型」組成的 **Agent**
> （`Packet Core Alarm Agent V4`、`AthenaRAN-NR-ALPHA`、`Log Analysis Agent (LTNG Decoder)`…）。
>
> 本文件把**你這個台指期交易專案**用同一套方法拆解成可上架的 **Skill.md** 與 **Model**。

---

## 一、Athena 的兩層結構（先對齊觀念）

| Athena 名詞 | 是什麼 | 在本專案的對應 |
|---|---|---|
| **Skill**（skill.md） | 一個**原子能力**：一段 name + description + instructions，描述「何時用、要哪些輸入、產出什麼」 | 你 `tmf_trader/` 裡每一個單一職責模組（策略、風控、時段、出場、濾網…）＋每一支回測腳本 |
| **Knowledge** | Agent 可檢索的資料/文件庫 | `BACKTEST.md`（逐年真實資料結論）、`pine_strategies/`（54 個策略）、`README.md`、你的 `txf_kbars.csv` |
| **Model / Agent** | 基礎推理模型 **＋** 一組 Skills **＋** 一個 Knowledge，組成一個對外的角色 | 下面第三節的 5 個 Model（回測分析師、實盤守門員、Pine 移植器、策略研究員、路由器） |
| **System Skill**（Mission Classification、Scope Boundary…） | 不做業務、負責**編排/守門**的技能 | `intent-classification`、`scope-boundary-guard`、`evidence-grounding-review` |

一句話：**Skill = 一個模組的「使用說明卡」；Model = 一位帶著某些卡片與某本知識庫上工的專家。**

---

## 二、Skills 清單（14 個，檔案在 `web_llm/skills/`）

### A. 領域技能（Domain — 直接對應程式碼與資料）

| Skill | 對應的程式碼 / 資料 | 職責 |
|---|---|---|
| `tmf-contract-spec` | `config.py:CONTRACT_SPECS` | TXF/MXF/TMF 契約規格、每點價值、風控金額換算 |
| `backtest-runner` | `backtest.py` `orb_backtest.py` `swing_backtest.py` `combo_backtest.py` | 用同一套實盤程式跑逐年回測、輸出風報比 |
| `robustness-validator` | `backtest.py:optimize()/robustness()` | 跨種子/walk-forward 檢驗，揭穿單樣本過度配適 |
| `swing-signal-library` | `strategy_efficiency.py`、`swing_backtest.py` | 低頻波段訊號：效率比、DMI、MACD、均線多空排列 |
| `orb-intraday-analyzer` | `strategy_orb.py`、`strategy.py` | 開盤區間突破/逆勢訊號分析（附「日內逐年皆虧」鐵證） |
| `exit-module-designer` | ORB trailing、pine 31–40 | 固定/百分比/移動/ATR/時間出場設計 |
| `filter-module-designer` | `filters.py`、pine 41–48 | 去頻繁交易、虧損冷靜期、熱門時段、動能濾網 |
| `risk-circuit-breaker` | `risk.py` | 獨立執行緒 −2890 斷路器：平倉+撤單+鎖單 |
| `session-scheduler` | `session.py` | 早/夜盤切割、每盤 4 次、收盤前強制平倉窗 |
| `pine-strategy-porter` | `pine_strategies/` | 把 Pine v5 策略忠實移植成可回測的 Python |
| `pre-live-checklist` | `README.md` 上線清單、三層安全閘 | 由模擬→真錢前的逐項安全檢查（只檢查、不代按） |

### B. 系統技能（System — 編排與守門，對應 Athena 的 Mission Classification 等）

| Skill | Athena 對應 | 職責 |
|---|---|---|
| `intent-classification` | Mission Classification | 判斷使用者要：回測 / 移植 / 上線諮詢 / 參數最佳化，路由到對的 Model |
| `scope-boundary-guard` | Scope Boundary Definition | **鐵律：沒有三層確認鎖，一律不送真錢單**；把 DRY_RUN→模擬→真錢的邊界寫死 |
| `evidence-grounding-review` | Evidence Grounding Review | 任何「這策略有邊際」的宣稱**必須引用逐年回測數字**，否則駁回 |

---

## 三、Models 清單（5 個，檔案在 `web_llm/models/`）

| Model | ≈ Athena 的 | Base | 掛載的 Skills | Knowledge |
|---|---|---|---|---|
| `tmf-backtest-analyst` | Packet Core Alarm Agent V4 | 大型推理模型 | backtest-runner, robustness-validator, swing-signal-library, orb-intraday-analyzer, evidence-grounding-review | `BACKTEST.md` + `txf_kbars.csv` |
| `tmf-live-ops-guard` | NR AMOS CLI Checker（唯讀守門） | 推理模型 | risk-circuit-breaker, session-scheduler, pre-live-checklist, scope-boundary-guard, tmf-contract-spec | `README.md` |
| `pine-porter` | Log Analysis Agent (LTNG Decoder) | 推理模型 | pine-strategy-porter, exit-module-designer, filter-module-designer, backtest-runner | `pine_strategies/` |
| `tmf-strategy-researcher` | autonomous-researcher | 大型推理模型 | 上述全部（自主研究迴圈） | 全部 |
| `tmf-router` | Mission Classification（系統 Agent） | 輕量模型 | intent-classification | — |

**組裝關係（就是 Athena 「Model = Skills + Knowledge」的具體化）：**

```
                         ┌─────────────────┐
   使用者 ──▶ tmf-router ─┤ intent 分類     │
                         └───────┬─────────┘
              ┌──────────────────┼───────────────────┬─────────────┐
              ▼                  ▼                   ▼             ▼
   tmf-backtest-analyst   pine-porter        tmf-live-ops-guard  tmf-strategy-researcher
   ├ backtest-runner      ├ pine-strategy-   ├ risk-circuit-     └ (全部技能 + 全部知識,
   ├ robustness-validator │  porter          │  breaker             自主提出假設→回測→修正)
   ├ swing-signal-library ├ exit-module-     ├ session-scheduler
   ├ orb-intraday-analyzer│  designer        ├ pre-live-checklist
   └ evidence-grounding   ├ filter-module-   └ scope-boundary-guard  ◀── 貫穿所有 Model 的安全底線
     -review              │  designer
                          └ backtest-runner
   Knowledge: BACKTEST.md   Knowledge:         Knowledge: README.md
             + txf_kbars     pine_strategies/
```

---

## 四、為什麼你這個專案「天生」適合這樣拆

1. **模組已單一職責**：`tmf_trader/` 的 broker / risk / session / strategy / position_book 各司其職 —— 這正是「一個模組 = 一個 Skill」的前提。你不用重寫，只要替每個模組寫一張「使用說明卡」。
2. **回測與實盤同源**：`backtest.py` 餵 tick 進**與實盤完全相同**的元件鏈。所以 `backtest-runner` Skill 天生可信 —— Model 給出的結論可回溯到真實程式。
3. **已有 Knowledge 沉澱**：`BACKTEST.md` 是逐年真實資料的結論，`pine_strategies/README.md` 是 54 策略的適用性分析 —— 現成的檢索知識庫。
4. **安全邊界明確**：三層安全閘（DRY_RUN→模擬→真錢）＋ −2890 斷路器，天生對應 Athena 的 *Scope Boundary* 與守門系統技能。

---

## 五、延伸：你「從開始用 Claude 到現在」的整個專案家族 → 一個 35-Model 生態

你截圖右邊 Athena 有 **35 個 Model**。你的專案家族（從本機 Skill 清單可見）其實已經是同樣規模的生態，可直接對映：

| 你的專案（現有 Claude Skill） | 對應成 Athena 式 Model |
|---|---|
| `quant-trading-hub`（路由/索引） | = **Mission Classification** 系統 Model（就是本專案的 `tmf-router` 放大版） |
| `quant-backtest-analysis` | = 回測分析師 Model（本專案 `tmf-backtest-analyst` 是它的 TMF 特化） |
| `quant-live-trading-ops` / `pre-trade-checklist` | = 實盤守門員 Model（`tmf-live-ops-guard`） |
| `quant-live-monitoring` | = 即時監控 Dashboard Agent |
| `masterlink-swiftui-dev` / `cosmo-weather-dev` / `travel-planner-app-dev` … | = 各 App 的 Dev Agent（一個專案一個 Model，如 Athena 一個網元一個 Agent） |
| `skill-creator` / `ai-collaboration-builder` | = **Skill Creator** 本體（跟你左圖那個一模一樣） |

> 換句話說：**你已經在用「Skill + Model」的方式管理專案了** —— Claude 的 SKILL.md 生態
> 與 Athena 的 web-LLM 是同構的。本資料夾只是把 `claude_skill_tmf` 這一支，
> 明確地「上架成 Athena 格式」，作為其餘專案照做的範本。

---

## 六、怎麼實際跑起來（落地路徑）

- **選項 A｜留在 Claude 生態**：把 `web_llm/skills/*.md` 轉成標準 `SKILL.md`（加 frontmatter），
  放進 `.claude/skills/`，即可被 Claude Code / claude.ai 觸發。Model 定義則對應成一份 system prompt + 掛哪些 skill。
- **選項 B｜自架 Web LLM（像 Athena / Open WebUI）**：
  1. 起一個 Open WebUI + 一顆本地/雲端推理模型；
  2. 把每個 `skills/*.md` 的 description 貼進該平台的「Tools / Functions」或「Skill」欄；
  3. 把 `BACKTEST.md`、`pine_strategies/`、`txf_kbars.csv` 上傳成 **Knowledge**；
  4. 依 `models/*.md` 建立 5 個 Model（各自綁定 system prompt + 該掛的 skills + knowledge）。
- **安全提醒**：`tmf-live-ops-guard` 與所有 Model 都必須保留 `scope-boundary-guard` —— 任何
  Web LLM 版本**都不得**繞過三層安全閘去送真錢單。LLM 只做分析與建議，**真錢按鈕永遠留給人**。

> 每個 Skill 與 Model 的完整定義見 `web_llm/skills/` 與 `web_llm/models/`。
