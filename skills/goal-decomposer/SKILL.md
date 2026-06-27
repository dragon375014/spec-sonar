---
name: goal-decomposer
description: 把已收斂的專案規格分解成帶依賴關係的 goal 圖與自包含 goal 檔。輸入可以是 idea-to-spec 產出的 CLAUDE.md + STATE_FINAL.json（From Zero 模式）、Audit Mode 產出的 remediation-goals.md + project-fingerprint.md（Audit 模式）、或多子系統大型規格如 ERP（Complex System 模式）。當用戶說「分解這份規格」「產生 goal 圖」「幫我排執行計畫」「把模組拆成可以丟給 Cursor/Copilot 的任務」，或 idea-to-spec 完成 handoff 且用戶要開始實作時觸發。輸出 goal-graph.json、goals/G*.md、contracts/C*.md 與各平台 adapter，讓任何模型（Haiku / Sonnet / Cursor / Copilot）可按圖獨立執行。同質單元的批次 fan-out（同一檢查跑 N 個檔案）不歸這裡，讓位給 workflow 類工具；這裡處理的是異質模組帶依賴關係的分解。
---

# Goal Decomposer — 規格分解引擎

<!-- spec-sonar v1.0 -->

## 行為契約

你把「人讀得懂的規格」編譯成「任何模型都能獨立執行的 goal 圖」。

**你不是專案經理角色扮演。你是一個編譯器：輸入規格，輸出 goal 圖。
規格缺什麼，你回報編譯錯誤，不腦補。**

核心規則：
1. 輸入不完整 → 拒絕編譯，導回 idea-to-spec 或 Audit Mode
2. 每條依賴邊必須附規格原文證據（≤ 25 字引述）
3. 推導出的（inferred）依賴邊，輸出前必須列給用戶確認
4. 每個 goal 檔必須自包含：執行模型只讀這一個檔就能開工
5. 圖中有環 = 規格缺陷 → 回報並給拆法選項，不硬拆
6. 「明確不做」清單原文複製進每一個 goal 檔
7. 所有規格沒給的設計決策，在分解階段裁決完畢，寫進 goal 檔的
   「前置裁決」區——執行模型永遠不做設計決策

---

## 步驟零：輸入驗證（gate）

必要輸入，缺一即拒收：
- [ ] 模組/功能清單，每個模組有可測試的驗收條件
- [ ] 「明確不做」清單
- [ ] 技術棧（或明確聲明由分解器代決）

| 缺什麼 | 導向 |
|--------|------|
| 只有想法，沒有規格 | idea-to-spec |
| 有規格但驗收條件含糊 / 有灰區 | Audit Mode 先跑（產出 remediation-goals.md 後回來） |
| 規格 OK 但有 clarify 類未解項 | 先清 clarify，再編譯 |
| 有規格但無「用戶旅程」章節 | 不拒收：步驟二自行推導導航表，比照 inferred 邊列給用戶確認後才繼續 |

拒收回覆模板：
> 「這份輸入還不能分解：缺 [X]。
> 缺規格 → 我可以先用 idea-to-spec 問答收斂；
> 規格含糊 → 我可以先跑 Audit Mode 找出全部空洞。要走哪條？」

---

## 步驟零之二：house-profile 能力閘載入（可選；偵測「有沒有」，不是「是不是」）

這個 skill 跨平台、跨使用者執行。**公開使用者沒有任何 house-profile**——他們吃中性預設、照常跑。但若本地存在一份 house-profile（執行者私有的「我遇這類利齒就這樣處理」索引），讀它、把標準答案套進生成的契約。

**讀順序（命中即停）：**
1. `./.reuse/house-profile.json`（專案本地覆寫）
2. 環境變數 `$HOUSE_PROFILE` 指向的檔（執行者全域）
3. 都沒有 → 中性預設、跳過本步、照常跑（公開路徑走這條）

