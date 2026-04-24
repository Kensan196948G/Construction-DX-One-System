# 🚨 アラートAPI（Alerts API）

> アラートの一覧取得・詳細・承認・集計・インジェスト

---

## 📋 エンドポイント一覧

| メソッド | パス | 認証 | ロール | 説明 |
|----------|------|------|--------|------|
| `GET` | `/api/v1/alerts` | 必要 | 全ロール | アラート一覧取得 |
| `GET` | `/api/v1/alerts/{id}` | 必要 | 全ロール | アラート詳細取得 |
| `PATCH` | `/api/v1/alerts/{id}/acknowledge` | 必要 | admin, analyst | アラート承認 |
| `GET` | `/api/v1/alerts/summary/by-severity` | 必要 | 全ロール | 重要度別集計 |
| `POST` | `/api/v1/alerts/ingest` | 必要 | admin, analyst | アラートインジェスト |

---

## 1️⃣ GET /api/v1/alerts — アラート一覧取得

### 概要

| 項目 | 値 |
|------|------|
| メソッド | `GET` |
| パス | `/api/v1/alerts` |
| 認証要件 | Bearer Token 必要 |
| 必要ロール | 全ロール（`alerts:read`） |

### クエリパラメータ

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|------------|------|------|-----------|------|
| `page` | int | ❌ | 1 | ページ番号 |
| `per_page` | int | ❌ | 20 | 1ページあたりの件数（最大100） |
| `severity` | string | ❌ | - | 重要度フィルター（`critical`, `high`, `medium`, `low`） |
| `acknowledged` | bool | ❌ | - | 承認状態フィルター |
| `source` | string | ❌ | - | ソースフィルター |
| `start_date` | datetime | ❌ | - | 開始日時（ISO 8601） |
| `end_date` | datetime | ❌ | - | 終了日時（ISO 8601） |
| `sort` | string | ❌ | `-created_at` | ソート項目 |

### リクエスト例

```http
GET /api/v1/alerts?severity=critical&acknowledged=false&page=1&per_page=10 HTTP/1.1
Host: siem.example.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### レスポンス例（200 OK）

```json
{
  "status": "success",
  "data": [
    {
      "id": "alert-001",
      "title": "不審なポートスキャン検出",
      "severity": "critical",
      "source": "firewall",
      "description": "192.168.1.100 から複数ポートへのスキャンを検出",
      "acknowledged": false,
      "acknowledged_by": null,
      "acknowledged_at": null,
      "mitre_tactic": "Discovery",
      "mitre_technique": "T1046",
      "site": "東京建設現場A",
      "created_at": "2026-03-24T08:15:00Z",
      "updated_at": "2026-03-24T08:15:00Z"
    },
    {
      "id": "alert-002",
      "title": "ブルートフォース攻撃検出",
      "severity": "high",
      "source": "ids",
      "description": "SSH へのブルートフォース攻撃を検出（50回/分）",
      "acknowledged": false,
      "acknowledged_by": null,
      "acknowledged_at": null,
      "mitre_tactic": "Credential Access",
      "mitre_technique": "T1110",
      "site": "大阪建設現場B",
      "created_at": "2026-03-24T07:45:00Z",
      "updated_at": "2026-03-24T07:45:00Z"
    }
  ],
  "meta": {
    "total": 156,
    "page": 1,
    "per_page": 10,
    "total_pages": 16,
    "timestamp": "2026-03-24T10:00:00Z"
  }
}
```

### エラーケース

| ステータス | コード | 説明 |
|-----------|--------|------|
| 400 | `INVALID_PARAMETER` | クエリパラメータが不正 |
| 401 | `INVALID_TOKEN` | 認証失敗 |

---

## 2️⃣ GET /api/v1/alerts/{id} — アラート詳細取得

### 概要

| 項目 | 値 |
|------|------|
| メソッド | `GET` |
| パス | `/api/v1/alerts/{id}` |
| 認証要件 | Bearer Token 必要 |
| 必要ロール | 全ロール（`alerts:read`） |

### パスパラメータ

| パラメータ | 型 | 説明 |
|------------|------|------|
| `id` | string | アラートID |

### リクエスト例

```http
GET /api/v1/alerts/alert-001 HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### レスポンス例（200 OK）

```json
{
  "status": "success",
  "data": {
    "id": "alert-001",
    "title": "不審なポートスキャン検出",
    "severity": "critical",
    "source": "firewall",
    "description": "192.168.1.100 から複数ポートへのスキャンを検出",
    "raw_log": "Mar 24 08:15:00 fw01 kernel: DROP IN=eth0 ...",
    "acknowledged": false,
    "acknowledged_by": null,
    "acknowledged_at": null,
    "mitre_tactic": "Discovery",
    "mitre_technique": "T1046",
    "site": "東京建設現場A",
    "source_ip": "192.168.1.100",
    "dest_ip": "10.0.0.0/24",
    "related_alerts": ["alert-003", "alert-007"],
    "created_at": "2026-03-24T08:15:00Z",
    "updated_at": "2026-03-24T08:15:00Z"
  }
}
```

### エラーケース

| ステータス | コード | 説明 |
|-----------|--------|------|
| 401 | `INVALID_TOKEN` | 認証失敗 |
| 404 | `NOT_FOUND` | 指定IDのアラートが存在しない |

---

## 3️⃣ PATCH /api/v1/alerts/{id}/acknowledge — アラート承認

