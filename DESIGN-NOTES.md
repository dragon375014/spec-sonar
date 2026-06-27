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

## ADR-002｜交付物原型（archetype）完備性軸（2026-06-27）

**狀態：** ✅ 已實作（2026-06-27 下午）——`dark-zone-baseline.md` 加 **M0.5 archetype 分叉樁**（交易型/呈現型/混合，舊 5 型收為交易型子型）+ **類型 F 呈現型網站 baseline**（F-11 標準區塊 / F-12 可達性對稱律 / F-13 信任頁是產品 + L1/L2/L3 完備性階梯）；`goal-decomposer/SKILL.md` 步驟七加「archetype baseline 覆蓋」自檢。Audit Mode 共讀 baseline **自動受惠**。源於一條「為什麼管線產出後端 90 分、前端 10 分」的端到端診斷對話。

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

---

## ADR-004｜AskUserQuestion 接力的階段交接（2026-06-27，已實作）

**狀態：** 已實作——`idea-to-spec/SKILL.md` 步驟九 + `goal-decomposer/SKILL.md` 步驟八。

### 背景 / 問題
管線的階段交接（idea-to-spec → goal-decomposer → specmit）原本靠**使用者記得打對暗號**（「幫我分解」「跑管線」）。這有兩個問題：(1) 是人工接縫——使用者要記得每段該說什麼；(2) **測不出真正的端到端體驗**——一直手動打字，沒辦法知道「規劃好之後能不能一路按到交付」。

### 決策
每個階段**做完後主動以能力閘提議下一棒**（不是等暗號）：
- idea-to-spec 輸出 handoff → 問「要現在分解嗎？」→ 是則進 goal-decomposer。
- goal-decomposer 輸出 goal 圖 → 問「要現在跑管線嗎？」→ 是則進 specmit。
- 能力閘同 ADR-001：有 `AskUserQuestion` 走卡片、沒有退文字（公開使用者跨平台不壞）。
- 推薦選項排第一、永遠保留「先停在這」逃生口——**主動提議 ≠ 自動推進**，每段仍由人按一下。

### 為什麼是這個形狀
- **把人工接縫換成「主動問」而非「自動接」**：端到端可一路按到底，但每段拍板權還在人手上（符合「outer-loop 回人」的既有刻意人閘）。
- specmit 是末棒，跑完回報 run-report；BLOCKED / failed / resume 仍回人，不自動接。
- RequiBridge → idea-to-spec 那條交接走**私有**端（RequiBridge 私有），不在本公開 repo。

### ⚠️ 不要改回去
- **不要**把「主動提議」變成「自動推進」（跳過人的確認）——那會奪走拍板權、也會在 BLOCKED 時硬衝。
- **不要**因為某平台沒有 `AskUserQuestion` 就讓接力壞掉——能力閘退文字是正常路徑。

---

## ADR-005｜Audit Mode 安全 lens（2026-06-27，已實作；warn-only）

**狀態：** 已實作，`modes/audit-mode.md` 的「A6 安全 lens」。

### 背景 / 問題
舊案（brownfield）審查只跑暗區四態，沒掃安全。但網頁/Supabase 專案的攻擊面高度一致，且最貴的坑（RLS 鎖列不鎖欄自我提權、anon 可打無守門 SECURITY DEFINER RPC…）**Supabase advisor 與標準 lint 永遠綠燈**。需要一個可攜安全閘，但**第一版不能誤報擋住流程**。

### 決策
A6 安全 lens：archetype=網頁/Supabase 時加跑，**warn-only（只報不擋）**。
1. **ruleset 公私分離**：canonical 規則在 governance-meta `playbooks/supabase-web-security-gate.md`（公開，10 條 GOLD + commodity）；Audit Mode 只描述觸發 + GOLD 類清單 + 指向它。commodity 直接吃 Supabase advisor、不重造。
2. **能力閘讀 allowlist**（同 goal-decomposer 步驟零之二、同 ADR-001 能力非身分）：有本地 house-profile.security_context → 用 `intentional_exceptions_allowlist` 把 finding 分 **🆕 新的要看** vs **✅ 已簽接受**（附 signed_by/date/review_by，過期提示複查）；沒有 → 全列 🆕。
3. **warn-only 的意義**：第一版只報不擋；allowlist 的工作因此從「擋/放」變成「分新 vs 已決定」，人每次只看 🆕。升 fail-closed 是後續決策（業主 2026-06-27 選 warn-only）。