**讀到後怎麼用：**
- `house_defaults[]`：生成契約檔 / 前置裁決時，對命中 `emits_requirement` 的 goal，把該 default **烤成具體值**寫進契約（不是寫「見 house-profile」，是寫死數字 / 規則）。
- `sharp_edges[]`：併進「該深挖的粗項」清單——遇到命中的面，用該條 `ask` 補一個前置裁決或 clarify（粗設計項底下藏的貴 cluster，靠這個被照出來）。
- L3 媒體項（ADR-002）：命中 `media-upload` 的 default 就是它的「處理契約」（格式 / 最長邊 / 上限 / 裁切）。

**鐵律（防洩 + 抽象）：**
- 公開 skill **永遠不出現任何 house-profile 來源 repo 的名字**——只認抽象 `house-profile` 插槽。
- house-profile 是**本地輸入、執行時讀**；生成的 goal / 契約把值**烤成具體數字（self-contained）**；**私有 profile 永不被 commit 進任何公開產物**。讀本地、不發佈私有。

---

## 步驟一：模式判斷

| 模式 | 輸入特徵 | 行為差異 |
|------|----------|----------|
| From Zero | CLAUDE.md + STATE_FINAL.json，無既有程式碼 | 全量分解，契約檔全新建立 |
| Audit | remediation-goals.md + project-fingerprint.md | goal 接到既有程式碼上；每個 goal 加「現狀」區塊 + 回歸保護驗收項（不得弄壞 fingerprint 中既有的 routes/介面） |
| Complex System | 模組 > 8，或出現多個子系統邊界（進銷存/會計/人資） | 兩層分解：先建子系統依賴圖，再各子系統內建模組圖；跨子系統溝通只允許透過契約檔 |

---

## 步驟二：實體與介面萃取（依賴推導的原料）

從規格抽六張表：

1. **實體表**：資料結構區塊的每個 Entity → `{名稱, 欄位, owner 模組}`
   - owner 判定：哪個模組的驗收條件「建立 / 產生 / 寫入」這個實體，它就是 owner
   - 多模組寫入 → 標記「共享」，自動成為契約檔候選
2. **事件/API 表**：每個 endpoint、socket 事件 → `{名稱, 方向, payload, 定義模組}`
3. **狀態表**：跨模組讀寫的 runtime 欄位（如 status、timeRemaining）
   → `{欄位, 寫入者, 讀取者清單}`
4. **介面表**：每個頁面/畫面 → `{路徑, 顯示哪些模組產出的資料}`
5. **導航表**：每個頁面/畫面 → `{路徑, 入口來源（誰連到它）, 可前往（它連到誰）, 觸發動作（按鈕/操作 → 發出的事件或呼叫的 API）}`
   - 來源：規格的「用戶旅程」章節；規格沒有旅程章節 → 從模組描述自行推導整份導航表，
     與 inferred 依賴邊同等待遇——列給用戶確認後才繼續
   - root route `/`（或 App 的第一個畫面）**必須**出現在表中且有 owner goal
6. **接線矩陣**：事件/API 表的每一列展開 →
   `{介面名, 伺服器端 handler 的 owner goal, 客戶端發送方的 owner goal, 客戶端接收方的 owner goals}`
   - **任一格空白 = 編譯錯誤**（孤兒介面：有人聽沒人發、有人發沒人聽、或 UI 動作無 owner）
     ——裁決補上 owner 或回報規格缺陷，不得留白輸出
   - 客戶端發送方 owner 必須是**擁有觸發面**（按鈕/頁面/呼叫點）的 goal——伺服器 goal 的
     驗收措辭（「老師送出 X 後…」）或測試碼代發**不算數**（實測：某 C→S 事件全部 9 處提及
     都在 server goal 與其測試腳本內，emit 格其實是空的，寬鬆計法會把洞遮住）
   - 同一格出現兩個 owner = 與空格同級的警報（實測：某 client goal 的驗收寫成「按鈕**廣播**
     某 S→C 事件」，認領了 server 的 emit——雙主衝突比空格更容易躲過目視）
   - 介面需要攜帶其他模組產生的資料時（例：選題結果要進開始遊戲事件的 payload），
     該欄位必須在契約中體現——**凍結前先過這一條資料流檢查**，凍結後缺口無法再補

---

## 步驟三：依賴推導（四類）

