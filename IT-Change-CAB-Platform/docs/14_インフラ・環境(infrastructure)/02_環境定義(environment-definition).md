# 環境定義書
## IT変更管理・リリース自動化プラットフォーム（IT-Change-CAB-Platform）

| 項目 | 内容 |
|------|------|
| **文書番号** | INF-CAB-002 |
| **バージョン** | 1.0.0 |
| **作成日** | 2026-03-26 |
| **作成者** | みらい建設工業 IT部門 |
| **対象リポジトリ** | Kensan196948G/IT-Change-CAB-Platform |

---

## 1. 環境一覧

### 1.1 環境構成

| 環境名 | 用途 | URL | 管理者 |
|--------|------|-----|--------|
| 開発環境（Development） | 開発・単体テスト | http://localhost:3000 | 各開発者 |
| CI環境（CI） | 自動テスト実行 | - (GitHub Actions) | CI/CD管理者 |
| ステージング環境（Staging） | 結合テスト・E2E・性能テスト・UAT | https://stg-cab.mirai-kensetsu.co.jp | 運用チーム |
| 本番環境（Production） | 本番運用 | https://cab.mirai-kensetsu.co.jp | 運用チーム |

### 1.2 環境間の関係

```
開発環境 → CI環境 → ステージング環境 → 本番環境
  │         │           │                │
 開発者    GitHub      テスト・検証       本番運用
 ローカル  Actions     本番同等構成      ユーザー利用
```

---

## 2. 開発環境（Development）

### 2.1 概要

| 項目 | 内容 |
|------|------|
| 用途 | 開発者のローカル開発・デバッグ |
| 構成 | Docker Compose（開発用） + ローカルNode.js |
| データ | シードデータ（テスト用固定データ） |
| デプロイ | 手動（npm run dev） |

### 2.2 サービス構成

| サービス | イメージ/実行方法 | ポート | 備考 |
|---------|----------------|--------|------|
| Frontend | npm run dev (Vite) | 3000 | ホットリロード有効 |
| Backend | npm run dev (ts-node-dev) | 8000 | ホットリロード有効 |
| PostgreSQL | postgres:16-alpine (Docker) | 5432 | テスト用DB |
| Redis | redis:7-alpine (Docker) | 6379 | テスト用Redis |
| MailHog | mailhog (Docker) | 1025/8025 | メールテスト用 |
| BullMQ Dashboard | bullmq-dashboard (Docker) | 4735 | ジョブ管理UI |

### 2.3 環境変数

```env
# .env.development
NODE_ENV=development
PORT=8000

# データベース
DATABASE_URL=postgresql://admin:password@localhost:5432/cab_platform_dev
DB_USER=admin
DB_PASSWORD=password
DB_NAME=cab_platform_dev

# Redis
REDIS_URL=redis://localhost:6379/0

# 認証
JWT_SECRET=dev-jwt-secret-key-do-not-use-in-production
JWT_EXPIRY=24h
SESSION_TIMEOUT=3600

# メール（MailHog）
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USER=
SMTP_PASSWORD=
MAIL_FROM=cab-platform@dev.local

# Teams通知（開発環境では無効）
TEAMS_WEBHOOK_URL=

# CORS
CORS_ORIGIN=http://localhost:3000

# ログ
LOG_LEVEL=debug
LOG_FORMAT=text

# フロントエンド
VITE_API_URL=http://localhost:8000/api/v1
VITE_APP_TITLE=CAB Platform (Dev)
```

---

## 3. CI環境（CI）

### 3.1 概要

| 項目 | 内容 |
|------|------|
| 用途 | 自動テスト実行、ビルド確認 |
| 構成 | GitHub Actions ランナー + テスト用コンテナ |
| データ | テスト用一時データ（テスト毎にリセット） |
| デプロイ | 自動（GitHub Actions トリガー） |

### 3.2 GitHub Actions ランナー

| 項目 | 設定 |
|------|------|
| ランナー | ubuntu-latest |
| Node.js | 20.x |
| Docker | GitHub Actionsビルトイン |
| キャッシュ | npm キャッシュ |

### 3.3 環境変数

```env
# CI環境（GitHub Actions Secrets/Variables）
NODE_ENV=test

# データベース（テスト用コンテナ）
DATABASE_URL=postgresql://test_user:test_password@localhost:5433/cab_platform_test

# Redis（テスト用コンテナ）
REDIS_URL=redis://localhost:6380/0

# 認証
JWT_SECRET=ci-test-jwt-secret

# 通知（CI環境では無効）
TEAMS_WEBHOOK_URL=
SMTP_HOST=

# ログ
LOG_LEVEL=warn
```

---

## 4. ステージング環境（Staging）

