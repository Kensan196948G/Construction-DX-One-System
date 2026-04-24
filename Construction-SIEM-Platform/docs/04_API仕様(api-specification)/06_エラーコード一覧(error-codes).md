# ⚠ エラーコード一覧（Error Codes）

> HTTPステータスコードとエラーレスポンスの仕様

---

## 📋 ステータスコード一覧

### ✅ 成功レスポンス（2xx）

| コード | 名称 | 説明 | 使用場面 |
|:------:|------|------|---------|
| 200 | OK | リクエスト成功 | GET, PATCH の正常完了 |
| 201 | Created | リソース作成成功 | POST でのリソース新規作成 |
| 202 | Accepted | 非同期処理受付 | バッチインジェスト等の非同期処理 |

### ❌ クライアントエラー（4xx）

| コード | 名称 | 説明 | 使用場面 |
|:------:|------|------|---------|
| 400 | Bad Request | リクエスト不正 | パラメータ形式エラー、不正なJSON |
| 401 | Unauthorized | 認証失敗 | トークン未指定、期限切れ、不正 |
| 403 | Forbidden | 権限不足 | ロール不足によるアクセス拒否 |
| 404 | Not Found | リソース未存在 | 指定IDのリソースが見つからない |
| 422 | Unprocessable Entity | バリデーションエラー | Pydantic バリデーション失敗 |
| 429 | Too Many Requests | レート制限超過 | 100req/min を超過 |

### 🔴 サーバーエラー（5xx）

| コード | 名称 | 説明 | 使用場面 |
|:------:|------|------|---------|
| 500 | Internal Server Error | サーバー内部エラー | 予期しないサーバー側エラー |

> **注意:** 本番環境では500エラーの詳細情報（スタックトレース等）はレスポンスに含まれません。デバッグ情報はサーバーログにのみ記録されます。

---

## 📦 エラーレスポンス形式

全てのエラーレスポンスは以下の統一フォーマットで返却されます。

```json
{
  "status": "error",
  "error": {
    "code": "ERROR_CODE",
    "message": "人間が読めるエラーメッセージ",
    "details": []
  },
  "meta": {
    "timestamp": "2026-03-24T10:00:00Z",
    "request_id": "req_abc123"
  }
}
```

| フィールド | 型 | 説明 |
|------------|------|------|
| `status` | string | 常に `"error"` |
| `error.code` | string | マシンリーダブルなエラーコード |
| `error.message` | string | 日本語のエラーメッセージ |
| `error.details` | array | 詳細情報（バリデーションエラー時など） |
| `meta.timestamp` | string | エラー発生日時（ISO 8601） |
| `meta.request_id` | string | リクエスト追跡用ID |

---

## 🔍 エラーコード詳細

### 400 Bad Request

| エラーコード | メッセージ | 原因 |
|-------------|----------|------|
| `INVALID_REQUEST` | リクエスト形式が不正です | JSON パースエラー |
| `INVALID_PARAMETER` | パラメータが不正です | クエリパラメータの値が不正 |
| `MISSING_PARAMETER` | 必須パラメータが不足しています | 必須フィールドが未指定 |
| `INVALID_TRANSITION` | 無効なステータス遷移です | インシデントの不正な遷移 |

#### レスポンス例

```json
{
  "status": "error",
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "パラメータが不正です",
    "details": [
      {
        "field": "severity",
        "message": "有効な値は critical, high, medium, low です",
        "provided_value": "urgent"
      }
    ]
  },
  "meta": {
    "timestamp": "2026-03-24T10:00:00Z",
    "request_id": "req_abc123"
  }
}
```

---

### 401 Unauthorized

| エラーコード | メッセージ | 原因 |
|-------------|----------|------|
| `MISSING_TOKEN` | 認証トークンが指定されていません | Authorization ヘッダー未設定 |
| `INVALID_TOKEN` | 認証トークンが不正です | トークンの改ざん・不正形式 |
| `TOKEN_EXPIRED` | 認証トークンの有効期限が切れています | 30分の有効期限超過 |
| `INVALID_CREDENTIALS` | ユーザー名またはパスワードが不正です | ログイン認証失敗 |

#### レスポンス例

```json
{
  "status": "error",
  "error": {
    "code": "TOKEN_EXPIRED",
    "message": "認証トークンの有効期限が切れています。再度ログインしてください。"
  },
  "meta": {
    "timestamp": "2026-03-24T10:00:00Z",
    "request_id": "req_def456"
  }
}
```

---

### 403 Forbidden