### 為什麼是這個形狀
- **同一條能力閘 + 公私分離法則的第四次**（ADR-001 ui_mode / ADR-003 house-profile / ADR-004 接力 / 本案）：公開定機制+ruleset，私有放 allowlist/綁定。
- **GOLD 優先**：賣點不是 advisor 已抓的 commodity，是 advisor 抓不到、要踩過才學到的那 10 條。

### ⚠️ 不要改回去
- **不要**把 commodity（advisor 已抓）重寫進來——直接吃 advisor。
- **不要**在公開 Audit Mode 寫死任何專案的表名/allowlist——那是私有 house-profile 的事。
- **不要**沒經人就把 warn 升 fail-closed——誤報擋流程比漏報更快讓人關掉整個閘。

### 參考
- 公開 ruleset：governance-meta `playbooks/supabase-web-security-gate.md`。
- 萃取來源（私有完整 20 條目錄）：消費者本地（CS `文檔/安全坑目錄_P0-P2_*`）。

---

## ADR-006｜Audit→修 接力（triage + blast-radius 閘）（2026-06-27，已實作）

**狀態：** 已實作，`modes/audit-mode.md` A7 + `goal-decomposer/SKILL.md` Audit 模式列。

### 背景 / 問題
Audit Mode（含 A6 安全 lens、archetype 完備）跑完會出一堆 finding。想把「該修的」自動接續往下 kickoff（→ goal-decomposer → specmit）。但**不能無腦自動修全部**——9453 實審證明：findings 裡很多是 **✅ 已做對**（S-01/12/16…）、或**刻意延後的 roadmap**（line-pay 模組四、entitlement 模組五是 501/mock，是路線圖不是 bug）、或**刻意 allowlist**（fn_available_slots 對 anon）。全自動修會：動壞已對的、提前蓋延後的功能、「修」掉故意的。

### 決策
**照出 → triage → 人選 → 才 kickoff**（不是自動修全部）：
1. **triage（三桶）**：fix-now（真要修）/ roadmap（刻意延後功能，不自動建）/ intentional（✅或 allowlist，跳過）。只有 fix-now 進 kickoff。
2. **blast-radius（fix-now 內再分）**：low（UI/內容→可一路跑）/ high（安全·RLS·GRANT·金流→ goal 寫「執行前人看 SQL 才 apply」+ opus tier，executor 走 BLOCKED 回人，**不自動 apply**）。
3. **kickoff offer（能力閘，同 ADR-004）**：Audit 完 → AskUserQuestion「fix-now 候選有 N 條，要修哪幾個？」多選（roadmap/✅ 不列）→ 選的寫 remediation-goals → goal-decomposer（Audit）→ specmit。
4. remediation-goals.md stub += `triage` / `blast_radius` 兩欄。

### 為什麼是這個形狀
- **自動的是流程，不是判斷**：照出/分類/提議/分解/跑 自動；修哪些、危險的要不要 apply＝人拍板。安全/DB 改動永遠多一道人關。
- **同一條法則第五次**（能力閘 + 主動提議≠自動推進）：ADR-001/003/004/005/本案。warn-only（ADR-005）+ 本接力 = 只看 🆕 fix-now、選了才動、high blast-radius 還會停下給人看 SQL。

### ⚠️ 不要改回去
- **不要**把 roadmap/intentional 也丟進 kickoff——會提前蓋延後功能、改壞已對的。
- **不要**讓 high blast-radius 的安全/RLS goal 自動 apply——必須 BLOCKED 回人審 SQL。
- **不要**把「主動提議修」變「自動修」——奪走拍板權、且誤改安全比漏報更慘。

### 參考
- 觸發鏈：Audit Mode A6/A7 → goal-decomposer（Audit）→ specmit（ADR-004 接力）。
- 驗證靶：9453americantimetest（安全幾乎全 ✅、L3 媒體與 Cookie 是 fix-now；line-pay/entitlement 是 roadmap，正好示範三桶）。

---

