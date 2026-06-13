# DESIGN-NOTES — spec-sonar 設計決策記錄（ADR）

本檔記錄 spec-sonar 工具鏈的重大設計決策與其**「為什麼」**。
目的：防止日後（人或自動同步 session）忘了來龍去脈，**把刻意的設計當成 bug 改回去**。
新決策往下追加，不刪舊的。

---

## ADR-001｜idea-to-spec 提問通道：capability-gated `ui_mode`（2026-06-13）

**狀態：** 已採用，實作於 [`skills/idea-to-spec/SKILL.md`](skills/idea-to-spec/SKILL.md)「步驟零 + 提問呈現規則 + rich 模式強制觸發協議」。

### 背景 / 問題
idea-to-spec 原本每輪以**純文字 Markdown** 提問（A/B/C/D），並在回覆尾端輸出 `<STATE>` 區塊作為**跨輪記憶**。在 Claude Code 這種富互動介面裡造成兩個體感問題：

1. `<STATE>` 整坨攤在用戶面前 —— 它是機器記憶、不是給人看的，但 skill 沒有任何隱藏機制。
2. 選項型問題用純文字，沒用上 Claude Code 原生的 `AskUserQuestion` 卡片 UI。

但 idea-to-spec 是**刻意 model-agnostic**：要能在 Codex / Manus / 純文字 LLM 上跑。`AskUserQuestion` 是 Claude Code 專屬工具，**不能寫死**。

### 決策
新增「步驟零：輸出通道偵測」，以**能力（capability）**而非**身分（identity）**決定呈現：

- 偵測「當前工具清單裡有沒有 `AskUserQuestion` 類結構化提問工具」→ `ui_mode = "rich"`；沒有 → `"text"`。
- `rich`：選項型問題走 `AskUserQuestion`（卡片）；`<STATE>` 仍以文字附在工具呼叫前（跨輪記憶必須留在 transcript）。
- `text`：維持原純 Markdown 格式。
- **開放式問題**（要自由描述，如第 1 輪意圖擷取）即使 rich 也維持文字，不硬塞成選擇題。
- 兩通道的問題內容 / 選項 / 後果 / STATE 必須一致，只差外觀。

### 為什麼是「能力」不是「身分」（關鍵）
同一個 Claude 模型在 **claude.ai 網頁 / Cursor / API 裸跑**時都**沒有** `AskUserQuestion`。若用「我是不是 Claude」判斷，會在這些環境呼叫一個不存在的工具而失敗。偵測「工具在不在」才正確，且天生跨平台優雅降級：任何平台只要提供同義工具就自動吃到富 UI，沒有就回退文字。

### 與 GitHub spec-kit #2181 的對照
spec-kit（GitHub 的 spec-driven 開發工具，與本專案近親）在 issue #2181 / PR #2191 做了**同一件事**：把編號選項 Markdown 換成原生 `AskUserQuestion`，**只對 Claude Code、其他 agent 維持 Markdown**；用結構化 `{label, description}`、推薦項排第一、保留自由輸入逃生口、保留所有問答上限。**我們的 `ui_mode` 與其設計意圖一致。**

關鍵差異：

| | spec-kit #2181 | 本專案 `ui_mode` |
|---|---|---|
| 何時決定 | **生成時（build-time）**：程式（`ClaudeIntegration` class）後處理產生的 skill，**程式自己構造** `AskUserQuestion` payload | **執行時（runtime）**：SKILL.md prompt 指示模型自行偵測並呼叫 |
| 確定性 | 高（程式強制，每次都觸發） | 軟（模型每輪自行決定；prompt 無法強制 tool call） |
| 可攜性 | 需要 build pipeline | 單檔 prompt，零前置 |

### 為什麼**不**採 spec-kit 的 build-time 手法
1. **架構不符**：spec-kit 有一條把模板生成成 skill 的 build pipeline，所以有「後處理」的插點。idea-to-spec **是手寫 prompt，SKILL.md 就是成品，沒有任何生成步驟**，沒有那層可插。
2. **prompt 本質上強制不了 tool call**：在 Claude Code 裡 SKILL.md 只能「指示」模型；要不要呼叫 `AskUserQuestion` 是推論時的模型決定。要達到 spec-kit 的強制，必須在**程式層攔截改寫模型輸出** —— skill 沒有這層。
3. **代價不划算**：照搬就得把 idea-to-spec 重構成「程式生成 + 後處理」pipeline，丟掉單檔手寫、跨平台直接可讀的最大優點，只換來把「軟觸發」變「硬觸發」。而在 Claude Code 內，軟觸發退回文字本來就**無害**（文字格式就是可攜後援）。

**結論：借 spec-kit 的「意圖」（已寫進 rich 模式強制觸發協議），不照它的「手法」。**

### 後果與已知上限
- `rich` 命中率提高但**非 100%**：(a) 模型在重工具回合可能仍退文字；(b) `AskUserQuestion` 本身有 harness bug —— 在 plugin 載入的 skill 內呼叫會回空（anthropics/claude-code #29547、#29733）、無 TTY（Agent SDK / headless）渲染不出、`"*"` 權限可能被自動跳過、某些情況要先 toggle plan mode（#9846）。協議裡的**逃生口**就是為這些 bug 留的：工具失效 → 退文字、不卡關。
- `<STATE>` 在 rich 下仍會出現在 transcript（收進程式碼框），因為它是跨輪記憶的載體，**不可移除**。若要徹底隱藏需改成寫檔記憶，屬另一個更大的變更，目前不做。

### ⚠️ 不要改回去
- **不要**因為「看到 `<STATE>` 攤出來」就刪掉 STATE 輸出 —— 那會砍掉跨輪記憶，下一輪會重問已答過的問題。
- **不要**把 `ui_mode` 判斷改成「偵測是不是 Claude」 —— 會在無 `AskUserQuestion` 的 Claude 環境壞掉。
- **不要**因為「rich 偶爾退文字」就以為壞了 —— 那是設計內的軟行為 + 已知 harness bug，逃生口刻意如此。

### 參考
- GitHub spec-kit #2181（提案）/ PR #2191（已合併）：https://github.com/github/spec-kit/issues/2181
- anthropics/claude-code #29547、#29733、#9846、#9912（AskUserQuestion 可靠性）
- 安裝來源：`npx specmit init` 從各公開 repo 的 **`main`** 分支抓檔（installer `bin/pipeline.js`）。