| エラーコード | メッセージ | 原因 |
|-------------|----------|------|
| `FORBIDDEN` | このリソースへのアクセス権限がありません | ロール不足 |
| `INSUFFICIENT_PERMISSIONS` | 必要な権限が不足しています | 特定のパーミッション不足 |

#### レスポンス例

```json
{
  "status": "error",
  "error": {
    "code": "FORBIDDEN",
    "message": "このエンドポイントにはadmin権限が必要です",
    "details": {
      "required_role": "admin",
      "current_role": "viewer",
      "required_permission": "users:manage"
    }
  },
  "meta": {
    "timestamp": "2026-03-24T10:00:00Z",
    "request_id": "req_ghi789"
  }
}
```

---

### 404 Not Found

| エラーコード | メッセージ | 原因 |
|-------------|----------|------|
| `NOT_FOUND` | 指定されたリソースが見つかりません | IDに対応するリソースなし |
| `ENDPOINT_NOT_FOUND` | エンドポイントが見つかりません | 存在しないパス |

#### レスポンス例

```json
{
  "status": "error",
  "error": {
    "code": "NOT_FOUND",
    "message": "指定されたアラートが見つかりません",
    "details": {
      "resource": "alert",
      "id": "alert-999"
    }
  },
  "meta": {
    "timestamp": "2026-03-24T10:00:00Z",
    "request_id": "req_jkl012"
  }
}
```

---

### 422 Unprocessable Entity

| エラーコード | メッセージ | 原因 |
|-------------|----------|------|
| `VALIDATION_ERROR` | バリデーションエラーが発生しました | Pydantic モデルの検証失敗 |

#### レスポンス例

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
        "msg": "ensure this value has at most 200 characters",
        "type": "value_error.any_str.max_length"
      }
    ]
  },
  "meta": {
    "timestamp": "2026-03-24T10:00:00Z",
    "request_id": "req_mno345"
  }
}
```

---

### 429 Too Many Requests

| エラーコード | メッセージ | 原因 |
|-------------|----------|------|
| `RATE_LIMIT_EXCEEDED` | レート制限を超過しました | 100req/min 超過 |

#### レスポンス例

```json
{
  "status": "error",
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "レート制限を超過しました。しばらく待ってから再試行してください。",
    "details": {
      "limit": 100,
      "window": "1 minute",
      "retry_after_seconds": 32
    }
  },
  "meta": {
    "timestamp": "2026-03-24T10:00:00Z",
    "request_id": "req_pqr678"
  }
}
```

#### レスポンスヘッダー

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 32
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1700000032
```

---

### 500 Internal Server Error

| エラーコード | メッセージ | 原因 |
|-------------|----------|------|
| `INTERNAL_ERROR` | サーバー内部エラーが発生しました | 予期しないエラー |

#### レスポンス例（本番環境）

```json
{
  "status": "error",
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "サーバー内部エラーが発生しました。管理者に連絡してください。"
  },
  "meta": {
    "timestamp": "2026-03-24T10:00:00Z",
    "request_id": "req_stu901"
  }
}
```

> **本番環境のセキュリティ:** スタックトレースやデバッグ情報はレスポンスに含まれません。`request_id` を使用してサーバーログから詳細を確認してください。

#### レスポンス例（開発環境のみ）

```json
{
  "status": "error",
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "サーバー内部エラーが発生しました",
    "debug": {
      "exception": "ConnectionError",
      "detail": "Elasticsearch connection refused",
      "traceback": "..."
    }
  }
}
```

---

## 📊 エラーコード早見表

| HTTP | コード | 対処方法 |
|:----:|--------|---------|
| 400 | `INVALID_REQUEST` | リクエスト形式を確認 |
| 400 | `INVALID_PARAMETER` | パラメータ値を確認 |
| 400 | `MISSING_PARAMETER` | 必須フィールドを追加 |
| 400 | `INVALID_TRANSITION` | ステータス遷移ルールを確認 |
| 401 | `MISSING_TOKEN` | Authorization ヘッダーを設定 |
| 401 | `INVALID_TOKEN` | トークンを再取得 |
| 401 | `TOKEN_EXPIRED` | `/auth/token` で再ログイン |
| 401 | `INVALID_CREDENTIALS` | ユーザー名・パスワードを確認 |
| 403 | `FORBIDDEN` | 管理者に権限付与を依頼 |
| 404 | `NOT_FOUND` | リソースIDを確認 |
| 422 | `VALIDATION_ERROR` | details フィールドで原因を特定 |
| 429 | `RATE_LIMIT_EXCEEDED` | Retry-After 秒後に再試行 |
| 500 | `INTERNAL_ERROR` | request_id を添えて管理者に報告 |
