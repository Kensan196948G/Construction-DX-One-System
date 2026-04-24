# 📡 API概要（API Overview）

> Construction SIEM Platform REST API v2.0.0 仕様概要

---

## 📋 基本情報

| 項目 | 値 |
|------|------|
| ベースURL | `/api/v1` |
| APIバージョン | `2.0.0` |
| プロトコル | HTTPS（本番環境必須） |
| レスポンス形式 | JSON（`Content-Type: application/json`） |
| 文字コード | UTF-8 |

---

## 🔐 認証方式

| 項目 | 詳細 |
|------|------|
| 方式 | JWT Bearer Token |
| ヘッダー | `Authorization: Bearer <token>` |
| トークン有効期限 | 30分（デフォルト） |
| リフレッシュ | `/api/v1/auth/token` で再発行 |

### 認証フロー

```
1. POST /api/v1/auth/token にユーザー名・パスワードを送信
2. JWT トークンを取得
3. 以降のリクエストに Authorization ヘッダーを付与
```

**リクエスト例:**

```http
GET /api/v1/alerts HTTP/1.1
Host: siem.example.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```

---

## ⏱ レート制限

Construction SIEM Platform は **2種類** のレート制限を実装しています。

### IPベースレート制限（全エンドポイント共通）

| 項目 | 値 |
|------|------|
| 制限方式 | IPアドレスベース（固定ウィンドウ方式） |
| 制限値 | **100リクエスト/分** |
| ヘッダー | `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` |
| 超過時 | HTTP 429 Too Many Requests |

#### レスポンスヘッダー例

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1700000000
```

### APIキーベースレート制限（Phase 36+）

APIキー認証エンドポイント（`/api-keys/{id}/verify`）には**個別レート制限**が適用されます。

| 項目 | 値 |
|------|------|
| 制限方式 | APIキーIDベース（固定ウィンドウ方式） |
| デフォルト制限値 | **60リクエスト/分** |
| ストレージ | メモリ内（LRU近似、上限10000エントリ） |
| GC | 確率的クリーンアップ（p=0.01、5分TTL） |
| 管理API | `GET /api-keys/rate-limit/stats`, `POST /api-keys/rate-limit/cleanup` |
| ヘッダー | `X-APIKey-RateLimit-Limit`, `X-APIKey-RateLimit-Remaining`, `X-APIKey-RateLimit-Reset` |
| 超過時 | HTTP 429 Too Many Requests |

#### APIキーレート制限ヘッダー例

```http
X-APIKey-RateLimit-Limit: 60
X-APIKey-RateLimit-Remaining: 45
X-APIKey-RateLimit-Reset: 1700000060
```

---

## 📦 レスポンス形式

### 成功レスポンス

```json
{
  "status": "success",
  "data": { ... },
  "meta": {
    "total": 150,
    "page": 1,
    "per_page": 20,
    "timestamp": "2026-03-24T10:00:00Z"
  }
}
```

### エラーレスポンス

```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "リクエストパラメータが不正です",
    "details": [
      {
        "field": "severity",
        "message": "有効な値は critical, high, medium, low です"
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

## 🔗 エンドポイント一覧

| カテゴリ | プレフィックス | 説明 |
|----------|---------------|------|
| 🔐 認証 | `/api/v1/auth/*` | トークン発行・ユーザー情報 |
| 🚨 アラート | `/api/v1/alerts/*` | アラート管理・インジェスト |
| 📋 インシデント | `/api/v1/incidents/*` | インシデント管理・統計 |
| 🛡 脅威インテリジェンス | `/api/v1/threat-intel/*` | IoC管理・照合 |
| 🔗 相関分析 | `/api/v1/correlation/*` | MITRE ATT&CK分析 |
| 📊 KPI | `/api/v1/kpi/*` | MTTD/MTTR/SLAダッシュボード |
| ✅ コンプライアンス | `/api/v1/compliance/*` | ISO27001/NIST CSF |
| 📥 データ検証 | `/api/v1/data/*` | バリデーション・バッチインジェスト |
| 🔔 通知 | `/api/v1/notifications/*` | Teams/Slack/Webhook |
| 📝 監査 | `/api/v1/audit/*` | 監査ログ・統計 |
| 🔑 APIキー管理 | `/api-keys/*` | APIキーCRUD・スコープ管理・レート制限（Phase 35-37） |
| 🤖 SOAR自動化 | `/ueba/soar/*` | プレイブック自動実行・インシデント連携（Phase 32） |
| 👁 UEBA | `/ueba/*` | ユーザー行動分析・異常検知（Phase 30-31） |

---

## 📖 APIドキュメント（インタラクティブ）

| ツール | URL | 説明 |
|--------|-----|------|
| 🟢 Swagger UI | `/api/docs` | インタラクティブなAPI実行環境 |
| 🔵 ReDoc | `/api/redoc` | 見やすいリファレンス形式 |
| 📄 OpenAPI JSON | `/api/openapi.json` | OpenAPI 3.0 スキーマ定義 |

---

## 🏗 共通パラメータ

### ページネーション

| パラメータ | 型 | デフォルト | 説明 |
|------------|------|-----------|------|
| `page` | int | 1 | ページ番号 |
| `per_page` | int | 20 | 1ページあたりの件数（最大100） |
| `sort` | string | `-created_at` | ソート項目（`-` で降順） |

### フィルタリング

クエリパラメータでフィルタリングが可能です。各エンドポイントで利用可能なフィルターは個別仕様を参照してください。

### 日時形式

全ての日時は **ISO 8601** 形式（`YYYY-MM-DDTHH:mm:ssZ`）で統一されています。

---

## 🔄 バージョニング

APIバージョンはURLパスに含まれます（`/api/v1`）。メジャーバージョンアップ時は新しいパス（`/api/v2`）が追加され、旧バージョンは非推奨期間（6ヶ月）の後に廃止されます。