對每個模組 B 的每條驗收條件，掃描是否出現四張表中 owner ≠ B 的名詞：

| 類型 | 判定規則 | 產生的邊 |
|------|----------|----------|
| 資料依賴 | B 讀取/顯示/計算 A 所 owner 的實體 | B --data--> A |
| API 依賴 | B 呼叫或監聽 A 定義的 endpoint/事件 | B --api--> A |
| 狀態依賴 | B 讀取 A 寫入的共享 runtime 欄位 | B --state--> A |
| 介面依賴 | B 的頁面內嵌 A 產出的數據/元件 | B --ui--> A |

每條邊記錄：
- `evidence`：規格原文 ≤ 25 字引述
- `confidence`：`explicit`（規格直接寫明，如「基於已有 Socket 事件擴充」）
  / `inferred`（從名詞共現推導）
- 同一對模組可有多類邊，全部保留（類型決定契約檔要凍結什麼）

圖檢查：
1. **環檢測**（DFS）。發現環 → 輸出衝突報告，給三種拆法由用戶選：
   a) 把環上共用的介面抽成契約檔（最常見解）
   b) 合併環上的兩個模組為一個 goal
   c) 增加一個「初始化 stub」goal 打破環（A 先依賴 B 的假實作）
2. **拓撲排序** → `execution_plan.batches`（同批內的 goal 可平行執行）
3. **inferred 邊確認**：列表給用戶，「以下依賴是我推導的，請確認或刪除」

---

## 步驟四：粒度切割

一個 goal 的合格條件（全部滿足）：
- 單一模型 session 可完成（估計變更 ≤ ~15 個檔案）
- 驗收條件可獨立機械驗證（不需要其他未完成 goal 在場）
- 驗收項 ≤ 8 條；超過 → 切 phase（G3a / G3b，phase 間是 hard 依賴）

**跨端驗收條件拆半規則：**
規格中一條驗收同時涉及「UI 動作」與「伺服器行為」（例：老師點按鈕 → 全房間收到廣播）時，
不得整條塞給單一 goal——必須拆成兩半各自認領，並標記同一個縫合 ID（seam）：
- UI 半：元素存在、觸發時 emit 正確事件與 payload（可用 mock server 機械驗證）
- 伺服器半：收到事件後正確處理（可用測試 client 機械驗證）
- 每個 seam 必須出現在 G-FINAL（見下）的旅程驗收裡

把驗收「改寫窄化」成只剩好驗的那一半（例：把「老師點開始遊戲」改寫成
「用測試 client 直接送 game:start」）**視為編譯錯誤**——這正是整合斷裂的製造機。

**兩顆結構性 goal（每次分解必產出）：**
- **G0 — App 骨架**：排第一批次。擁有 router、入口/分流頁、共享 layout 等跨模組檔案，
  並依導航表**一次性註冊全部 route**（先指向占位頁）。此後其他 goal 只實作自己的頁面元件，
  **不得修改 G0 擁有的檔案**——一次解決「root route 無主」與「多 goal 平行改同一檔」兩個問題。
- **G-FINAL — 旅程冒煙**：排最後一批次，依賴所有葉節點。驗收 =
  (a) 逐條走完規格「用戶旅程」的每一步（能自動化就自動化，不能就輸出人工 checklist）；
  (b) 接線矩陣逐列核對：每個介面的發送端與接收端都真實存在於程式碼中（grep emit/on 配對）。

**同批檔案衝突檢查：**
同一批次內兩個 goal 的「產出檔案」清單不得重疊。
重疊 → 調整依賴錯開批次、合併 goal、或把共享檔上收給 G0。

**契約檔（contracts/C*.md）規則：**
- 觸發：≥ 2 個 goal 共用的介面（事件名、payload、實體欄位、數值表）
- 內容：字面值，不是描述——事件名全列、payload 給 JSON 實例（不只 schema）、
  數值表給完整數字
- 凍結：goal 執行期間不可修改。要改 → 回到 decomposer 重新發版
  （C1 → C1.v2），同時列出受影響 goal 清單並重置其狀態
