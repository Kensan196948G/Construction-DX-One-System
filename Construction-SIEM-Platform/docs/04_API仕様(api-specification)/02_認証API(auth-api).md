# 🔐 認証API（Auth API）

> JWT Bearer Token による認証エンドポイント仕様

---

## 📋 エンドポイント一覧

| メソッド | パス | 認証 | 説明 |
|----------|------|------|------|
| `POST` | `/api/v1/auth/token` | 不要 | トークン発行 |
| `GET` | `/api/v1/auth/me` | 必要 | ユーザー情報取得 |
| `GET` | `/api/v1/auth/roles` | 必要（admin） | ロール一覧取得 |

---

## 1️⃣ POST /api/v1/auth/token — トークン発行

### 概要

| 項目 | 値 |
|------|------|
| メソッド | `POST` |
| パス | `/api/v1/auth/token` |
| 認証要件 | **不要**（このエンドポイントで認証情報を取得する） |
| Content-Type | `application/x-www-form-urlencoded` |

### リクエストボディ

| フィールド | 型 | 必須 | 説明 |
|------------|------|------|------|
| `username` | string | ✅ | ユーザー名 |
| `password` | string | ✅ | パスワード |
| `grant_type` | string | ❌ | `password`（デフォルト） |

### リクエスト例

```http
POST /api/v1/auth/token HTTP/1.1
Host: siem.example.com
Content-Type: application/x-www-form-urlencoded

username=admin&password=SecureP@ss123
```

### レスポンス例（200 OK）

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTcwMDAwMTgwMH0.xxxxx",
  "token_type": "bearer",
  "expires_in": 1800,
  "role": "admin"
}
```

### JWTペイロード構造

```json
{
  "sub": "admin",
  "role": "admin",
  "exp": 1700001800,
  "iat": 1700000000
}
```

### エラーケース

| ステータス | コード | 説明 |
|-----------|--------|------|
| 400 | `INVALID_REQUEST` | リクエスト形式が不正 |
| 401 | `INVALID_CREDENTIALS` | ユーザー名またはパスワードが不正 |
| 429 | `RATE_LIMIT_EXCEEDED` | ログイン試行回数超過（5回/分） |

#### エラーレスポンス例（401）

```json
{
  "status": "error",
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "ユーザー名またはパスワードが正しくありません"
  }
}
```

---

## 2️⃣ GET /api/v1/auth/me — ユーザー情報取得

### 概要

| 項目 | 値 |
|------|------|
| メソッド | `GET` |
| パス | `/api/v1/auth/me` |
| 認証要件 | **必要**（Bearer Token） |
| 必要ロール | 全ロール |

### リクエスト例

```http
GET /api/v1/auth/me HTTP/1.1
Host: siem.example.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### レスポンス例（200 OK）

```json
{
  "status": "success",
  "data": {
    "username": "admin",
    "role": "admin",
    "permissions": [
      "alerts:read",
      "alerts:write",
      "alerts:acknowledge",
      "incidents:read",
      "incidents:write",
      "incidents:delete",
      "users:manage",
      "audit:read",
      "settings:manage"
    ],
    "last_login": "2026-03-24T09:30:00Z",
    "created_at": "2026-01-01T00:00:00Z"
  }
}
```

### ロール別権限マトリクス

| 権限 | admin | analyst | viewer |
|------|:-----:|:-------:|:------:|
| alerts:read | ✅ | ✅ | ✅ |
| alerts:write | ✅ | ✅ | ❌ |
| alerts:acknowledge | ✅ | ✅ | ❌ |
| incidents:read | ✅ | ✅ | ✅ |
| incidents:write | ✅ | ✅ | ❌ |
| incidents:delete | ✅ | ❌ | ❌ |
| users:manage | ✅ | ❌ | ❌ |
| audit:read | ✅ | ✅ | ❌ |
| settings:manage | ✅ | ❌ | ❌ |

### エラーケース

| ステータス | コード | 説明 |
|-----------|--------|------|
| 401 | `TOKEN_EXPIRED` | トークンの有効期限切れ |
| 401 | `INVALID_TOKEN` | トークンが不正または改ざんされている |

---

## 3️⃣ GET /api/v1/auth/roles — ロール一覧取得

### 概要

| 項目 | 値 |
|------|------|
| メソッド | `GET` |
| パス | `/api/v1/auth/roles` |
| 認証要件 | **必要**（Bearer Token） |
| 必要ロール | **admin のみ** |

### リクエスト例

```http
GET /api/v1/auth/roles HTTP/1.1
Host: siem.example.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### レスポンス例（200 OK）

```json
{
  "status": "success",
  "data": {
    "roles": [
      {
        "name": "admin",
        "description": "システム管理者（全権限）",
        "permissions": ["*"],
        "user_count": 2
      },
      {
        "name": "analyst",
        "description": "セキュリティアナリスト（分析・対応）",
        "permissions": [
          "alerts:read",
          "alerts:write",
          "alerts:acknowledge",
          "incidents:read",
          "incidents:write",
          "audit:read"
        ],
        "user_count": 5
      },
      {
        "name": "viewer",
        "description": "閲覧専用ユーザー",
        "permissions": [
          "alerts:read",
          "incidents:read"
        ],
        "user_count": 10
      }
    ]
  }
}
```

### エラーケース

| ステータス | コード | 説明 |
|-----------|--------|------|
| 401 | `INVALID_TOKEN` | トークンが不正 |
| 403 | `FORBIDDEN` | admin ロール以外のアクセス |

#### エラーレスポンス例（403）

```json
{
  "status": "error",
  "error": {
    "code": "FORBIDDEN",
    "message": "このエンドポイントにはadmin権限が必要です"
  }
}
```

---

## 🔑 セキュリティに関する注意事項

| 項目 | 推奨事項 |
|------|---------|
| トークン保管 | クライアント側でセキュアに保管（httpOnly Cookie 推奨） |
| パスワードポリシー | 最低12文字、大小文字・数字・記号を含む |
| ブルートフォース対策 | 5回/分のログイン試行制限 |
| トークン有効期限 | 30分（環境変数 `JWT_EXPIRATION` で変更可能） |
| HTTPS | 本番環境では必須 |
