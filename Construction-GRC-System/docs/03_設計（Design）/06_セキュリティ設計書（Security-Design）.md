# セキュリティ設計書（Security Design）

## 建設業 統合リスク＆コンプライアンス管理システム（Construction-GRC-System）

| 項目 | 内容 |
|------|------|
| **文書番号** | DES-GRC-006 |
| **バージョン** | 1.0.0 |
| **作成日** | 2026-03-26 |
| **最終更新日** | 2026-03-26 |
| **作成者** | みらい建設工業 IT部門 |
| **準拠規格** | ISO27001:2022 / NIST CSF 2.0 |
| **関連文書** | DES-GRC-001（システムアーキテクチャ設計書）、REQ-GRC-003（非機能要件一覧） |

---

## 改訂履歴

| バージョン | 日付 | 変更内容 | 変更者 |
|-----------|------|---------|--------|
| 1.0.0 | 2026-03-26 | 初版作成 | IT部門 |

---

## 1. セキュリティ設計方針

### 1.1 基本原則

| 原則 | 説明 | 関連管理策 |
|------|------|----------|
| セキュリティバイデザイン | 設計段階からセキュリティを組み込む | A.8.25, A.8.26 |
| 多層防御（Defense in Depth） | ネットワーク/アプリ/データの各層で防御 | A.8.20 |
| 最小権限の原則 | 必要最小限の権限のみ付与 | A.5.15, A.8.3 |
| ゼロトラスト | 全通信を検証、暗黙の信頼を排除 | A.5.14 |
| 監査可能性 | 全操作のログ記録、追跡可能性の確保 | A.8.15 |

### 1.2 準拠するISO27001管理策

| 管理策 | タイトル | 本設計での対応 |
|--------|---------|-------------|
| A.5.15 | アクセス制御 | RBAC（7ロール） |
| A.5.17 | 認証情報 | JWT + MFA（TOTP） |
| A.8.3 | 情報アクセス制限 | Row Level Security |
| A.8.5 | セキュアな認証 | 多要素認証 |
| A.8.9 | 構成管理 | Docker構成管理 |
| A.8.15 | ログ記録 | 全操作監査ログ |
| A.8.20 | ネットワークセキュリティ | TLS 1.3, WAF |
| A.8.24 | 暗号の使用 | TLS + AES-256 |
| A.8.25 | セキュアな開発ライフサイクル | SAST/DAST, コードレビュー |
| A.8.26 | アプリケーションセキュリティ | OWASP Top 10対策 |
| A.8.28 | セキュアコーディング | Python/JS セキュアコーディング規約 |

---

## 2. 認証設計（Authentication）

### 2.1 認証方式

| 項目 | 仕様 |
|------|------|
| 方式 | JWT（JSON Web Token）+ MFA（TOTP） |
| アクセストークン有効期限 | 30分 |
| リフレッシュトークン有効期限 | 7日 |
| 署名アルゴリズム | RS256（RSA 2048bit） |
| トークン格納場所 | フロントエンド: メモリ（XSS対策）、リフレッシュ: httpOnly Cookie |
| MFA方式 | TOTP（RFC 6238、30秒間隔、6桁） |
| MFA適用範囲 | system_admin/grc_admin: 必須、他ロール: 推奨 |

### 2.2 JWT Payload構造

```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "username": "tanaka",
  "role": "grc_admin",
  "department_id": "...",
  "permissions": ["risk:read", "risk:write", "control:read", "control:write"],
  "iat": 1711418400,
  "exp": 1711420200,
  "jti": "unique-token-id"
}
```

### 2.3 パスワードポリシー

| 項目 | 要件 |
|------|------|
| 最小文字数 | 12文字 |
| 最大文字数 | 128文字 |
| 複雑性 | 大文字/小文字/数字/特殊文字を各1文字以上 |
| パスワード履歴 | 直近12世代の再利用禁止 |
| 有効期間 | 90日（変更強制） |
| 辞書チェック | 一般的パスワード20万語リストとの照合 |
| ハッシュ方式 | bcrypt（コストファクター12） |

### 2.4 アカウントロック

| 項目 | 設定値 |
|------|--------|
| ロック閾値 | 5回連続認証失敗 |
| ロック期間 | 30分（自動解除） |
| IPベースレートリミット | 10回/分 |
| ロック時通知 | システム管理者に通知 |
| ブルートフォース検知 | 同一IPから異なるアカウントへの試行を検知 |

### 2.5 セッション管理