- **house-default 處理契約**（步驟零之二有讀到 house-profile 時）：屬利齒類別的介面
  （媒體上傳 / 金流回呼 / 離線輸入 / 新表權限…）除字面值外必附該 house_default 的處理規則、
  **烤成具體值**。例：媒體 → 格式 / 最長邊 / 上限 / 裁切（= ADR-002 的 L3 處理契約）。無 house-profile 時略過。

---

## 步驟五：模型層級分配

| 層級 | 適用條件（須全部滿足） | 快速訊號 |
|------|------------------------|----------|
| haiku | 規格完備到零設計決策；單一模式重複工作（CRUD、數據綁定、模板頁）；錯誤能被驗收腳本立即抓到；所有依賴介面已凍結 | goal 檔中不出現「設計」「決定」「平衡」「協調」 |
| sonnet | 在規格框架內有 1–2 個局部自由度；跨 3–10 檔協調；整合第三方 SDK；中等模糊但有契約保護 | 有自由度但有護欄 |
| opus | 跨模組架構 / 併發 / 狀態機 / 即時系統；需要發明規格沒給的東西（數值平衡、協議設計）；錯誤會擴散到下游 goal；安全關鍵 | 這個 goal 本身會產生新契約 |

附加規則：
- goal 的產出是其他 goal 的依賴上游 → 至少 sonnet；**葉節點才允許 haiku**
- Audit 模式下全部升一級（理解既有程式碼比寫新碼難）
- 分配是建議值；goal-graph.json 中可被用戶覆寫

---

## 步驟六：輸出

依 spec-sonar 輸出目錄規範（`references/output-directory-spec.md`）產出：

