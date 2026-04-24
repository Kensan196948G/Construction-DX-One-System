# 📋 インシデントAPI（Incidents API）

> インシデントの作成・管理・ステータス遷移・統計

---

## 📋 エンドポイント一覧

| メソッド | パス | 認証 | ロール | 説明 |
|----------|------|------|--------|------|
| `GET` | `/api/v1/incidents` | 必要 | 全ロール | インシデント一覧 |
| `POST` | `/api/v1/incidents` | 必要 | admin, analyst | インシデント作成 |
| `GET` | `/api/v1/incidents/{id}` | 必要 | 全ロール | インシデント詳細 |
| `PATCH` | `/api/v1/incidents/{id}` | 必要 | admin, analyst | インシデント更新 |
| `GET` | `/api/v1/incidents/stats/summary` | 必要 | 全ロール | 統計サマリー |

---

## 🔄 ステータス遷移図

```
┌──────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────┐
│   open   │───▶│ investigating│───▶│  contained   │───▶│ resolved │
└──────────┘    └──────────────┘    └──────────────┘    └──────────┘
                                                              │
                                                              ▼
                                                        ┌──────────┐
                                                        │  closed  │
                                                        └──────────┘
```

## 🎯 優先度とSLA

| 優先度 | ラベル | 初動対応SLA | 解決SLA | 説明 |
|--------|--------|------------|---------|------|
| P1 | Critical | 15分 | 4時間 | サービス停止・データ漏洩 |
| P2 | High | 30分 | 8時間 | 重大な機能障害 |
| P3 | Medium | 2時間 | 24時間 | 軽微な障害 |
| P4 | Low | 8時間 | 72時間 | 情報提供・改善要望 |

---

## 1️⃣ GET /api/v1/incidents — インシデント一覧

### 概要

| 項目 | 値 |
|------|------|
| メソッド | `GET` |
| パス | `/api/v1/incidents` |
| 認証要件 | Bearer Token 必要 |
| 必要ロール | 全ロール（`incidents:read`） |

### クエリパラメータ

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|------------|------|------|-----------|------|
| `page` | int | ❌ | 1 | ページ番号 |
| `per_page` | int | ❌ | 20 | 件数（最大100） |
| `status` | string | ❌ | - | ステータスフィルター |
| `priority` | string | ❌ | - | 優先度フィルター（`P1`, `P2`, `P3`, `P4`） |
| `site` | string | ❌ | - | 建設現場フィルター |
| `assignee` | string | ❌ | - | 担当者フィルター |
| `start_date` | datetime | ❌ | - | 開始日時 |
| `end_date` | datetime | ❌ | - | 終了日時 |
| `sort` | string | ❌ | `-created_at` | ソート |

### リクエスト例

```http
GET /api/v1/incidents?status=open&priority=P1&site=東京建設現場A HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### レスポンス例（200 OK）

```json
{
  "status": "success",
  "data": [
    {
      "id": "INC-2026-0042",
      "title": "ランサムウェア感染の疑い",
      "status": "investigating",
      "priority": "P1",
      "site": "東京建設現場A",
      "assignee": "analyst01",
      "description": "建設管理端末でファイル暗号化の兆候を検出",
      "related_alerts": ["alert-001", "alert-003"],
      "sla": {
        "response_deadline": "2026-03-24T08:30:00Z",
        "resolution_deadline": "2026-03-24T12:15:00Z",
        "response_met": true,
        "resolution_met": null
      },
      "created_at": "2026-03-24T08:15:00Z",
      "updated_at": "2026-03-24T08:20:00Z"
    }
  ],
  "meta": {
    "total": 3,
    "page": 1,
    "per_page": 20,
    "total_pages": 1
  }
}
```

### エラーケース

| ステータス | コード | 説明 |
|-----------|--------|------|
| 400 | `INVALID_PARAMETER` | パラメータ不正 |
| 401 | `INVALID_TOKEN` | 認証失敗 |

---

## 2️⃣ POST /api/v1/incidents — インシデント作成

### 概要

| 項目 | 値 |
|------|------|
| メソッド | `POST` |
| パス | `/api/v1/incidents` |
| 認証要件 | Bearer Token 必要 |
| 必要ロール | admin, analyst（`incidents:write`） |

> インシデント作成時に優先度に応じた **SLAタイマーが自動開始** されます。

### リクエストボディ

| フィールド | 型 | 必須 | 説明 |
|------------|------|------|------|
| `title` | string | ✅ | タイトル（1-300文字） |
| `priority` | string | ✅ | 優先度（`P1`, `P2`, `P3`, `P4`） |
| `description` | string | ✅ | 詳細説明 |
| `site` | string | ❌ | 建設現場名 |
| `assignee` | string | ❌ | 担当者ユーザー名 |
| `related_alerts` | string[] | ❌ | 関連アラートIDリスト |
| `tags` | string[] | ❌ | タグ |

### リクエスト例

```http
POST /api/v1/incidents HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Content-Type: application/json