| 項目 | 設定値 |
|------|--------|
| アイドルタイムアウト | 30分 |
| 最大セッション時間 | 8時間 |
| 同時セッション上限 | 3セッション/ユーザー |
| セッション固定攻撃対策 | ログイン時にセッションID再生成 |
| セッション保存場所 | Redis（暗号化） |
| ログアウト時処理 | トークン無効化（Redisブラックリスト） |

---

## 3. 認可設計（Authorization）

### 3.1 RBAC（ロールベースアクセス制御）

#### ロール定義

| ロール | 権限レベル | 説明 |
|--------|-----------|------|
| system_admin | 最高 | システム全体の管理 |
| grc_admin | 高 | GRC全機能の管理 |
| risk_owner | 中（限定） | 担当リスクの管理 |
| compliance_officer | 中（限定） | コンプライアンス業務 |
| auditor | 中（限定） | 監査業務 |
| executive | 低（閲覧） | ダッシュボード・レポート閲覧 |
| general_user | 最低（限定） | 割当チェックリスト回答のみ |

#### 権限マトリクス

| リソース | system_admin | grc_admin | risk_owner | compliance_officer | auditor | executive | general_user |
|---------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| ユーザー管理 | CRUD | R | - | - | - | - | - |
| システム設定 | CRUD | R | - | - | - | - | - |
| 監査ログ | R | R | - | - | R | - | - |
| リスク | CRUD | CRUD | CRU* | R | R | R | - |
| コンプライアンス | CRUD | CRUD | R | CRU | R | R | CRU** |
| 管理策 | CRUD | CRUD | R | CRU | R | R | - |
| 監査 | CRUD | CRUD | R | R | CRUD | R | - |
| レポート | CRUD | CRUD | R | R | R | R | - |
| 通知 | CRUD | CRUD | R | R | R | R | R |

- CRU*: 担当リスクのみ
- CRU**: 割り当てられたチェックリスト項目のみ

### 3.2 データレベルアクセス制御

```python
# Row Level Security実装例

class RiskQuerySet(models.QuerySet):
    def for_user(self, user):
        """ユーザーのロールに応じたフィルタリング"""
        if user.role.name in ('system_admin', 'grc_admin'):
            return self.all()
        elif user.role.name == 'risk_owner':
            return self.filter(risk_owner=user)
        elif user.role.name in ('auditor', 'compliance_officer'):
            return self.filter(is_deleted=False)
        elif user.role.name == 'executive':
            return self.filter(is_deleted=False)
        else:
            return self.none()
```

### 3.3 APIレベル権限制御

```python
# DRF Permission Classes

class RiskPermission(BasePermission):
    def has_permission(self, request, view):
        role = request.user.role.name
        if request.method in SAFE_METHODS:
            return role in ('system_admin', 'grc_admin', 'risk_owner',
                           'compliance_officer', 'auditor', 'executive')
        return role in ('system_admin', 'grc_admin', 'risk_owner')

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        role = request.user.role.name
        if role in ('system_admin', 'grc_admin'):
            return True
        if role == 'risk_owner':
            return obj.risk_owner == request.user
        return False
```

---

## 4. 通信暗号化

### 4.1 TLS設定

| 項目 | 設定値 |
|------|--------|
| プロトコル | TLS 1.3（最低TLS 1.2） |
| 暗号スイート | TLS_AES_256_GCM_SHA384, TLS_CHACHA20_POLY1305_SHA256 |
| 証明書 | Let's Encrypt（開発）/ Azure証明書（本番） |
| HSTS | max-age=31536000; includeSubDomains; preload |
| HTTP→HTTPS | 自動リダイレクト（301） |

### 4.2 Nginx TLS設定

```nginx
server {
    listen 443 ssl http2;
    server_name grc.example.com;

    ssl_certificate /etc/ssl/certs/grc.crt;
    ssl_certificate_key /etc/ssl/private/grc.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers on;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_stapling on;
    ssl_stapling_verify on;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
}
```

---

## 5. データ暗号化

### 5.1 保存データ暗号化

| 対象 | 方式 | 鍵管理 |
|------|------|--------|
| データベース全体 | PostgreSQL TDE | Azure Key Vault |
| PII（個人情報） | django-encrypted-model-fields (AES-256-GCM) | Azure Key Vault |
| パスワード | bcrypt（コストファクター12） | ソルト自動生成 |
| MFAシークレット | AES-256-GCM（アプリレベル暗号化） | Azure Key Vault |
| 証跡ファイル | Azure Blob Storage SSE（AES-256） | Azure管理 |
| バックアップ | AES-256 | Azure Key Vault |
| Redisデータ | Redis TLS + at-rest暗号化 | Azure管理 |

