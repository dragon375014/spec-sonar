# Conflict Analysis Mode — Skill 生態衝突分析

<!-- spec-sonar v1.0 設計文件 -->

## 定位

當一個環境裡裝了多個 skills，它們會互搶觸發、互相覆蓋產物、或對同一情境
給出不相容指令。Conflict Analysis Mode 對 SKILL.md 清單做靜態分析，
輸出 conflict-report.md。

## 流程（S1–S5）

```
輸入：所有 SKILL.md 路徑清單
S1 解析：每個 skill 抽出
   { name, 觸發短語集, 輸出產物（檔名）, 狀態區塊名, 核心動詞域 }
S2 觸發重疊：兩兩配對 → 生成 20 句合成測試語句
   （覆蓋雙方觸發短語的交集區）→ 判斷每句會觸發誰；同句雙觸發 = 衝突
S3 邏輯矛盾：兩 skill 對同一情境給出不相容指令
   （如都聲稱「主動觸發、優先於其他」）
S4 命名空間污染：輸出檔名碰撞 / 狀態區塊名碰撞 / 同名異義術語
S5 輸出 conflict-report.md
```

## `conflict-report.md` 格式規範

必要結構：
1. 掃描摘要（skill 數、衝突數、分級統計）
2. 摘要表
3. 每衝突一節，欄位固定：
   - skill-A vs skill-B
   - 類型
   - 嚴重度
   - 證據（雙方原文引述）
   - 影響（用戶會經歷什麼）
   - 建議（具體改法，含改哪一方的哪一句）

### 類型枚舉

| 類型 | 定義 |
|------|------|
| `trigger-overlap` | 同一句用戶輸入會觸發兩個 skill |
| `logic-contradiction` | 兩 skill 對同一情境給出不相容指令 |
| `namespace-pollution` | 輸出檔名 / 狀態區塊名 / 術語碰撞 |

### 嚴重度

| 級別 | 定義 |
|------|------|
| `critical` | 必然互搶，或產物互相覆蓋 |
| `high` | 常見語句會誤觸 |
| `medium` | 特定語句才碰撞 |
| `low` | 理論性 |

## 範例

完整範例見 `examples/conflict-report-sample.md`。
