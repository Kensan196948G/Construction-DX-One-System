# 🔐 セキュリティ設計

> Construction SIEM Platform のセキュリティアーキテクチャと実装方針

---

## 📋 目次

1. [多層防御アーキテクチャ](#多層防御アーキテクチャ)
2. [JWT認証](#jwt認証)
3. [RBAC認可](#rbac認可)
4. [レート制限](#レート制限)
5. [APIキー認証](#apiキー認証)
6. [Webhook HMAC-SHA256署名](#webhook-hmac-sha256署名)
7. [入力検証](#入力検証)
8. [情報漏洩防止](#情報漏洩防止)
9. [パスワード管理](#パスワード管理)

---

## 🏰 多層防御アーキテクチャ

本プラットフォームは**多層防御（Defense in Depth）**の原則に基づき、以下の7層でセキュリティを確保します。

```
┌─────────────────────────────────────────────┐
│  Layer 1: 認証（Authentication）            │  JWT / APIキー / LDAP
├─────────────────────────────────────────────┤
│  Layer 2: 認可（Authorization）             │  RBAC ロール判定・スコープ
├─────────────────────────────────────────────┤
│  Layer 3: レート制限（Rate Limiting）       │  IP: 100/min・APIキー: 60/min
├─────────────────────────────────────────────┤
│  Layer 4: Webhook署名検証                   │  HMAC-SHA256 + タイムスタンプ
├─────────────────────────────────────────────┤
│  Layer 5: 入力検証（Input Validation）      │  Pydantic バリデーション
├─────────────────────────────────────────────┤
│  Layer 6: 情報漏洩防止                      │  シークレットハッシュ化・非返却
├─────────────────────────────────────────────┤
│  Layer 7: 監査ログ（Audit Logging）         │  全操作記録（ISO27001 A.8.15）
└─────────────────────────────────────────────┘
```

| 層 | 防御対象 | 実装技術 | 失敗時の挙動 |
|:---:|----------|----------|-------------|
| 1 | なりすまし | JWT (HS256) / APIキー SHA-256 | `401 Unauthorized` |
| 2 | 権限昇格 | RBAC (3ロール) / スコープ制御 | `403 Forbidden` |
| 3 | DoS攻撃 | SlowAPI (IP) + 固定ウィンドウ (APIキー) | `429 Too Many Requests` |
| 4 | Webhook偽装 | HMAC-SHA256 署名 + 300秒タイムスタンプ | 署名不一致で処理拒否 |
| 5 | インジェクション | Pydantic Field | `422 Validation Error` |
| 6 | 情報漏洩 | APIキープレーンテキスト非保存 | — |
| 7 | 否認 | 監査ログ | ログ記録（非ブロッキング） |

---

## 🔑 JWT認証

### 基本設定

| 項目 | 値 | 設定方法 |
|------|-----|---------|
| アルゴリズム | HS256 | 固定 |
| 秘密鍵 | 環境変数 `JWT_SECRET_KEY` | `.env` ファイル |
| 有効期限 | 60分（デフォルト） | 環境変数 `ACCESS_TOKEN_EXPIRE_MINUTES` |
| トークン形式 | Bearer Token | `Authorization` ヘッダー |

### 認証フロー

```
クライアント                    サーバー
    │                              │
    │  POST /auth/token            │
    │  (username + password)       │
    ├─────────────────────────────►│
    │                              │  ユーザー検証
    │                              │  JWT生成
    │  200 OK                      │
    │  {access_token, token_type}  │
    │◄─────────────────────────────┤
    │                              │
    │  GET /api/v1/events          │
    │  Authorization: Bearer xxx   │
    ├─────────────────────────────►│
    │                              │  JWT検証
    │                              │  ロール確認
    │  200 OK / 401 / 403          │
    │◄─────────────────────────────┤
```

### トークンペイロード

```json
{
  "sub": "username",
  "role": "analyst",
  "exp": 1700000000
}
```

---

## 👥 RBAC認可

### ロール定義

| ロール | 説明 | 権限 |
|--------|------|------|
| 🔴 `admin` | システム管理者 | 全権限（設定変更、ユーザー管理、監査ログ閲覧） |
| 🟡 `analyst` | セキュリティアナリスト | `read` / `write` / `execute_playbook` |
| 🟢 `viewer` | 閲覧ユーザー | `read` のみ |

### 権限マトリクス

| 操作 | admin | analyst | viewer |
|------|:-----:|:-------:|:------:|
| イベント閲覧 | ✅ | ✅ | ✅ |
| イベント作成 | ✅ | ✅ | ❌ |
| プレイブック実行 | ✅ | ✅ | ❌ |
| ルール管理 | ✅ | ✅ | ❌ |
| IoC管理 | ✅ | ✅ | ❌ |
| ユーザー管理 | ✅ | ❌ | ❌ |
| 監査ログ閲覧 | ✅ | ❌ | ❌ |
| システム設定 | ✅ | ❌ | ❌ |
| コンプライアンスチェック | ✅ | ❌ | ❌ |

### 実装方式

```python
# ロールベースの依存関数
def require_role(required_roles: list[str]):
    def role_checker(current_user = Depends(get_current_user)):
        if current_user.role not in required_roles:
            raise HTTPException(status_code=403)
        return current_user
    return role_checker

# 使用例
@router.get("/audit/logs")
async def get_audit_logs(user = Depends(require_role(["admin"]))):
    ...
```

---

## ⏱ レート制限

### 設定

| 項目 | 値 | 備考 |
|------|-----|------|
| 制限値 | 100 リクエスト/分/IP | 環境変数 `RATE_LIMIT_PER_MINUTE` |
| ライブラリ | SlowAPI | Starlette ベース |
| キー | クライアントIPアドレス | `get_remote_address` |
| レスポンス | `429 Too Many Requests` | `Retry-After` ヘッダー付き |

### 超過時のレスポンス

```json
{
  "detail": "Rate limit exceeded. Try again in 60 seconds.",
  "retry_after": 60
}
```

---

## ✅ 入力検証

### Pydantic Field バリデーション

| フィールド | バリデーション | 例 |
|-----------|---------------|-----|
| `severity` | `ge=1, le=10` | 1〜10の整数 |
| `event_type` | `max_length=100` | 最大100文字 |
| `source_ip` | IPv4形式チェック | `192.168.1.1` |
| `description` | `max_length=5000` | 最大5000文字 |
| `username` | `min_length=3, max_length=50` | 3〜50文字 |

### バリデーションエラーレスポンス

```json
{
  "detail": [
    {
      "loc": ["body", "severity"],
      "msg": "ensure this value is less than or equal to 10",
      "type": "value_error.number.not_le"
    }
  ]
}
```

---

## 🛡 情報漏洩防止

### 環境別エラーレスポンス

| 環境 | 例外詳細 | スタックトレース |
|------|---------|----------------|
| 開発 (`development`) | 表示 | 表示 |
| ステージング (`staging`) | 表示 | 非表示 |
| 本番 (`production`) | **非表示** | **非表示** |

### 本番環境のエラーレスポンス

```json
{
  "detail": "Internal server error. Please contact the administrator."
}
```

---

## 🔒 パスワード管理

### 現在の実装

| 項目 | 内容 |
|------|------|
| ハッシュアルゴリズム | SHA-256 |
| ソルト | ユーザー固有のランダムソルト |
| 保存形式 | `salt:hashed_password` |
| 最小長 | 8文字 |

### 本番環境への移行計画

```
現在: SHA-256 + salt（ローカル認証）
  ↓
Phase 16: Entra ID / LDAP 連携
  ↓
将来: SSO / MFA 対応
```

> ⚠️ **注意**: 現在のパスワード管理はPoC段階の実装です。本番環境では必ず Entra ID または LDAP に移行してください。

---

## 🔑 APIキー認証（Phase 34+）

サービス間通信・外部システム連携のための機械向け認証機構。

### 設計原則

| 項目 | 内容 |
|------|------|
| キー生成 | `secrets.token_urlsafe(32)` — 256bit エントロピー |
| 保存形式 | **SHA-256 ハッシュのみ**（プレーンテキスト非保存） |
| 表示形式 | `siem_{先頭8文字}...` プレフィックス付き |
| スコープ | `read` / `write` / `admin`（階層制御） |
| 削除方式 | 論理削除（`is_active=False`）— 監査証跡保持 |
| レート制限 | **60リクエスト/分/キー**（固定ウィンドウ） |

### セキュリティ上の留意点

- APIキーのプレーンテキストは**作成時一度のみ**返却（再表示不可）
- ローテーション時は旧キーを即座に無効化し新キーを発行
- SHA-256ハッシュ比較で定数時間比較（タイミング攻撃防止）

---

## 📡 Webhook HMAC-SHA256署名（Phase 35+）

外部システムへのイベント通知を改ざんから保護するための署名機構。

### 署名アルゴリズム

```
payload_bytes = JSON.encode(payload)
signature = HMAC-SHA256(key=WEBHOOK_SECRET, msg=payload_bytes)
header = "sha256=" + hex(signature)
```

### 受信側の検証手順

1. `X-SIEM-Signature` ヘッダーを取得
2. ローカルで同じ秘密鍵・ペイロードでHMAC-SHA256を計算
3. `hmac.compare_digest()` で定数時間比較（タイミング攻撃防止）
4. タイムスタンプを確認（300秒以内のリクエストのみ受理）

### セキュリティ要件

| 項目 | 要件 |
|------|------|
| 秘密鍵 | `WEBHOOK_SECRET` 環境変数に 256bit ランダム値を設定 |
| 生成コマンド | `openssl rand -hex 32` |
| タイムスタンプ検証 | ±300秒以内（リプレイアタック防止） |
| 比較方式 | `hmac.compare_digest()` 必須（タイミング攻撃防止） |

---

## 📊 セキュリティ設定一覧

| 環境変数 | デフォルト値 | 説明 |
|----------|------------|------|
| `JWT_SECRET_KEY` | (必須) | JWT署名用秘密鍵 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | トークン有効期限（分） |
| `RATE_LIMIT_PER_MINUTE` | `100` | IPベースレート制限（リクエスト/分） |
| `WEBHOOK_SECRET` | (必須) | Webhook HMAC-SHA256署名秘密鍵 |
| `PASSWORD_SALT` | (必須) | パスワードハッシュ用ソルト |
| `ENVIRONMENT` | `development` | 実行環境（development/staging/production） |
| `CORS_ORIGINS` | `http://localhost:3000` | CORS許可オリジン（本番では明示的に設定） |