### 4.1 概要

| 項目 | 内容 |
|------|------|
| 用途 | 結合テスト、E2Eテスト、性能テスト、受入テスト |
| 構成 | 本番同等のDocker Compose構成 |
| データ | 匿名化済み本番相当データ |
| デプロイ | CI/CDパイプラインによる自動デプロイ |
| アクセス制限 | 社内ネットワークからのみアクセス可能 |

### 4.2 サーバースペック

| 項目 | スペック |
|------|---------|
| CPU | 4 vCPU |
| メモリ | 8GB |
| ディスク | 100GB SSD |
| OS | Ubuntu 22.04 LTS |

### 4.3 サービス構成

| サービス | イメージ | ポート | 備考 |
|---------|---------|--------|------|
| Nginx | nginx:alpine | 80, 443 | SSL終端、リバースプロキシ |
| Frontend | cab-platform-frontend:staging | 3000 (内部) | ビルド済み静的ファイル |
| Backend | cab-platform-backend:staging | 8000 (内部) | Node.js本番モード |
| Worker | cab-platform-backend:staging | - | BullMQワーカー |
| PostgreSQL | postgres:16-alpine | 5432 (内部) | 本番同等設定 |
| Redis | redis:7-alpine | 6379 (内部) | 本番同等設定 |
| Prometheus | prom/prometheus | 9090 | メトリクス収集 |
| Grafana | grafana/grafana | 3001 | 監視ダッシュボード |

### 4.4 環境変数

```env
# .env.staging
NODE_ENV=staging
PORT=8000
APP_VERSION=<リリース候補バージョン>

# データベース
DATABASE_URL=postgresql://stg_admin:${STG_DB_PASSWORD}@db:5432/cab_platform_stg
DB_USER=stg_admin
DB_PASSWORD=${STG_DB_PASSWORD}
DB_NAME=cab_platform_stg

# Redis
REDIS_URL=redis://redis:6379/0

# 認証
JWT_SECRET=${STG_JWT_SECRET}
JWT_EXPIRY=8h
SESSION_TIMEOUT=1800

# メール
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=${STG_SMTP_USER}
SMTP_PASSWORD=${STG_SMTP_PASSWORD}
MAIL_FROM=cab-platform-stg@mirai-kensetsu.co.jp

# Teams通知（テスト用チャネル）
TEAMS_WEBHOOK_URL=${STG_TEAMS_WEBHOOK_URL}

# CORS
CORS_ORIGIN=https://stg-cab.mirai-kensetsu.co.jp

# ログ
LOG_LEVEL=info
LOG_FORMAT=json

# フロントエンド
VITE_API_URL=https://stg-cab.mirai-kensetsu.co.jp/api/v1
VITE_APP_TITLE=CAB Platform (Staging)
```

### 4.5 ステージング環境の制約

| 制約 | 内容 |
|------|------|
| 通知先 | テスト用Teamsチャネル・テスト用メールアドレスに限定 |
| データ | 個人情報は匿名化処理済みデータを使用 |
| 外部連携 | ITSM連携はモック/サンドボックスを使用 |
| アクセス | VPN経由の社内ネットワークからのみ |

---

## 5. 本番環境（Production）

### 5.1 概要

| 項目 | 内容 |
|------|------|
| 用途 | 本番運用、ユーザー利用 |
| 構成 | Docker Compose 本番構成 |
| データ | 本番データ |
| デプロイ | CI/CDパイプライン + 手動承認 |
| 可用性 | 稼働率 99.5%以上、RTO 4時間 |

### 5.2 サーバースペック

| 項目 | スペック |
|------|---------|
| CPU | 8 vCPU |
| メモリ | 16GB |
| ディスク | 200GB SSD |
| OS | Ubuntu 22.04 LTS |
| バックアップ | 別ストレージ 500GB |

### 5.3 サービス構成

| サービス | イメージ | ポート | リソース制限 |
|---------|---------|--------|------------|
| Nginx | nginx:alpine | 80, 443 | CPU: 0.5, Mem: 256MB |
| Frontend | cab-platform-frontend:v<VERSION> | 3000 (内部) | CPU: 0.5, Mem: 512MB |
| Backend | cab-platform-backend:v<VERSION> | 8000 (内部) | CPU: 2.0, Mem: 4GB |
| Worker | cab-platform-backend:v<VERSION> | - | CPU: 1.0, Mem: 2GB |
| PostgreSQL | postgres:16-alpine | 5432 (内部) | CPU: 2.0, Mem: 4GB |
| Redis | redis:7-alpine | 6379 (内部) | CPU: 0.5, Mem: 512MB |
| 監視スタック | 各種 | 内部 | 別途割当 |

