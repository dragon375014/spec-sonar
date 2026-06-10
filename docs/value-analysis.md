# spec-sonar 專案價值分析

<!-- spec-sonar v1.0 -->

> **Executive summary (EN):** spec-sonar's defensible value is not "spec-driven development"
> (a crowded space: GitHub spec-kit, AWS Kiro, BMAD, task-master) but three specific assets:
> (1) dark-zone detection targets *unstated* requirements, not formatting of stated ones;
> (2) pre-adjudication + the cold-start test turn "any model can execute" from a slogan into
> a testable property; (3) requirement *change* is a first-class citizen (STATE conflict
> protocols), which competitors treat as out of scope. Main risks: quality is hard to measure
> without an eval harness, and the convergence engine itself requires a strong model.

## 一、它解決的真問題

AI coding 的失敗主因已經從「模型不會寫」移到「沒人寫下該寫的東西」。
mathdefense 案例提供了直接證據：一份看起來非常完整的規格（六模組、驗收條件、
資料結構、安全規則俱全），仍藏著三個會在開工第一天引爆的洞——
單位數值真空、移動模型未定、重連需求與「不做帳號」互撞。
**這三個洞不是寫作品質問題，是「不知道自己不知道」問題**——
而這正是市面上工具最少覆蓋的一層。

## 二、三個核心資產（可獨立存活的價值）

1. **dark-zone-baseline（領域知識結晶）**
   10 基準維度 + 5 類型擴充包是蒸餾過的失敗經驗清單。
   即使不用整套工具鏈，單獨拿它當 PRD checklist 都有價值。
   它也是社群貢獻的天然入口（門檻明確：附真實失敗案例才收）。

2. **裁決前置 + 冷啟動測試（方法論貢獻）**
   「任何模型可執行」在大多數專案裡是口號；spec-sonar 把它變成可測試性質：
   goal 檔合格 = 最弱目標模型在零脈絡下能答出四問。
   經濟學意義：強模型的智慧被固化成便宜模型可執行的結構——
   設計成本攤提一次，執行成本降一個數量級，且執行層無 vendor lock-in。

3. **STATE 衝突處理協議（變更是一級公民）**
   用戶會推翻、會自相矛盾、會臨時追加——多數 spec 工具假裝這不會發生。
   推翻級聯、矛盾三選一、後期追加分級，是收斂引擎從 demo 變成可用工具的分界線。

## 三、競品對照與差異化

| 競品 | 它做什麼 | spec-sonar 的差異 |
|------|----------|-------------------|
| GitHub spec-kit | /specify → /plan → /tasks 的規格驅動開發 | spec-kit 格式化「已說出的需求」；spec-sonar 偵測「沒說出的需求」（暗區）並處理需求變更 |
| AWS Kiro | IDE 內建 spec-driven 工作流 | 綁定單一 IDE；spec-sonar 是 adapter 投影，四平台通用 |
| BMAD / agile-agent 類 | 多 agent 角色扮演（PM/架構師/QA） | spec-sonar 明確反角色扮演——固定行為規則 + 可驗證輸出 |
| claude-task-master | PRD → 任務清單 | 任務清單無依賴類型、無證據、無契約凍結；goal-graph 有四類依賴邊 + evidence + 契約版本化 |

另一個結構性差異：**非技術用戶優先**（user_tech_level 分層、非技術用語提問），
競品幾乎全部假設用戶是工程師。

## 四、誠實的弱點與風險

1. **品質不可量測（最大缺口）**：暗區覆蓋率、goal 冷啟動通過率目前都沒有 eval。
   沒有數字，「比較好」只是主張。→ 路線圖第一優先應是 eval harness。
2. **收斂引擎自身需要強模型**：產出 model-agnostic，但生產過程綁定
   高階模型的提問與裁決品質。這是設計取捨（也是賣點），但要誠實標示。
3. **大廠競爭**：spec-kit 有 GitHub 的分發管道。spec-sonar 的生存空間在
   「暗區偵測 + 變更處理 + 跨平台」三件大廠還沒做好的事，需要跑得快。
4. **維度清單會腐化**：dark-zone-baseline 是經驗清單，需要持續餵真實失敗案例，
   否則三年後就過時。CONTRIBUTING 的證據門檻就是為此設計。
5. **語言門檻**：核心 SKILL.md 是繁中。Claude 執行無礙（lang 欄位自適應），
   但對國際貢獻者的閱讀門檻是真實的。

## 五、適用族群（按價值密度排序）

1. **非技術創業者 / 接案工作室**——把「客戶說不清楚」轉成結構化收斂，
   READMEmd + CLAUDE.md 雙產出同時服務溝通與執行。
2. **用多個 AI 工具的獨立開發者**——一份規格投影到 Claude Code + Cursor + Copilot，
   不用維護三份漂移的指示檔。
3. **教學場景**——軟體工程課的需求工程教材：亮區/暗區是可教學的心智模型。
4. **企業內部工具團隊**——Audit Mode 對既有爛攤子的價值高於 From Zero。

## 六、結論

spec-sonar 的價值不在「又一個 spec 工具」，在於它選了一個窄而深的切入點：
**未知的未知 → 結構化偵測；強模型的設計 → 可驗證的固化；需求變更 → 協議化處理**。
這三件事每一件都有真實案例佐證（mathdefense 自審即抓到三洞 + 自身 schema 漂移）。
下一步的關鍵不是加功能，是把「比較好」變成可量測——eval harness 先行。