### 5.2 暗号化フィールド

```python
from encrypted_model_fields.fields import EncryptedCharField, EncryptedEmailField

class User(AbstractBaseUser):
    # 暗号化対象フィールド
    email = EncryptedEmailField()
    mfa_secret = EncryptedCharField(max_length=32, blank=True)
    # 通常フィールド
    username = models.CharField(max_length=150, unique=True)
    full_name = models.CharField(max_length=200)
```

---

## 6. 監査ログ設計

### 6.1 記録対象イベント

| イベントカテゴリ | 記録項目 | 保管期間 |
|---------------|---------|---------|
| 認証 | ログイン成功/失敗、ログアウト、MFA検証、パスワード変更 | 5年 |
| データ操作 | CRUD操作（変更前後値含む） | 5年 |
| 権限変更 | ロール変更、権限付与/剥奪 | 無期限 |
| ファイル操作 | アップロード、ダウンロード、削除 | 5年 |
| レポート出力 | レポート種別、出力者、日時 | 5年 |
| システム設定 | 設定変更（前後値） | 無期限 |
| セキュリティイベント | アカウントロック、不正アクセス検知 | 無期限 |

### 6.2 ログエントリ構造

```json
{
  "id": "uuid",
  "timestamp": "2026-03-26T10:30:00.000+09:00",
  "event_type": "data_update",
  "severity": "info",
  "user": {
    "id": "uuid",
    "username": "tanaka",
    "role": "grc_admin"
  },
  "session": {
    "id": "session-uuid",
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0..."
  },
  "resource": {
    "type": "risk",
    "id": "RISK-IT-001"
  },
  "action": "update",
  "changes": {
    "status": {"before": "open", "after": "in_progress"},
    "likelihood_inherent": {"before": 3, "after": 4}
  },
  "result": "success"
}
```

### 6.3 改ざん防止

| 対策 | 方法 |
|------|------|
| 追記のみ | 監査ログテーブルへのUPDATE/DELETE権限を剥奪 |
| チェックサム | 各ログエントリにSHA-256ハッシュチェーンを付与 |
| 外部保存 | 重要ログをSIEM（Microsoft Sentinel）にも転送 |
| パーティショニング | 月次パーティションによるデータ分離 |

---

## 7. 入力検証・インジェクション対策

### 7.1 OWASP Top 10 対策

| 脅威 | 対策 | 実装 |
|------|------|------|
| A01:2021 アクセス制御の不備 | RBAC + Row Level Security | DRF Permission Classes |
| A02:2021 暗号化の失敗 | TLS 1.3 + AES-256 | Nginx + django-encrypted-fields |
| A03:2021 インジェクション | パラメータバインド + エスケープ | Django ORM + DRF Serializer |
| A04:2021 安全でない設計 | 脅威モデリング + セキュリティレビュー | 設計レビュープロセス |
| A05:2021 セキュリティの設定ミス | 設定の自動チェック | Django check --deploy |
| A06:2021 脆弱なコンポーネント | 依存パッケージスキャン | Dependabot + Safety |
| A07:2021 認証の失敗 | JWT + MFA + アカウントロック | simplejwt + django-otp |
| A08:2021 ソフトウェアとデータの整合性 | CI/CDパイプラインのセキュリティ | GitHub Actions + 署名検証 |
| A09:2021 セキュリティログの不足 | 全操作監査ログ | AuditLogMiddleware |
| A10:2021 SSRF | URLホワイトリスト | 外部API呼び出しの制御 |

### 7.2 入力バリデーション

| レイヤー | バリデーション | ツール |
|---------|-------------|-------|
| フロントエンド | 即時フィードバック（形式チェック） | Vuelidate / VeeValidate |
| API（Serializer） | 型、必須、値範囲、参照整合性 | DRF Serializers |
| モデル | DB制約（NOT NULL, UNIQUE, CHECK, FK） | Django Model validators |

### 7.3 HTTPセキュリティヘッダー

```python
# Django settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True

# CSP (Content Security Policy)
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")  # Vuetify用
CSP_IMG_SRC = ("'self'", "data:")
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com")
CSP_CONNECT_SRC = ("'self'",)
```

---

## 8. 脆弱性管理

### 8.1 自動スキャン