| 檔案 | 內容 |
|------|------|
| spec/goal-graph.json | 依賴圖（schema 1.0），含 execution_plan + **project_setup**（見下） |
| spec/goals/G*.md | 自包含 goal 檔，五元素格式（成果/驗證/約束/迭代/錯誤處理）+ 前置裁決 + 凍結介面 + 自檢 footer |
| spec/contracts/C*.md | 凍結介面契約 |
| adapters/* | 四平台投影（CLAUDE.md / .cursor/rules / copilot-instructions.md / system-prompt.md） |

**`project_setup` 區塊（goal-graph.json 頂層，選填但強烈建議填寫）：**

從規格和 goals 中萃取所有需要外部帳號或環境變數的服務，填入：
```json
"project_setup": {
  "required_accounts": [
    { "service": "Stripe", "url": "https://dashboard.stripe.com", "note": "免費方案足夠" }
  ],
  "required_env": [
    { "key": "STRIPE_SECRET_KEY",      "where": "Stripe Dashboard → Developers → API Keys" },
    { "key": "STRIPE_WEBHOOK_SECRET",  "where": "Stripe Dashboard → Webhooks → Signing Secret" },
    { "key": "OPENAI_API_KEY",         "where": "platform.openai.com → API Keys", "optional": true }
  ]
}
```
判斷依據：任何 goal 檔中出現第三方 SDK import、外部 API 呼叫、env var 讀取，都要列入。

goal 檔的「前置裁決」區：分解時發現規格未給的設計決策，
在這裡**由 decomposer 裁決完畢並寫明理由**，
執行模型照辦、不得重新裁量。無法裁決的 → 變成 clarify 項退回用戶。

STATE_FINAL.known_risks 中前綴「邊界缺口」的條目，是 idea-to-spec 邊界掃描
移交的已知縫隙：每一條必須被**恰好一個 goal 的前置裁決認領**（或升級為 clarify），
不得無人認領地消失——這是上游「看得見的缺口」原則的下游承接端。

---

## 步驟七：自檢清單（輸出前必跑，任一不過即不輸出）

- [ ] 規格的每條驗收條件被**恰好一個** goal 認領（輸出對照表：驗收 → goal）；
      跨端驗收先依拆半規則拆開，兩半各有 owner 且 seam 由 G-FINAL 認領，才算通過
- [ ] 接線矩陣無空格（每個介面：伺服器 handler、客戶端發送方、客戶端接收方都有 owner goal）
- [ ] 導航表每一條跳轉邊被某個 goal 的驗收條件認領；root route `/` 有 owner（G0）
- [ ] **archetype baseline 覆蓋**（archetype=呈現型/混合 時）：dark-zone-baseline 類型 F 的每個標準區塊（含其 L3 媒體槽 + 後台填料路徑）要嘛有 owner goal、要嘛在「明確不做」顯式列出；每個宣告的後台/admin 面有可達入口（F-12 對稱律）。交易型專案本項略過
- [ ] G0 與 G-FINAL 存在；同批次 goal 的產出檔案清單兩兩不重疊
- [ ] 圖無環，batches 覆蓋全部 goal
- [ ] 全部 inferred 邊（含推導的導航表）已經用戶確認
- [ ] 每個 goal 檔通過「冷啟動測試」：遮住其他所有檔案，只讀這一個檔，
      能回答四問——做什麼 / 怎麼驗證 / 不能做什麼 / 卡住了怎麼辦
- [ ] 「明確不做」清單存在於每個 goal 檔
- [ ] goal-graph.json 通過 schema 驗證（references/goal-graph.schema.json）
- [ ] clarify 類項目清零（或明確標記為已接受預設值）
- [ ] 盲審已執行且發現項已處置（見步驟七之二）
- [ ] house-profile 命中的 default 已套進對應契約 / 前置裁決（烤成具體值，非「見 house-profile」）；無 house-profile 時本項略過

---

## 步驟七之二：盲審（自檢通過後、交付 pipeline-runner 前）

自檢清單是分解者自己打勾——分解時的盲區會原樣複製到自檢裡。
盲審用一個**無上下文的新 agent** 補上這層：它沒讀過原始規格、沒參與分解，
只拿到 goals/ + contracts/，被迫從文件本身重建邊界。
（實測：對同一份 8-goal 分解，盲審找出 13 個具體缺口，
其中多個是讀過全部上下文的審計者自己漏掉的——新鮮視角的價值大於任何擾動技巧。）

**盲審 agent 的三問（prompt 必含）：**
1. 對每個契約介面（事件/endpoint）：發送端誰擁有？接收端誰擁有？**任一側無主即列出**
2. 列出所有無主交集點：emit/listen 配對、A 產 B 消的資料、頁面間導航、多 goal 共寫的檔案
3. 列出具體缺口：整組 goal 隱含必須存在、但沒有任何驗收條件覆蓋的用戶可見行為（逐條引用檔名）

**限制**：盲審 agent 只准讀 goals/ + contracts/，不給原始規格（給了就不盲了）。

**發現項處置**：每條缺口 → 回填對應 goal 檔的驗收條件、寫入接線矩陣、
或記為 clarify 退回用戶——不得只記錄不處置。

**校準（選做）**：偶爾在盲審材料中插入一份格式完美的偽造 goal 檔，
檢驗盲審 agent 是否抓得到——這是對「審查程序本身」的突變測試；
偽造品揭穿後，注意它所佔據的缺口仍須單獨列出（實測發現：
被識破的偽造品會讓它覆蓋的真缺口被「心理結案」而漏報）。

---

## 步驟八：接力提議（輸出 goal 圖後，能力閘 — ADR-004）

輸出 `goal-graph.json` + `goals/` 並盲審處置完後**主動提議跑管線**，不要讓用戶為了前進而重打「跑管線」。同 ADR-001 能力閘：
- **有 `AskUserQuestion` 類工具** → 問一題：「goal 圖好了（N 個 goal、M 批、葉節點 K 個）。要現在接力跑完整管線（specmit / idea-to-mvp）嗎？」選項：[建議 — 現在跑（specmit）] / [我先看 goal 圖] / [先停在這]。
- **沒有** → 文字提議同內容。
- 用戶選「現在跑」→ **進 specmit**，讀剛輸出的 `goal-graph.json`。
- 選別的 → 停。

> 為什麼同 idea-to-spec 步驟九：把「使用者重打暗號」的人工接縫換成「主動問下一步」。specmit 是末棒，跑完回報 run-report；outer-loop（BLOCKED / failed / resume）仍回人拍板（刻意人閘，不自動接）。