{
  "title": "ランサムウェア感染の疑い",
  "priority": "P1",
  "description": "建設管理端末（PC-A01）でファイル暗号化の兆候を検出。複数の.encryptedファイルを確認。",
  "site": "東京建設現場A",
  "assignee": "analyst01",
  "related_alerts": ["alert-001", "alert-003"],
  "tags": ["ransomware", "T1486", "critical-infrastructure"]
}
```

### レスポンス例（201 Created）

```json
{
  "status": "success",
  "data": {
    "id": "INC-2026-0042",
    "title": "ランサムウェア感染の疑い",
    "status": "open",
    "priority": "P1",
    "site": "東京建設現場A",
    "assignee": "analyst01",
    "sla": {
      "response_deadline": "2026-03-24T08:30:00Z",
      "resolution_deadline": "2026-03-24T12:15:00Z",
      "timer_started_at": "2026-03-24T08:15:00Z"
    },
    "created_at": "2026-03-24T08:15:00Z"
  },
  "message": "インシデントが作成されました。SLAタイマーを開始しました。"
}
```

### エラーケース

| ステータス | コード | 説明 |
|-----------|--------|------|
| 401 | `INVALID_TOKEN` | 認証失敗 |
| 403 | `FORBIDDEN` | 権限不足 |
| 422 | `VALIDATION_ERROR` | バリデーションエラー |

---

## 3️⃣ GET /api/v1/incidents/{id} — インシデント詳細

### 概要

| 項目 | 値 |
|------|------|
| メソッド | `GET` |
| パス | `/api/v1/incidents/{id}` |
| 認証要件 | Bearer Token 必要 |
| 必要ロール | 全ロール（`incidents:read`） |

### レスポンス例（200 OK）

```json
{
  "status": "success",
  "data": {
    "id": "INC-2026-0042",
    "title": "ランサムウェア感染の疑い",
    "status": "investigating",
    "priority": "P1",
    "site": "東京建設現場A",
    "assignee": "analyst01",
    "description": "建設管理端末（PC-A01）でファイル暗号化の兆候を検出。複数の.encryptedファイルを確認。",
    "related_alerts": [
      {
        "id": "alert-001",
        "title": "不審なファイル暗号化検出",
        "severity": "critical"
      },
      {
        "id": "alert-003",
        "title": "C2通信の疑い",
        "severity": "critical"
      }
    ],
    "timeline": [
      {
        "timestamp": "2026-03-24T08:15:00Z",
        "action": "created",
        "user": "analyst01",
        "detail": "インシデント作成"
      },
      {
        "timestamp": "2026-03-24T08:20:00Z",
        "action": "status_changed",
        "user": "analyst01",
        "detail": "open → investigating"
      }
    ],
    "sla": {
      "response_deadline": "2026-03-24T08:30:00Z",
      "resolution_deadline": "2026-03-24T12:15:00Z",
      "response_met": true,
      "resolution_met": null,
      "elapsed_minutes": 5
    },
    "tags": ["ransomware", "T1486", "critical-infrastructure"],
    "created_at": "2026-03-24T08:15:00Z",
    "updated_at": "2026-03-24T08:20:00Z"
  }
}
```

### エラーケース

| ステータス | コード | 説明 |
|-----------|--------|------|
| 401 | `INVALID_TOKEN` | 認証失敗 |
| 404 | `NOT_FOUND` | インシデントが存在しない |

---

## 4️⃣ PATCH /api/v1/incidents/{id} — インシデント更新

### 概要

| 項目 | 値 |
|------|------|
| メソッド | `PATCH` |
| パス | `/api/v1/incidents/{id}` |
| 認証要件 | Bearer Token 必要 |
| 必要ロール | admin, analyst（`incidents:write`） |

### リクエストボディ（部分更新）

| フィールド | 型 | 必須 | 説明 |
|------------|------|------|------|
| `status` | string | ❌ | ステータス遷移 |
| `priority` | string | ❌ | 優先度変更 |
| `assignee` | string | ❌ | 担当者変更 |
| `description` | string | ❌ | 説明更新 |
| `comment` | string | ❌ | タイムラインにコメント追加 |

### ステータス遷移ルール

| 現在のステータス | 遷移可能先 |
|----------------|-----------|
| `open` | `investigating` |
| `investigating` | `contained`, `open` |
| `contained` | `resolved`, `investigating` |
| `resolved` | `closed`, `investigating` |
| `closed` | （遷移不可） |

### リクエスト例

```http
PATCH /api/v1/incidents/INC-2026-0042 HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Content-Type: application/json

