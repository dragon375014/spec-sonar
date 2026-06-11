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

拒收回覆模板：
> 「這份輸入還不能分解：缺 [X]。
> 缺規格 → 我可以先用 idea-to-spec 問答收斂；
> 規格含糊 → 我可以先跑 Audit Mode 找出全部空洞。要走哪條？」

---

## 步驟一：模式判斷

| 模式 | 輸入特徵 | 行為差異 |
|------|----------|----------|
| From Zero | CLAUDE.md + STATE_FINAL.json，無既有程式碼 | 全量分解，契約檔全新建立 |
| Audit | remediation-goals.md + project-fingerprint.md | goal 接到既有程式碼上；每個 goal 加「現狀」區塊 + 回歸保護驗收項（不得弄壞 fingerprint 中既有的 routes/介面） |
| Complex System | 模組 > 8，或出現多個子系統邊界（進銷存/會計/人資） | 兩層分解：先建子系統依賴圖，再各子系統內建模組圖；跨子系統溝通只允許透過契約檔 |

---

## 步驟二：實體與介面萃取（依賴推導的原料）

從規格抽四張表：

1. **實體表**：資料結構區塊的每個 Entity → `{名稱, 欄位, owner 模組}`
   - owner 判定：哪個模組的驗收條件「建立 / 產生 / 寫入」這個實體，它就是 owner
   - 多模組寫入 → 標記「共享」，自動成為契約檔候選
2. **事件/API 表**：每個 endpoint、socket 事件 → `{名稱, 方向, payload, 定義模組}`
3. **狀態表**：跨模組讀寫的 runtime 欄位（如 status、timeRemaining）
   → `{欄位, 寫入者, 讀取者清單}`
4. **介面表**：每個頁面/畫面 → `{路徑, 顯示哪些模組產出的資料}`

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

**契約檔（contracts/C*.md）規則：**
- 觸發：≥ 2 個 goal 共用的介面（事件名、payload、實體欄位、數值表）
- 內容：字面值，不是描述——事件名全列、payload 給 JSON 實例（不只 schema）、
  數值表給完整數字
- 凍結：goal 執行期間不可修改。要改 → 回到 decomposer 重新發版
  （C1 → C1.v2），同時列出受影響 goal 清單並重置其狀態

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

---

## 步驟七：自檢清單（輸出前必跑，任一不過即不輸出）

- [ ] 規格的每條驗收條件被**恰好一個** goal 認領（輸出對照表：驗收 → goal）
- [ ] 圖無環，batches 覆蓋全部 goal
- [ ] 全部 inferred 邊已經用戶確認
- [ ] 每個 goal 檔通過「冷啟動測試」：遮住其他所有檔案，只讀這一個檔，
      能回答四問——做什麼 / 怎麼驗證 / 不能做什麼 / 卡住了怎麼辦
- [ ] 「明確不做」清單存在於每個 goal 檔
- [ ] goal-graph.json 通過 schema 驗證（references/goal-graph.schema.json）
- [ ] clarify 類項目清零（或明確標記為已接受預設值）
