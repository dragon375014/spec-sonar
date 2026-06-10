# spec-sonar

> 找出你不知道你不知道的事，然後讓任何 AI 模型都能執行。

**[English README](README.md)**

spec-sonar 是一個開源工具鏈，把模糊的產品想法轉成可執行、跨模型通用的規格。讓強模型（Claude Opus / Fable）**做一次**深度設計，產出固化成結構之後，任何便宜的模型——Haiku、Sonnet、Cursor、Copilot、GPT——都能**可靠地**執行。

## 為什麼需要它

AI coding agent 很少因為「不會寫程式」而失敗，它們失敗在**沒人寫下來的東西**：沒說出口的需求、互相矛盾的限制、沒人想到要問的維度。spec-sonar 用三個機制直接攻擊這個缺口：

1. **暗區偵測**——把軟體規格系統性遺漏的維度做成結構化清單（10 個基準維度 + 五種產品類型擴充包），由 5–7 輪問答引擎驅動，全程追蹤已知（亮區）與未知（暗區）。
2. **Goal 編譯**——把規格分解成自包含 goal 檔的依賴圖。所有設計決策在分解期由強模型**裁決前置**，執行模型永遠不需要猜。
3. **Adapter 投影**——同一份規格投影成 `CLAUDE.md`、`.cursor/rules`、`copilot-instructions.md` 和通用 system prompt。規格寫一次，到處能跑。

## 三層架構

```
┌─────────────────────────────────────────────────────────────┐
│ 第一層 · idea-to-spec（skill，已完成）                        │
│   模糊想法 ── 5–7 輪問答 ──► CLAUDE.md + STATE_FINAL.json    │
│   暗區追蹤 · 衝突處理協議 · 重複造輪子偵測                     │
├─────────────────────────────────────────────────────────────┤
│ 第二層 · goal-decomposer（skill，已完成）                     │
│   規格 ── 依賴推導   ──► goal-graph.json                     │
│        ── 裁決前置   ──► goals/G*.md（自包含）                │
│        ── 介面凍結   ──► contracts/C*.md                     │
├─────────────────────────────────────────────────────────────┤
│ 第三層 · 執行層（任何模型）                                    │
│   Haiku / Sonnet / Cursor / Copilot / GPT 按圖執行           │
│   用 BLOCKED 協議取代猜測                                     │
└─────────────────────────────────────────────────────────────┘
```

## 三種使用模式

| 模式 | 輸入 | 目的 |
|------|------|------|
| **From Zero** | 模糊想法 | 5–7 輪收斂成規格 |
| **Audit** | 現有專案描述、文件、或 `project-scanner.py` 指紋 | 找出既有設計的空洞（每維度判定亮 / 灰 / 暗 / 衝突） |
| **Complex System** | ERP / 多模組 SaaS | 兩層分解 + 跨子系統契約 |

## 快速開始

```bash
git clone https://github.com/<you>/spec-sonar
# 安裝 skills 到 Claude Code
cp -r skills/idea-to-spec  ~/.claude/skills/
cp -r skills/goal-decomposer ~/.claude/skills/
```

1. 跟 Claude 說你的想法——「我想做一個瑜珈教室預約系統」。idea-to-spec 引擎跑 5–7 輪聚焦問答，用 `<STATE>` 區塊追蹤亮區/暗區，最後交付 `README.md` + `CLAUDE.md` + `STATE_FINAL.json`。
2. 說「分解這份規格」。goal-decomposer 把它編譯成 `goal-graph.json` + 自包含的 `goals/G*.md` + 凍結的 `contracts/C*.md` + 四平台 adapter。
3. 把 goal 檔按依賴順序餵給**任何**模型（同批次可平行）。每個 goal 檔都通過「冷啟動測試」：一個沒有任何對話脈絡的執行者能回答——做什麼、怎麼驗證、不能做什麼、卡住怎麼辦。

審查既有專案：

```bash
python tools/project-scanner.py /path/to/project -o scan/project-fingerprint.md
# 然後把指紋交給 Audit Mode（modes/audit-mode.md）
```

## 可攜性保證

goal 檔不是「寫得清楚的任務說明」，而是一種**消除執行模型自由度**的格式。八條機制（詳見 [docs/model-portability.md](docs/model-portability.md)）：

自包含原則 · 裁決前置 · 介面字面凍結（給 JSON 實例，不給 schema 描述） · 驗證機械化 · BLOCKED 協議取代猜測 · 負向驗收（可測試的「不做」） · 自檢 footer · 冷啟動測試作為合格判準。

## 目錄結構

```
skills/
  idea-to-spec/            需求收斂引擎（SKILL.md + references）
  goal-decomposer/         規格 → goal 圖編譯器（SKILL.md）
modes/
  audit-mode.md            既有設計的暗區偵測
  conflict-analysis-mode.md  skill 生態衝突分析
tools/
  project-scanner.py       純標準庫的程式碼指紋工具（輸出 <20 KB）
schemas/
  goal-graph.schema.json   依賴圖的 JSON Schema
docs/
  output-directory-spec.md · adapter-formats.md · model-portability.md
  review-findings.md · value-analysis.md
examples/
  mathdefense/             真實端到端案例（規格 → 圖 → goal 檔）
  conflict-report-sample.md
```

## 案例研究：mathdefense

一個真實的課堂即時多人塔防數學遊戲：從模糊想法經 6 輪收斂成完整規格，再分解成 7 個 goal + 2 份契約、5 個執行批次。對自己產出跑 audit 抓到三個真實的規格空洞（單位數值缺失、殭屍移動模型未定、重連身份需求與「不做帳號」規則相撞）——詳見 [docs/review-findings.md](docs/review-findings.md)。

## 路線圖

- [ ] 兩份 SKILL.md 的英文原生版
- [ ] Eval harness：量測暗區覆蓋率與 goal 冷啟動通過率
- [ ] Audit Mode 與 Conflict Analysis Mode 打包成可執行 skill
- [ ] 更多端到端範例（B2B SaaS、Marketplace、內部工具）
- [ ] `goal-graph.json` 執行器（自動按批次分派給模型）

## 貢獻

見 [CONTRIBUTING.zh-TW.md](CONTRIBUTING.zh-TW.md)。最有價值的貢獻：有真實失敗案例佐證的新暗區維度、產品類型擴充包、更多平台的 adapter 格式。

## 授權

[MIT](LICENSE)
