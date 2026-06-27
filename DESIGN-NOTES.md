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

---

## ADR-002｜交付物原型（archetype）完備性軸（2026-06-27，提案）

**狀態：** 提案（design proposal），尚未實作。源於一條「為什麼管線產出後端 90 分、前端 10 分」的端到端診斷對話。

### 背景 / 問題
實測：把一個 idea 跑過 RequiBridge → idea-to-spec → goal-decomposer → 執行，**跟後端/DB 相關的部分都很順，前端 UI/UX 只有 10 分**。例：做品牌官網，產出 header 只有 2 個選項、沒有「關於我」、有後台卻沒入口可達。

逐站追蹤發現**管線並不缺前端器官**（用戶旅程維度、兩段邊界掃描、導航表、接線矩陣、G0、G-FINAL 都在）。真正的洞是三層：

- **R1 原型缺口（最根本）**：`dark-zone-baseline.md` 的 5 個類型包（Marketplace/SaaS/消費型/內部工具/ERP）**全是「應用/系統」原型**，**沒有「品牌/內容/呈現型網站」這一類**；11 通用維度幾乎全是後端形狀，唯一碰畫面的「用戶旅程」框成任務漏斗，**沒有 IA/標準區塊/導覽廣度維度**。
- **R2 完備性是相對的**：導航表/接線矩陣/旅程覆蓋只驗「**已宣告的都到得了**」，不驗「**該有的有沒有**」——沒有一站立 baseline。Garbage-in → verified-garbage-out。
- **R3 機械驗收偏置**：可機械驗的後端被 scorecard 棘輪推高；前端完備性/IA 不可機械驗 → 沒東西可釘 → 墊底。

**Audit Mode 有同一個盲區**：它與 idea-to-spec 共讀 `dark-zone-baseline`（見 `modes/audit-mode.md`），所以掃 90/10 網站會回報「沒問題」——它看不到「缺關於我頁」，因為沒有維度期待一個關於我頁。

### 決策（提案）
補一條**交付物原型（archetype）完備性軸**，每個原型自帶「適合它那種表面」的 baseline。**不是把官網版型硬塞進管線**——網頁只是眾原型之一（純 API → DX baseline、自動化 → 執行面、bot → 對話流、列印 → 排版），所以「不能只用網頁當標準」靠設計滿足、非例外。

1. **落點 = `dark-zone-baseline.md`（一處修、兩模式亮）**：from-zero（idea-to-spec 步驟三）與 brownfield（Audit Mode A2）共讀此檔，故 archetype 軸加此處則兩路同時長眼。
2. **兩層結構**：第一層 M0 modality（已存在，列印在這層）；第二層 archetype 只長在「螢幕」下 = **交易型應用 / 呈現型網站 / 混合**。既有 5 類型包收進「交易型應用」當子類（純加法）。
3. **判定 = infer-first + 一行確認**：archetype 從 solution_map/前幾輪答案/project-scanner 掃碼**推定**（痛點類別 ≠ archetype，是不同軸），再以 B 類推定句一行確認（猜錯=上線才爆，性質同 M0）。粗類別在 client-facing 端（RequiBridge）即可，深挖子類交執行端。
4. **呈現型 baseline**：①標準區塊（首頁/關於我/商品服務/內容/聯絡 + 頁尾法務）②可達性對稱律（凡宣告存在的面都要有可抵達入口，含後台）③信任頁是產品不是裝飾。
5. **三層完備性階梯**：L1 存在 / L2 可達 / **L3 充實**——一個面需要圖/影，就必須同時有**媒體槽**（頁面內圖片/影片區塊）+ **後台填料路徑**（上傳/選圖/儲存）；生成成「一坨文字、沒圖槽、後台無放圖的路」= 不完整。L3 機械可驗（grep 媒體區塊 + admin route），順手修 R3。**L3 的檢查是「填得進去嗎」三問**（2026-06-27 dogfood 9453americantimetest 修正——只問「有沒有槽」會放過空殼）：(a) 有媒體槽？(b) 有**真**的填料路徑（非 mock 的上傳+儲存+picker）？(c) 槽**實際填了**沒（非全 null）？只過 (a) = 結構齊全、料全空的空殼（9453 實證：有 `PhotoFrame` 槽 + `image_key` 欄 + admin 圖片輸入，但上傳是 mock / r2-sign 501 stub、`image_key` 全 null → 整站空殼 = 它的「前端 10 分」）。
6. **補全模式（brownfield）= 復用 `tools/project-scanner.py` + Audit Mode**（拿 archetype baseline 當尺差集照出缺/薄的面），specmit 僅加薄編排動詞，**不另造掃描器**（防 D2 雙真相源）。掃描照出「哪些不完整」、人排序「先補哪個」。
7. **下游強制**：goal-decomposer 步驟七自檢加一條「archetype baseline 覆蓋」——每個 baseline 區塊（含 L3 媒體槽+後台路徑）要嘛有 owner goal、要嘛在「明確不做」顯式列出。