### 概要

| 項目 | 値 |
|------|------|
| メソッド | `PATCH` |
| パス | `/api/v1/alerts/{id}/acknowledge` |
| 認証要件 | Bearer Token 必要 |
| 必要ロール | admin, analyst（`alerts:acknowledge`） |

### パスパラメータ

| パラメータ | 型 | 説明 |
|------------|------|------|
| `id` | string | アラートID |

### リクエストボディ（任意）

```json
{
  "comment": "調査中。関連するネットワークログを確認済み。"
}
```

### リクエスト例

```http
PATCH /api/v1/alerts/alert-001/acknowledge HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Content-Type: application/json

{
  "comment": "調査中。関連するネットワークログを確認済み。"
}
```

### レスポンス例（200 OK）

```json
{
  "status": "success",
  "data": {
    "id": "alert-001",
    "acknowledged": true,
    "acknowledged_by": "analyst01",
    "acknowledged_at": "2026-03-24T10:05:00Z",
    "comment": "調査中。関連するネットワークログを確認済み。"
  }
}
```

### エラーケース

| ステータス | コード | 説明 |
|-----------|--------|------|
| 401 | `INVALID_TOKEN` | 認証失敗 |
| 403 | `FORBIDDEN` | viewer ロールからのアクセス |
| 404 | `NOT_FOUND` | アラートが存在しない |
| 409 | `ALREADY_ACKNOWLEDGED` | 既に承認済み |

---

## 4️⃣ GET /api/v1/alerts/summary/by-severity — 重要度別集計

### 概要

| 項目 | 値 |
|------|------|
| メソッド | `GET` |
| パス | `/api/v1/alerts/summary/by-severity` |
| 認証要件 | Bearer Token 必要 |
| 必要ロール | 全ロール（`alerts:read`） |

### リクエスト例

```http
GET /api/v1/alerts/summary/by-severity HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### レスポンス例（200 OK）

```json
{
  "status": "success",
  "data": {
    "summary": {
      "critical": {
        "total": 12,
        "acknowledged": 8,
        "unacknowledged": 4
      },
      "high": {
        "total": 34,
        "acknowledged": 28,
        "unacknowledged": 6
      },
      "medium": {
        "total": 67,
        "acknowledged": 55,
        "unacknowledged": 12
      },
      "low": {
        "total": 43,
        "acknowledged": 40,
        "unacknowledged": 3
      }
    },
    "total": 156,
    "period": {
      "start": "2026-03-01T00:00:00Z",
      "end": "2026-03-24T23:59:59Z"
    }
  }
}
```

---

## 5️⃣ POST /api/v1/alerts/ingest — アラートインジェスト

### 概要

| 項目 | 値 |
|------|------|
| メソッド | `POST` |
| パス | `/api/v1/alerts/ingest` |
| 認証要件 | Bearer Token 必要 |
| 必要ロール | admin, analyst（`alerts:write`） |
| バリデーション | Pydantic モデルによる厳密なバリデーション |

### リクエストボディ

| フィールド | 型 | 必須 | 説明 |
|------------|------|------|------|
| `title` | string | ✅ | アラートタイトル（1-200文字） |
| `severity` | string | ✅ | 重要度（`critical`, `high`, `medium`, `low`） |
| `source` | string | ✅ | ソース（`firewall`, `ids`, `endpoint`, `network`, `iot`） |
| `description` | string | ✅ | 説明文 |
| `site` | string | ❌ | 建設現場名 |
| `source_ip` | string | ❌ | 送信元IP（IPv4/IPv6） |
| `dest_ip` | string | ❌ | 宛先IP |
| `raw_log` | string | ❌ | 生ログ |
| `mitre_tactic` | string | ❌ | MITRE ATT&CK タクティック |
| `mitre_technique` | string | ❌ | MITRE ATT&CK テクニックID |

### リクエスト例

```http
POST /api/v1/alerts/ingest HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Content-Type: application/json

{
  "title": "不正プロセス実行検出",
  "severity": "high",
  "source": "endpoint",
  "description": "建設現場端末でPowerShellによる不正なスクリプト実行を検出",
  "site": "東京建設現場A",
  "source_ip": "192.168.1.50",
  "mitre_tactic": "Execution",
  "mitre_technique": "T1059"
}
```

### レスポンス例（201 Created）

```json
{
  "status": "success",
  "data": {
    "id": "alert-157",
    "title": "不正プロセス実行検出",
    "severity": "high",
    "created_at": "2026-03-24T10:10:00Z"
  },
  "message": "アラートが正常にインジェストされました"
}
```

### Pydantic バリデーションエラー例（422）

```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "リクエストデータのバリデーションに失敗しました",
    "details": [
      {
        "loc": ["body", "severity"],
        "msg": "value is not a valid enumeration member; permitted: 'critical', 'high', 'medium', 'low'",
        "type": "value_error.enum"
      },
      {
        "loc": ["body", "title"],
        "msg": "field required",
        "type": "value_error.missing"
      }
    ]
  }
}
```

### エラーケース

| ステータス | コード | 説明 |
|-----------|--------|------|
| 401 | `INVALID_TOKEN` | 認証失敗 |
| 403 | `FORBIDDEN` | 権限不足 |
| 422 | `VALIDATION_ERROR` | Pydantic バリデーションエラー |
| 429 | `RATE_LIMIT_EXCEEDED` | レート制限超過 |