### 5.4 環境変数

```env
# .env.prod
NODE_ENV=production
PORT=8000
APP_VERSION=<リリースバージョン>

# データベース
DATABASE_URL=postgresql://prod_admin:${PROD_DB_PASSWORD}@db:5432/cab_platform
DB_USER=prod_admin
DB_PASSWORD=${PROD_DB_PASSWORD}
DB_NAME=cab_platform

# Redis
REDIS_URL=redis://redis:6379/0

# 認証
JWT_SECRET=${PROD_JWT_SECRET}
JWT_EXPIRY=8h
SESSION_TIMEOUT=1800

# メール
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=${PROD_SMTP_USER}
SMTP_PASSWORD=${PROD_SMTP_PASSWORD}
MAIL_FROM=cab-platform@mirai-kensetsu.co.jp

# Teams通知
TEAMS_WEBHOOK_URL=${PROD_TEAMS_WEBHOOK_URL}

# CORS
CORS_ORIGIN=https://cab.mirai-kensetsu.co.jp

# ログ
LOG_LEVEL=info
LOG_FORMAT=json

# フロントエンド
VITE_API_URL=https://cab.mirai-kensetsu.co.jp/api/v1
VITE_APP_TITLE=IT変更管理プラットフォーム
```

---

## 6. 環境変数一覧（全環境比較）

| 変数名 | 開発 | CI | ステージング | 本番 |
|--------|------|-----|------------|------|
| `NODE_ENV` | development | test | staging | production |
| `PORT` | 8000 | 8000 | 8000 | 8000 |
| `DATABASE_URL` | localhost:5432/cab_dev | localhost:5433/cab_test | db:5432/cab_stg | db:5432/cab_platform |
| `REDIS_URL` | localhost:6379/0 | localhost:6380/0 | redis:6379/0 | redis:6379/0 |
| `JWT_SECRET` | 固定値（開発用） | 固定値（テスト用） | ランダム生成 | ランダム生成（256bit） |
| `JWT_EXPIRY` | 24h | 1h | 8h | 8h |
| `SESSION_TIMEOUT` | 3600 | 300 | 1800 | 1800 |
| `LOG_LEVEL` | debug | warn | info | info |
| `LOG_FORMAT` | text | json | json | json |
| `SMTP_HOST` | localhost (MailHog) | (無効) | smtp.office365.com | smtp.office365.com |
| `SMTP_PORT` | 1025 | - | 587 | 587 |
| `TEAMS_WEBHOOK_URL` | (空) | (空) | テスト用チャネル | 本番チャネル |
| `CORS_ORIGIN` | * | * | stg-domain | prod-domain |
| `VITE_API_URL` | localhost:8000 | - | stg-domain/api/v1 | prod-domain/api/v1 |

---

## 7. 環境間のデータ管理

### 7.1 データフロー

| フロー | 内容 | 頻度 |
|-------|------|------|
| 本番 → ステージング | 匿名化済み本番データのコピー | リリース前テスト時 |
| シードデータ → 開発 | テスト用固定データの投入 | 環境構築時 |
| シードデータ → CI | テスト用一時データの投入 | テスト実行時 |

### 7.2 データ匿名化ルール

| データ項目 | 匿名化方法 |
|-----------|-----------|
| ユーザー名 | ハッシュ化された仮名に置換 |
| メールアドレス | `user_XXXX@test.example.com` に置換 |
| IPアドレス | `0.0.0.0` に置換 |
| コメント・説明文 | テスト用テキストに置換（機密情報を含む場合） |
| RFC番号 | 保持（識別性を維持） |
| 日時 | 保持 |

---

## 8. SSL/TLS証明書管理

### 8.1 証明書情報

| 環境 | ドメイン | 証明書 | 有効期限管理 |
|------|---------|--------|------------|
| ステージング | stg-cab.mirai-kensetsu.co.jp | 内部CA発行 | 年次更新 |
| 本番 | cab.mirai-kensetsu.co.jp | 商用CA発行 | 年次更新（30日前アラート） |

### 8.2 証明書更新手順

```bash
# 1. 新しい証明書を配置
cp new-cert.pem /opt/cab-platform/nginx/ssl/cert.pem
cp new-key.pem /opt/cab-platform/nginx/ssl/key.pem
chmod 600 /opt/cab-platform/nginx/ssl/key.pem

# 2. Nginx再読み込み（無停止）
docker compose exec nginx nginx -s reload

# 3. 証明書確認
echo | openssl s_client -connect cab.mirai-kensetsu.co.jp:443 2>/dev/null | openssl x509 -noout -dates
```

---

*文書管理：本文書はバージョン管理対象。変更時はバージョン番号を更新すること。*