### 為什麼是這個形狀（關鍵）
- **M0 modality 是先例**：它把「靜默假設螢幕」變成「顯式分叉 + 已知缺口」。archetype 是它的姊妹樁——把「靜默假設此案是交易型應用」變成顯式選擇。
- **同一個結構盲區的第三次出現**（作者自身體系）：Rule 34 反向器官（補往後退）、設計地基模板（補美感軸）、本案（補 IA/媒體完備性軸）——體系對「可機械驗的對」長滿器官、對「完整與否」缺器官。

### 影響面
- spec-sonar：`dark-zone-baseline.md`（archetype 軸 + 呈現型 baseline + L1/L2/L3）、`goal-decomposer/SKILL.md`（步驟七一條自檢）；Audit Mode 共讀 baseline **自動受惠**。
- RequiBridge：planner/solution_map 多一個 archetype tag 進 spec-seed。
- specmit：`bin/` 加薄「補全」動詞。

### ⚠️ 不要改回去
- **不要**把既有 5 類型包當「全部原型」——它們只是「交易型應用」的子類；漏掉呈現型/混合是本 bug 根因。
- **不要**在 specmit 內另寫掃描器——掃描器是 project-scanner + Audit Mode，specmit 只編排。
- **不要**把「導航表/旅程覆蓋通過」當「前端完整」——它們驗的是相對於已宣告 scope 的一致性，不是相對於 archetype baseline 的完備性。

### 參考
- N=1 dogfood 目標：真實 90/10 網站碼 `9453americantimetest`。
- 完整診斷（逐站 10 掉點 + 設計來回）：CS 專案 `文檔/自動化服務飛輪規劃/管線_archetype完備性軸_診斷與修法設計_2026-06-27.md`。

---

## ADR-003｜house-profile 能力閘注入（2026-06-27，已實作於 goal-decomposer）

**狀態：** 已實作，goal-decomposer SKILL.md「步驟零之二 + 契約檔 house-default 規則 + 自檢一條」。ADR-002 §5 的 L3「處理契約」的**值**從這層來。

### 背景 / 問題
ADR-002 把 L3 升成「填得進去嗎」三問，但留了一個遞迴的洞：粗設計項（「L3 填料路徑」）底下藏一叢細決定（格式 / 尺寸 / 上限 / 裁切 / 離線 / 配額），**靠記性會漏**（實例：8MB 圖直存塞爆 storage = L3 子盲區）。這些細節**因執行者而異、且不該每次重問**——它們是「我這樣做開發」的慣例（house-default），不是公開使用者要的東西。需要一個機制：公開管線能拉執行者私有的慣例知識，但不外洩、不打擾公開使用者。

診斷證據（2026-06-27 對 CS 專案跑唯讀 git 挖掘）：CS 已隱性編碼 **≥7 條跨領域 house-default**（new-db-table RLS+GRANT / payment-callback / manual-trigger / pg-overload-DROP / cross-layer-contract / frontend-no-overwrite-DB-SSOT / migration-apply-lock），全部散在散文 CLAUDE.md / 專案綁定 BLOCKER / prose GOTCHAS 三種**不可注入**形態 = N≥2，值得建。

### 決策
**公開定插槽、私有放值**：
1. **機制（公開 goal-decomposer）**：步驟零之二「house-profile 能力閘」——偵測「有沒有」（不是「是不是」，同 ADR-001）。讀順序 ① `./.reuse/house-profile.json`（專案覆寫）② `$HOUSE_PROFILE`（執行者全域）③ 都沒有 → 中性預設、跳過、照常跑（公開使用者走這條）。
2. **值（私有，不在本 repo）**：house-profile.json = `house_defaults[]`（每條 category / default / `emits_requirement` 路由鍵，同 reuse-manifest）+ `sharp_edges[]`（粗項藏的貴 cluster + 該問的 `ask`）。
3. **套用**：命中 `emits_requirement` 的 goal → 把 default **烤成具體值**寫進契約 / 前置裁決；命中的 `sharp_edges` → 用 `ask` 補裁決。L3 媒體項的「處理契約」就是 `media-upload` default（格式/最長邊/上限/裁切）。

### 為什麼是這個形狀（關鍵）
- **能力非身分（同 ADR-001）+ 檔案鬆耦合（同 PIPELINE-CONTRACT）**：house-profile 只是另一個可選輸入檔，有就讀、沒有優雅降級。這是本生態系第三次用同一條 loose-coupling 法則。
- **防洩邊界**：公開 skill **永不出現 house-profile 來源 repo 的名字**（只認抽象插槽）；house-profile 是本地輸入、執行時讀；生成的 goal 把值烤成具體數字（self-contained）；私有 profile 永不 commit 進公開產物。讀本地、不發佈私有。

### ⚠️ 不要改回去
- **不要**在公開 skill 寫死任何 house-profile 來源 repo 名 / 具體 default 值——那會把私有慣例洩進公開 repo，且綁死單一使用者。
- **不要**讓「沒有 house-profile」變成報錯——公開使用者沒有它是正常路徑，必須優雅降級。

### 參考
- 值的家：執行者私有 reuse-hub（公開 repo 不需知道，故此處不展開）。
- 完整討論（worth-it 診斷 + 公私分割）：CS 專案 `文檔/自動化服務飛輪規劃/管線完備性工作流_線索分類與狀態_2026-06-27.md` §D/§F。
