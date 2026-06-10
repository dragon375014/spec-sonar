# 數學塔防對戰系統 — 專案規格

## 專案目標

建立一個跑在平板瀏覽器上的課堂即時多人塔防數學遊戲：學生分植物隊與殭屍隊，透過回答國中數學題獲得個人資源，在即時同步的格子地圖上部署攻防單位，老師透過獨立控制台監控並介入遊戲。

---

## 技術棧

- **遊戲前端**：Phaser.js 3 + HTML5 Canvas
- **即時通訊**：Socket.io（Client + Server）
- **後端**：Node.js + Express
- **題庫資料庫**：Supabase（PostgreSQL）
- **Session 狀態**：後端記憶體（Map 物件），遊戲結束即清除
- **QR Code 產生**：`qrcode` npm 套件（後端產生 Data URL）
- **部署**：Railway 或 Render（需支援 WebSocket）

---

## 資料結構

```
GameRoom {
  roomCode: string (6碼)
  teacherId: string (socket id)
  status: 'waiting' | 'playing' | 'paused' | 'ended'
  unit: string (數學單元名稱)
  difficulty: 'easy' | 'medium' | 'hard'
  timeLimit: number (秒)
  timeRemaining: number (秒)
  players: Map<socketId, Player>
  mapState: GridCell[][]
}

Player {
  socketId: string
  name: string
  team: 'plant' | 'zombie'
  resources: number (陽光 or 黑暗能量)
  correctCount: number
  wrongCount: number
  currentQuestion: Question | null
  cooldowns: Map<unitType, timestamp>
}

GridCell {
  x: number
  y: number
  occupant: Unit | null
}

Unit {
  type: string
  team: 'plant' | 'zombie'
  hp: number
  attackPower: number
  range: number (植物用)
  speed: number (殭屍用)
  cooldownMs: number
}

Question {
  id: string
  content: string
  options: string[]
  answer: string
  unit: string
  difficulty: string
}
```

---

## 功能模組（依開發順序）

### 模組一：房間系統

**驗收條件：**
- [ ] 老師呼叫 `POST /api/room/create`，傳入單元名稱與時長，回傳 6 碼房間代碼與 QR Code（Data URL）
- [ ] 學生呼叫 `POST /api/room/join`，傳入代碼與暱稱，回傳 socket token 與分配隊伍
- [ ] 系統自動平衡隊伍人數（差距超過 1 人時，提示學生換隊）
- [ ] 老師的控制台頁面（`/teacher/:roomCode`）顯示目前加入人數與隊伍分配
- [ ] 學生的等待頁面（`/student/:roomCode`）顯示自己的隊伍與等待開始訊息

**不做：** 帳號登入、歷史紀錄

---

### 模組二：題庫與答題引擎

**驗收條件：**
- [ ] Supabase 有 `questions` 資料表，欄位：id、content、options（JSON array）、answer、unit、difficulty
- [ ] 老師選擇單元後，系統從題庫隨機拉題分配給學生
- [ ] 學生平板顯示題目與 4 個選項（單選）
- [ ] 答對 → 個人資源 +N（N 依難度設定：easy=1, medium=2, hard=3）→ 立即顯示下一題
- [ ] 答錯 → 顯示正確答案 1.5 秒 → 顯示下一題（資源不變）
- [ ] 每個學生的題目佇列獨立，不同學生看到不同題目順序

---

### 模組三：遊戲引擎（地圖 + 攻防邏輯）

**驗收條件：**
- [ ] Phaser.js 渲染 9×5 格子地圖（植物隊佔左 4 欄，殭屍從右側進入）
- [ ] 植物隊可點選空格子部署植物單位（消耗陽光），同格子冷卻期間無法再部署
- [ ] 殭屍隊可召喚殭屍（消耗黑暗能量），殭屍從右側進入對應行向左移動
- [ ] 植物自動攻擊射程內的殭屍，殭屍自動攻擊路徑上的植物
- [ ] 單位 HP 歸零時從地圖移除
- [ ] 每種單位有各自的冷卻時間（至少 3 種植物、3 種殭屍）
- [ ] 資源不足時，部署按鈕呈現 disabled 狀態並顯示所需資源數

**植物單位（初版三種）：**
| 單位 | 陽光消耗 | 冷卻 | 攻擊方式 |
|------|----------|------|----------|
| 豌豆射手 | 1 | 15s | 直線射程攻擊 |
| 向日葵 | 2 | 30s | 被動產生陽光（每 10s +1） |
| 堅果牆 | 2 | 45s | 高 HP 阻擋殭屍 |

