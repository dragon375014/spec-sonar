# 四平台 Adapter 格式規範

<!-- spec-sonar v1.0 -->

共同規則：四個 adapter 都是 `spec/` 的**投影**，檔頭帶 provenance 註記，
永不手改。差異在於各平台的讀取模型不同——Claude Code 會執行任務、
Cursor 是編輯情境、Copilot 只做補全、通用 agent 看 system message。

---

## 1. `adapters/CLAUDE.md`（Claude Code）— 部署到專案根目錄

唯一會「執行 goal」的平台，所以包含執行協議。
必要區塊：專案目標 / 技術棧 / **goal 執行協議** / 明確不做 / 安全規則。

```markdown
# {project} — 專案規格
<!-- generated from spec/ — edit spec/, then regenerate -->

## Goal 執行協議
1. 讀 spec/goal-graph.json，找 status=ready 且依賴全 verified 的 goal
2. 只讀對應的 spec/goals/G*.md（檔案自包含，不需讀其他 goal）
3. 按五元素執行；遇歧義輸出 BLOCKED，不猜
4. 自檢 footer 全綠後，將 goal-graph.json 中該項 status 改為 done

## 明確不做
（spec/project-spec.md 原文複製）
```

---

## 2. `adapters/.cursor/rules/*.mdc`（Cursor）— 部署到 `.cursor/rules/`

Cursor 是編輯情境，不執行驗收——rules 只攜帶**約束**，
任務仍由用戶貼 goal 檔。拆成多檔利用 globs 作用域：

```
00-core.mdc        ← alwaysApply: true（專案目標+不做清單+技術棧，< 500 字）
10-server.mdc      ← globs: ["server/**"]（後端安全規則）
20-client.mdc      ← globs: ["public/**","src/client/**"]（前端/凍結事件名）
```

範例（00-core.mdc）：

```markdown
---
description: mathdefense core constraints
alwaysApply: true
---
- 技術棧固定：Phaser 3 / Socket.io / Express / Supabase。不引入其他框架。
- Socket 事件名以 spec/contracts/C1-socket-events.md 為準，禁止新增或改名。
- 禁止實作：帳號系統、跨 session 儲存、排行榜（完整清單見 CLAUDE.md「明確不做」）。
```

格式規則：每條 rule 是祈使句 bullet；單檔 < 1KB；不放驗收條件（Cursor 不會跑）。

---

## 3. `adapters/copilot-instructions.md`（GitHub Copilot）— 部署到 `.github/`

Copilot 只讀這一檔、不會追蹤連結、context 很小。
規則：**單檔 ≤ 2 頁、宣告式、零任務清單**，
把最容易被補全弄錯的事寫成「永遠/絕不」句式：

```markdown
# {project} — Copilot instructions
本專案是課堂即時多人塔防數學遊戲（Phaser 3 + Socket.io + Express + Supabase）。

永遠：
- Socket 事件名使用既有清單（room:join, unit:deploy, game:state, ...），不發明新事件
- unit:deploy 的資源/冷卻/格子檢查寫在 server 端，client 端只做 UI disabled
- 遊戲狀態只存後端記憶體 Map，以 roomCode 為 key

絕不：
- 不建立 users 表、JWT、密碼欄位（本專案無帳號系統）
- 不寫入任何跨 session 的持久化遊戲資料
- 不新增規格外功能（排行榜、成就、地圖編輯器）
```

---

## 4. `adapters/system-prompt.md`（通用 agent：GPT-4o / Codex 等）

設計成可直接整段貼入 system message（建議 ≤ 8KB），
goal 檔之後逐一以 user message 餵入。結構：

```markdown
# System Prompt — {project} 執行代理

## 角色
你是 {project} 專案的執行代理。你按 goal 檔執行，不做設計決策。

## 專案摘要
（project-spec.md 壓縮版：目標、技術棧、模組一行式、明確不做全文）

## 執行協議
1. 使用者每次給你一個 goal 檔（G*.md），它自包含一切所需
2. 依五元素順序工作：先讀驗證方式，再寫程式碼
3. 「前置裁決」區的決定照辦，不重新裁量
4. 歧義 → 輸出 BLOCKED 區塊（格式如下）並停止，不猜
5. 交付 = 自檢 footer 全綠 + 貼上驗證輸出

## BLOCKED 格式
（固定格式，同 goal 檔內定義）

## 輸出紀律
只輸出：程式碼變更、測試輸出、自檢清單、或 BLOCKED。不輸出計畫書與長篇解釋。
```
