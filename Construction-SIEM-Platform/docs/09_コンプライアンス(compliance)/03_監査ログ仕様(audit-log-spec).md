# 📋 監査ログ仕様

> Construction SIEM Platform の監査ログ記録仕様と運用

---

## 📋 目次

1. [概要](#概要)
2. [記録項目](#記録項目)
3. [保持方式](#保持方式)
4. [API仕様](#api仕様)
5. [除外設定](#除外設定)
6. [運用ガイドライン](#運用ガイドライン)

---

## 🎯 概要

### 監査ログの目的

| 目的 | 説明 |
|------|------|
| 🔍 追跡可能性 | 誰が、いつ、何をしたかの完全な記録 |
| 🛡 否認防止 | 操作の否認を防ぐための証跡 |
| 📜 コンプライアンス | ISO 27001 (A.8.15)、NIST CSF (DE.CM-3) 準拠 |
| 🔬 フォレンジック | インシデント調査時の証拠 |

### アーキテクチャ

```
HTTPリクエスト
    │
    ▼
┌──────────────────┐
│  FastAPI          │
│  ミドルウェア      │ ── 監査ログ記録
│                  │
│  ┌────────────┐  │
│  │AuditLogger │  │
│  │            │  │
│  │ record()   │──┼──► deque(maxlen=10000)  [開発環境]
│  │            │  │
│  │            │──┼──► Elasticsearch        [本番環境]
│  └────────────┘  │
└──────────────────┘
```

---

## 📝 記録項目

### 監査ログレコード構造

| フィールド | 型 | 説明 | 例 |
|-----------|-----|------|-----|
| `timestamp` | `datetime` | 記録日時（UTC） | `2026-03-24T10:30:00.000Z` |
| `user` | `string` | 操作ユーザー名 | `admin` |
| `client_ip` | `string` | クライアントIPアドレス | `192.168.1.100` |
| `method` | `string` | HTTPメソッド | `POST` |
| `path` | `string` | リクエストパス | `/api/v1/events` |
| `status_code` | `integer` | HTTPステータスコード | `200` |
| `processing_time` | `float` | 処理時間（ミリ秒） | `45.2` |
| `user_agent` | `string` | ユーザーエージェント | `curl/8.0` |
| `request_id` | `string` | リクエスト固有ID | `req-abc123` |

### ログレコード例

```json
{
  "timestamp": "2026-03-24T10:30:00.000Z",
  "user": "analyst_tanaka",
  "client_ip": "192.168.1.100",
  "method": "POST",
  "path": "/api/v1/events",
  "status_code": 201,
  "processing_time": 45.2,
  "user_agent": "Mozilla/5.0",
  "request_id": "req-abc123def456"
}
```

### 記録タイミング

```
リクエスト受信
    │
    ├── タイムスタンプ記録（開始）
    ├── ユーザー情報取得（JWT解析）
    ├── クライアントIP取得
    │
    ▼
リクエスト処理
    │
    ▼
レスポンス送信
    │
    ├── ステータスコード記録
    ├── 処理時間計算（終了 - 開始）
    └── 監査ログエントリ保存
```

---

## 💾 保持方式

### 環境別保持設定

| 環境 | ストレージ | 最大件数 | 保持期間 | 永続化 |
|------|-----------|:-------:|:-------:|:-----:|
| 開発 | `deque(maxlen=10000)` | 10,000件 | プロセス寿命 | ❌ |
| ステージング | `deque` + ファイル出力 | 10,000件（メモリ） | 30日（ファイル） | 🔶 |
| 本番 | **Elasticsearch** | 無制限 | ILMポリシーに従う | ✅ |

### 開発環境の保持方式

```python
from collections import deque

class AuditLogger:
    def __init__(self, max_entries=10000):
        self._logs = deque(maxlen=max_entries)

    def record(self, entry: dict):
        self._logs.append(entry)

    def get_logs(self, limit=100, offset=0):
        logs = list(self._logs)
        return logs[offset:offset + limit]
```

> ⚠️ **注意**: 開発環境の `deque` は最大10,000件で、古いエントリは自動的に破棄されます。本番環境では必ず Elasticsearch を使用してください。

### 本番環境のElasticsearch設定

```
インデックス: siem-audit-YYYY.MM.DD
ILMポリシー:
├── Hot:  7日（高速検索）
├── Warm: 30日（圧縮保存）
├── Cold: 365日（アーカイブ）
└── Delete: 365日超（法的要件に応じて延長可能）
```

---

## 🔌 API仕様

### エンドポイント一覧

| メソッド | パス | 説明 | 権限 |
|---------|------|------|:----:|
| `GET` | `/audit/logs` | 監査ログ一覧取得 | 🔴 admin |
| `GET` | `/audit/stats` | 監査ログ統計情報 | 🔴 admin |

### GET /audit/logs

監査ログの一覧を取得します。

**リクエスト**:

| パラメータ | 型 | デフォルト | 説明 |
|-----------|-----|----------|------|
| `limit` | int | 100 | 取得件数 |
| `offset` | int | 0 | オフセット |
| `user` | string | - | ユーザーでフィルタ |
| `method` | string | - | HTTPメソッドでフィルタ |
| `status_code` | int | - | ステータスコードでフィルタ |
| `start_time` | datetime | - | 開始日時 |
| `end_time` | datetime | - | 終了日時 |

**リクエスト例**:

```bash
# 最新100件取得
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  "http://localhost:8000/audit/logs?limit=100"

# ユーザー指定
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  "http://localhost:8000/audit/logs?user=analyst_tanaka&limit=50"

# ステータスコード指定（エラーのみ）
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  "http://localhost:8000/audit/logs?status_code=500"
```

**レスポンス例**:

```json
{
  "total": 5432,
  "offset": 0,
  "limit": 100,
  "logs": [
    {
      "timestamp": "2026-03-24T10:30:00.000Z",
      "user": "analyst_tanaka",
      "client_ip": "192.168.1.100",
      "method": "POST",
      "path": "/api/v1/events",
      "status_code": 201,
      "processing_time": 45.2
    }
  ]
}
```

### GET /audit/stats

監査ログの統計情報を取得します。

**レスポンス例**:

```json
{
  "total_entries": 5432,
  "unique_users": 12,
  "time_range": {
    "earliest": "2026-03-20T00:00:00Z",
    "latest": "2026-03-24T10:30:00Z"
  },
  "by_method": {
    "GET": 3200,
    "POST": 1500,
    "PUT": 500,
    "DELETE": 232
  },
  "by_status": {
    "2xx": 4800,
    "4xx": 580,
    "5xx": 52
  },
  "top_users": [
    { "user": "admin", "count": 2100 },
    { "user": "analyst_tanaka", "count": 1800 },
    { "user": "viewer_suzuki", "count": 1532 }
  ],
  "avg_processing_time_ms": 42.5
}
```

---

## 🚫 除外設定

### 除外エンドポイント

以下のエンドポイントは監査ログに記録されません。

| パス | 除外理由 |
|------|---------|
| `/health` | ヘルスチェック（大量呼び出し） |
| `/health/detailed` | ヘルスチェック（大量呼び出し） |
| `/metrics` | Prometheusスクレイピング（大量呼び出し） |
| `/docs` | Swagger UIアクセス |
| `/openapi.json` | OpenAPIスキーマ |
| `/redoc` | ReDoc UIアクセス |

### 除外理由

```
除外基準:
├── 高頻度の自動呼び出し（監視・ヘルスチェック）
├── 静的コンテンツ（ドキュメントUI）
└── セキュリティ上無関係（公開エンドポイント）

⚠️ 認証・認可が必要なエンドポイントは除外しません
```

---

## 📘 運用ガイドライン

### 定期レビュー

| 頻度 | レビュー内容 | 担当 |
|------|-----------|------|
| 日次 | 異常なアクセスパターン確認 | SOCアナリスト |
| 週次 | 統計レビュー（`/audit/stats`） | SOCリーダー |
| 月次 | 完全性チェック、保持ポリシー確認 | セキュリティ管理者 |
| 四半期 | コンプライアンス監査 | 監査担当者 |

### 異常検知ルール

| ルール | 条件 | アクション |
|--------|------|-----------|
| 🔴 大量エラー | 5xx が 10件/分 超過 | 即座にアラート |
| 🟠 不正アクセス試行 | 401/403 が 50件/分 超過 | SOC通知 |
| 🟡 深夜アクセス | 0:00-5:00 のアクセス | ログ記録・翌日レビュー |
| 🟡 大量データ取得 | 同一ユーザーが100件以上のGET/分 | ログ記録 |

### 監査ログの保護

| 対策 | 内容 |
|------|------|
| アクセス制限 | admin ロールのみ閲覧可能 |
| 改ざん防止 | Elasticsearch の不変インデックス設定（本番） |
| バックアップ | 日次スナップショット |
| 暗号化 | 保存時暗号化（ES設定） |