**殭屍單位（初版三種）：**
| 單位 | 黑暗能量消耗 | 冷卻 | 特性 |
|------|-------------|------|------|
| 普通殭屍 | 1 | 10s | 標準速度與 HP |
| 路障殭屍 | 2 | 20s | 高 HP，移動較慢 |
| 衝鋒殭屍 | 2 | 25s | 低 HP，移動快 |

---

### 模組四：即時同步（WebSocket）

**驗收條件：**
- [ ] 所有在同一房間的 socket 連線收到相同的 `gameState` 事件
- [ ] 任何學生部署單位後，所有平板在 300ms 內看到地圖更新
- [ ] 延遲超過 1s 時，客戶端顯示「連線不穩定」提示
- [ ] 學生斷線重連後，地圖狀態自動恢復到當前狀態
- [ ] 以下事件需廣播：`unit:placed`、`unit:removed`、`unit:attacked`、`zombie:moved`、`resource:updated`

**Socket 事件規格：**
```
Client → Server:
  'room:join'       { roomCode, name, team }
  'unit:deploy'     { unitType, x, y }
  'question:answer' { questionId, answer }

Server → Client:
  'game:state'      { mapState, players, timeRemaining, status }
  'game:start'      { unit, difficulty, timeLimit }
  'game:end'        { winner, reason }
  'question:next'   { question }
  'resource:sync'   { playerId, resources }
```

---

### 模組五：老師控制台

**驗收條件：**
- [ ] 老師頁面即時顯示每位學生：名字、隊伍、答對率、答對數、資源貢獻
- [ ] 暫停按鈕：廣播 `game:pause`，所有客戶端凍結操作
- [ ] 繼續按鈕：廣播 `game:resume`
- [ ] 難度調整（簡單/中等/困難）：即時影響後續出題
- [ ] 強制結束按鈕：需二次確認，確認後廣播 `game:end`
- [ ] 老師頁面不顯示遊戲地圖（只有數據面板）

---

### 模組六：勝負判定與結束報告

**驗收條件：**
- [ ] 偵測到殭屍 x 座標 ≤ 0（突破底線）→ 觸發 `game:end { winner: 'zombie', reason: 'breakthrough' }`
- [ ] 倒數計時歸零 → 計算兩隊剩餘 HP 總量判定勝負 → 觸發 `game:end`
- [ ] 遊戲結束畫面顯示勝隊與敗隊
- [ ] 老師頁面顯示報告：
  - 個人成績表：每位學生的答對率、答對/答錯題目列表、資源貢獻量
  - 全班統計：答錯率最高的 3 道題、兩隊答題總貢獻比較
- [ ] 報告頁面可截圖或列印（`@media print` 樣式）

---

## 明確不做

- 不做學生帳號系統（無 email、無密碼、無 JWT）
- 不做跨 session 的歷史記錄儲存
- 不做地圖編輯器
- 不做課程進度追蹤
- 不做排行榜或成就系統
- 不做單位外觀自訂
- **任何未在以上模組清單的功能，實作前必須先確認**

---

## 安全與權限規則

- 老師 socket 連線以 `roomCode + teacherToken` 驗證（開房間時產生一次性 token）
- 學生 socket 只能操作自己的 `socketId` 對應的 Player
- 遊戲狀態（`GameRoom`）只存在後端記憶體中，客戶端無法直接修改
- 所有 `unit:deploy` 事件在後端驗證：資源是否足夠、冷卻是否結束、格子是否空閒

---

## 開發順序建議

1. 先完成模組一（房間系統）+ 模組四（Socket 基礎連線）——驗證即時架構可行
2. 完成模組二（答題）——驗證題庫查詢與個人資源增減
3. 完成模組三（遊戲引擎）——最耗時，建議先用簡單圖形替代美術
4. 完成模組五（老師控制台）——基於已有 Socket 事件擴充
5. 最後完成模組六（勝負 + 報告）

---

## 已知技術風險

- **WebSocket 在學校網路的穩定性**：上線前必須在實際教室環境測試 30+ 台同時連線
- **Phaser.js 在低階 Android 平板的效能**：建議加入 FPS 監控，低於 20fps 時降低動畫品質
- **後端記憶體 Session**：若伺服器重啟，所有進行中的遊戲會中斷——開學期間避免更新部署