## ADR-007｜確定性階段交接 hook（2026-06-27，已實作於 specmit）

**狀態：** 已實作，specmit `hooks/pipeline-stage-notifier.mjs` + `bin/pipeline.js` 的 `mergeHookSettings`（init 自動裝）。

### 背景 / 問題
ADR-004/006 的階段 offer 是 prompt **軟觸發**——多數會問、偶爾忘。要不要硬化到確定性？評估光譜後：要，但**用 hook，不用「程式層強迫 tool call」**。

### 決策
PostToolUse(Write) hook：偵測管線產物檔（`STATE_FINAL.json` / `goal-graph.json` / `remediation-goals.md`）剛被 Write → 注入 `additionalContext` 提醒模型主動 offer 下一棒。
- **確定性的是「提醒注入」，不是「tool call 強迫」**：hook 在產物出現的當下**一定**注入，模型極大機率照做 offer。真正 100% 強迫 tool call 要程式層攔截輸出（spec-kit build-time 那種）——那才犧牲可攜，**刻意不做**。
- **能力閘加法層（同 ADR-001）**：hook **只在 Claude Code 有效**；skill 的軟 offer **留著**當其他平台（Codex/Manus/裸 LLM）後援 → 可攜性不掉。hook 是 additive hardening，不是 replacement。
- **注入提醒 ≠ 自動推進**：注入文字叫模型「主動問人」，人仍拍板。
- **偵測「產物檔 Write」而非「每次 Stop」** → 不會在對話中途亂跳。

### 為什麼是這個形狀（確定性 vs 可攜的光譜）
| 強度 | 機制 | 可攜代價 |
|---|---|---|
| 軟 offer | skill prompt | 無（但偶漏） |
| **確定性提醒** | **hook（本案）** | **無**（加法層、Claude Code only、軟 offer 後援） |
| 100% 強迫 tool call | 程式層攔截（spec-kit build-time） | 有（不可攜） |

停在 **hook 那格**：人類關卡只需要「確定性提醒」，不需要「強迫」；為了 100% 去犧牲可攜不划算。

### ⚠️ 不要改回去
- **不要**把軟 offer 從 skill 拿掉——那是其他平台的後援，拿掉就不可攜。
- **不要**把 hook 改成「自動執行下一棒」（跳過人）——它只該**注入提醒**。
- **不要**為了 100% 上「程式層強迫 tool call」——不值得犧牲可攜。

### 參考
- 實作：specmit `hooks/pipeline-stage-notifier.mjs`（PR #4）。
- prior-art：GitHub spec-kit 走 build-time 強迫（付可攜代價）；本案走 hook（加法、不犧牲）——同 ADR-001 對 spec-kit 的取捨。

---

## ADR-008｜brownfield「補全」入口 skill（2026-06-27，已實作）

**狀態：** 已實作——`skills/audit-existing-project/SKILL.md`（薄編排層）+ specmit `bin/pipeline.js` 安裝清單加三個檔。消掉 ECOSYSTEM 標的 `connector-needed`。

### 背景 / 問題
ADR-002（archetype 完備性軸）/ ADR-005（安全 lens）/ ADR-006（audit→修 接力）把 brownfield 體檢的**器官**都長齊了，但**沒有可自動觸發的前門**。具體兩個缺口（ECOSYSTEM `connector-needed` 記的）：
1. **沒有 skill description 命中「補全 / 體檢 / audit 這個既有專案」**——使用者裝完 `specmit init` 說「請幫我自動補全」，沒有任何 skill 的 description 會匹配，Audit Mode 不會被想起來。
2. **`modes/audit-mode.md` 不在安裝清單**——就算想起來，裝好的專案裡也沒有那份作業手冊（只有 idea-to-spec / goal-decomposer / specmit 三支進了 `~/.claude/skills/`）。

結果：brownfield 流程**只能靠 agent 直接去 spec-sonar repo 讀 Audit Mode** 才走得到——等於沒接通。from-zero（「我想做一個…」命中 idea-to-spec）是通的，brownfield 不是。