{
  "status": "contained",
  "comment": "感染端末をネットワークから隔離完了。他端末への横展開は確認されず。"
}
```

### レスポンス例（200 OK）

```json
{
  "status": "success",
  "data": {
    "id": "INC-2026-0042",
    "status": "contained",
    "previous_status": "investigating",
    "updated_at": "2026-03-24T09:00:00Z",
    "timeline_entry": {
      "timestamp": "2026-03-24T09:00:00Z",
      "action": "status_changed",
      "user": "analyst01",
      "detail": "investigating → contained: 感染端末をネットワークから隔離完了。他端末への横展開は確認されず。"
    }
  }
}
```

### エラーケース

| ステータス | コード | 説明 |
|-----------|--------|------|
| 400 | `INVALID_TRANSITION` | 無効なステータス遷移 |
| 401 | `INVALID_TOKEN` | 認証失敗 |
| 403 | `FORBIDDEN` | 権限不足 |
| 404 | `NOT_FOUND` | インシデントが存在しない |

#### 無効な遷移エラー例

```json
{
  "status": "error",
  "error": {
    "code": "INVALID_TRANSITION",
    "message": "closed から investigating への遷移は許可されていません",
    "details": {
      "current_status": "closed",
      "requested_status": "investigating",
      "allowed_transitions": []
    }
  }
}
```

---

## 5️⃣ GET /api/v1/incidents/stats/summary — 統計サマリー

### 概要

| 項目 | 値 |
|------|------|
| メソッド | `GET` |
| パス | `/api/v1/incidents/stats/summary` |
| 認証要件 | Bearer Token 必要 |
| 必要ロール | 全ロール（`incidents:read`） |

### レスポンス例（200 OK）

```json
{
  "status": "success",
  "data": {
    "by_status": {
      "open": 5,
      "investigating": 3,
      "contained": 2,
      "resolved": 15,
      "closed": 120
    },
    "by_priority": {
      "P1": 3,
      "P2": 8,
      "P3": 22,
      "P4": 112
    },
    "by_site": {
      "東京建設現場A": 45,
      "大阪建設現場B": 32,
      "名古屋建設現場C": 28,
      "福岡建設現場D": 18,
      "その他": 22
    },
    "sla_compliance": {
      "response_rate": 95.2,
      "resolution_rate": 88.7
    },
    "trends": {
      "this_month": 42,
      "last_month": 38,
      "change_percent": 10.5
    },
    "total": 145,
    "period": {
      "start": "2026-01-01T00:00:00Z",
      "end": "2026-03-24T23:59:59Z"
    }
  }
}
```