| ツール | 対象 | 頻度 | 統合先 |
|--------|------|------|--------|
| Dependabot | Python/Node.js依存パッケージ | 日次 | GitHub |
| Safety | Python パッケージ脆弱性 | CI毎回 | GitHub Actions |
| npm audit | Node.js パッケージ脆弱性 | CI毎回 | GitHub Actions |
| Bandit | Python SAST（静的解析） | CI毎回 | GitHub Actions |
| ESLint Security | JavaScript SAST | CI毎回 | GitHub Actions |
| Trivy | Dockerイメージ脆弱性 | CI毎回 | GitHub Actions |
| OWASP ZAP | DAST（動的解析） | 月次 | 手動実行 |

### 8.2 脆弱性対応SLA

| 深刻度 | 対応期限 | エスカレーション |
|--------|---------|--------------|
| Critical（CVSS 9.0+） | 24時間以内 | 即時：CISO |
| High（CVSS 7.0-8.9） | 7日以内 | 3日後：部門長 |
| Medium（CVSS 4.0-6.9） | 30日以内 | 14日後：リーダー |
| Low（CVSS 0.1-3.9） | 次回リリース | - |

### 8.3 ペネトレーションテスト

| 項目 | 内容 |
|------|------|
| 実施頻度 | 年次（外部委託） |
| 対象範囲 | Webアプリケーション全体 + API |
| テスト手法 | OWASP Testing Guide v4準拠 |
| 報告書 | 脆弱性一覧 + 修正推奨事項 |
| 再テスト | 修正後に再検証 |

---

## 9. インシデント対応

### 9.1 セキュリティイベント検知

| イベント | 検知方法 | 対応 |
|---------|---------|------|
| ブルートフォース攻撃 | 5回連続認証失敗 | アカウントロック + 管理者通知 |
| 異常ログインパターン | 通常と異なるIPからのログイン | ユーザーへの確認通知 |
| 権限外アクセス試行 | 403レスポンスの頻発 | 監査ログ記録 + 閾値超で通知 |
| 大量データダウンロード | 短時間の大量API呼び出し | レートリミット + 通知 |
| SQLインジェクション試行 | WAFによる検知 | ブロック + ログ記録 |

### 9.2 インシデント対応フロー

```
検知 --> 初動対応(15分以内) --> 影響範囲特定 --> 封じ込め
  |                                                    |
  +-- 通知: CISO/セキュリティチーム                       |
                                                       v
                                            復旧 --> 再発防止 --> 報告書作成
```

---

## 10. データ分類と保護

### 10.1 データ分類

| 分類 | 定義 | 例 | 保護レベル |
|------|------|---|----------|
| 極秘 | 漏洩時に重大な経営影響 | リスクアセスメント生データ、脆弱性情報 | フィールドレベル暗号化、CISO以上のみアクセス |
| 機密 | 漏洩時に業務影響 | 監査所見、是正処置、未公開の準拠状況 | DB暗号化、RBAC制御 |
| 社内限定 | 社内のみ共有 | チェックリスト、管理策実施状況 | RBAC制御 |
| 公開 | 公開可能 | ISO27001管理策定義、NIST CSFフレームワーク | 認証済ユーザーのみ |

### 10.2 データ保持・廃棄

| データ | 保持期間 | 廃棄方法 |
|--------|---------|---------|
| 監査ログ | 5年以上 | 暗号化シュレッド |
| リスク評価履歴 | 無期限 | - |
| 是正処置記録 | 5年以上 | 暗号化シュレッド |
| 証跡ファイル | 5年以上 | ストレージレベル安全削除 |
| ユーザー情報 | アカウント削除後1年 | 物理削除 |
| セッション情報 | セッション終了後即時 | Redis自動削除 |

---

## 11. シークレット管理

### 11.1 シークレット一覧

| シークレット | 保管場所 | ローテーション |
|------------|---------|-------------|
| Django SECRET_KEY | Azure Key Vault / .env | 年次 |
| JWT署名鍵（RSA） | Azure Key Vault | 年次 |
| DB接続パスワード | Azure Key Vault / .env | 90日 |
| Redis パスワード | Azure Key Vault / .env | 90日 |
| SMTP認証情報 | Azure Key Vault / .env | 90日 |
| 暗号化マスターキー | Azure Key Vault | 年次 |
| 外部API認証情報 | Azure Key Vault | 接続先の規定に従う |

### 11.2 シークレット管理規約

- ソースコードにシークレットを含めない（.envファイルはGit管理外）
- 開発環境と本番環境でシークレットを分離
- Azure Key Vaultのアクセスログを監視
- シークレットのローテーション手順を文書化

---

*文書管理: 本文書はバージョン管理対象とし、セキュリティ設計変更時は改訂履歴を更新すること。*