### 決策
補一支**薄入口 skill** + 把作業手冊一起裝進去：
1. **`skills/audit-existing-project/SKILL.md`**：description 命中「補全 / 體檢 / 健檢 / audit 既有專案 / 缺什麼 / 有頁沒入口」+「裝完 init 說補全」。讓位規則寫清楚：from-zero → idea-to-spec、單任務 → goal、單 bug → 直接修。**body 是純編排**：偵測能力（AskUserQuestion / project-scanner / house-profile）→ 跑 Audit Mode（暗區四態 + archetype 完備性 + A6 安全 lens）→ A7 triage → AskUserQuestion 問修哪幾個 → 寫 remediation-goals → 接 goal-decomposer（Audit 模式）。
2. **薄 = 不重寫判準**：skill **讀** `references/audit-mode.md`（= `modes/audit-mode.md` 安裝後位置）+ `../idea-to-spec/references/dark-zone-baseline.md`（sibling 已裝），**不在 skill 內複製** 四態 / baseline / GOLD 清單 / triage 規則——避免第二真相源漂移（同 ADR-002「specmit 不另寫掃描器」的 D2 防雙真相源）。
3. **specmit 安裝清單（`bin/pipeline.js`）GLOBAL 加三個檔**：`audit-existing-project/SKILL.md`、`modes/audit-mode.md → references/audit-mode.md`、`tools/project-scanner.py → references/project-scanner.py`。dark-zone-baseline 已由 idea-to-spec 那組裝進來，skill 跨 sibling 引用、不重裝。
4. **specmit 薄 CLI 動詞 `complete`（選配）**：補裝 brownfield 三檔 + 印「開新對話說『幫我補全這個專案』」的下一步指引——CLI affordance，給「裝完不知道怎麼啟動」的人一個按鈕（同 bot 可發現性：能力別藏成隱形指令）。

### 為什麼是這個形狀（關鍵）
- **入口 skill 是觸發層，不是邏輯層**：Anthropic harness 靠 skill description 自動匹配；ADR-002/005/006 的邏輯都在 `modes/audit-mode.md`（mode 文件、不是 skill、不會被 description 匹配）。所以缺的恰好是「一支 description 對得上 brownfield 意圖、body 只負責把那份 mode 文件叫出來跑」的薄殼。
- **與 idea-to-spec 對稱**：idea-to-spec 是 from-zero 的觸發前門（description 命中「我想做一個…」）；audit-existing-project 是 brownfield 的觸發前門（命中「補全既有專案」）。兩者共讀同一份 dark-zone-baseline，所以 archetype 完備性軸對兩條路同時生效（ADR-002 §1「一處修、兩模式亮」的觸發側落實）。
- **裝手冊進 references 是 deployment、不是 fork**：canonical 仍是 `modes/audit-mode.md` / `tools/project-scanner.py`；安裝清單把它們抓到 `~/.claude/skills/audit-existing-project/references/` 是部署副本（同「canonical home / installed copies are deployments」既有模型）。`specmit sync` 會更新。

### 影響面
- spec-sonar：新增 `skills/audit-existing-project/SKILL.md`（純加法，不動既有 skill / mode）。
- specmit：`bin/pipeline.js` GLOBAL 清單 +3 行、新增 `complete` 動詞、版本 0.4.1 → 0.4.2；`ECOSYSTEM.md` 移除 `connector-needed` 警告 + 路由表「complete an existing project」改指本 skill。

### ⚠️ 不要改回去
- **不要**把判準（四態 / archetype baseline / 安全 GOLD / triage）抄進 skill body——薄殼的價值就是不持有判準，抄進來就會跟 mode 文件漂移。
- **不要**讓 audit-existing-project 接 from-zero 的新想法——那是 idea-to-spec 的領域，description 的讓位規則就是為了不搶。
- **不要**因為「skill 已裝」就不裝 `audit-mode.md` / `project-scanner.py`——少任一個，裝好的專案裡 skill 叫不出手冊，等於回到 connector-needed。

### 參考
- 觸發鏈：`audit-existing-project`（本案）→ Audit Mode A0–A7（ADR-002/005/006）→ goal-decomposer（Audit）→ specmit（ADR-004 接力）。
- ECOSYSTEM 路由：「complete an existing project」/「security-scan a Supabase/web project」。
- 缺口來源：specmit `ECOSYSTEM.md` 舊版「Known follow-up (`connector-needed`)」段。
