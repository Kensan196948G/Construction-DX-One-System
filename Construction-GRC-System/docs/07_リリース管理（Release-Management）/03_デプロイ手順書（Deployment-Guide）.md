# デプロイ手順書（Deployment Guide）

| 項目 | 内容 |
|------|------|
| 文書番号 | GRC-RM-003 |
| バージョン | 1.0 |
| 作成日 | 2026-03-26 |
| 最終更新日 | 2026-03-26 |
| 作成者 | GRC開発チーム |
| 承認者 | インフラストラクチャリード |
| 分類 | リリース管理 |
| 準拠規格 | ISO27001:2022 / NIST CSF 2.0 / 建設業法 / 品確法 / 労安法 |

---

## 1. 目的

本文書は、Construction-GRC-Systemの各環境（開発・ステージング・本番）へのデプロイ手順を定義する。再現性のある安全なデプロイプロセスを確立し、サービス品質を維持することを目的とする。

---

## 2. 前提条件

### 2.1 必要ツール

| ツール | バージョン | 用途 |
|--------|----------|------|
| Docker | 24.0以上 | コンテナランタイム |
| Docker Compose | 2.20以上 | コンテナオーケストレーション |
| Git | 2.40以上 | ソースコード管理 |
| Node.js | 20 LTS | フロントエンドビルド |
| Python | 3.12以上 | バックエンドアプリケーション |
| PostgreSQL Client | 16以上 | データベースマイグレーション |
| AWS CLI | 2.x | AWSリソース操作（本番環境） |
| kubectl | 1.28以上 | Kubernetes操作（将来拡張用） |

### 2.2 必要権限

| 環境 | 必要権限 | 付与対象 |
|------|---------|---------|
| Development | Docker実行権限、リポジトリアクセス | 全開発者 |
| Staging | サーバーSSHアクセス、Docker実行権限 | インフラ担当、テックリード |
| Production | サーバーSSHアクセス、Docker実行権限、AWS IAM | インフラ担当（2名以上のペア作業必須） |

---

## 3. システム構成

### 3.1 コンテナ構成

```
┌──────────────────────────────────────────────────────────┐
│                    Docker Compose 構成                     │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐   │
│  │  Nginx   │  │ Frontend │  │   Backend (API)      │   │
│  │ :80/:443 │─►│  :3000   │  │   :8000              │   │
│  │          │─────────────────►                      │   │
│  └──────────┘  └──────────┘  └──────────┬───────────┘   │
│                                          │               │
│                              ┌───────────┼───────────┐   │
│                              │           │           │   │
│                              ▼           ▼           ▼   │
│                         ┌────────┐ ┌─────────┐ ┌──────┐ │
│                         │ Postgres│ │  Redis  │ │MinIO │ │
│                         │ :5432  │ │  :6379  │ │:9000 │ │
│                         └────────┘ └─────────┘ └──────┘ │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ Celery Worker │  │ Celery Beat  │  │  Prometheus   │  │
│  │              │  │  (Scheduler) │  │    :9090      │  │
│  └──────────────┘  └──────────────┘  └───────────────┘  │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐                     │
│  │   Grafana    │  │    Loki      │                     │
│  │   :3001      │  │   :3100      │                     │
│  └──────────────┘  └──────────────┘                     │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 3.2 ディレクトリ構成

```
Construction-GRC-System/
├── docker/
│   ├── docker-compose.yml              # 共通設定
│   ├── docker-compose.dev.yml          # 開発環境オーバーライド
│   ├── docker-compose.staging.yml      # ステージング環境オーバーライド
│   ├── docker-compose.prod.yml         # 本番環境オーバーライド
│   ├── nginx/
│   │   ├── nginx.conf
│   │   ├── conf.d/
│   │   └── ssl/
│   ├── backend/
│   │   └── Dockerfile
│   ├── frontend/
│   │   └── Dockerfile
│   └── monitoring/
│       ├── prometheus.yml
│       └── grafana/
├── backend/
│   ├── app/
│   ├── migrations/
│   ├── requirements.txt
│   └── manage.py
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── scripts/
│   ├── deploy.sh
│   ├── rollback.sh
│   ├── backup.sh
│   └── health-check.sh
└── .env.example
```

---

## 4. 開発環境デプロイ手順

### 4.1 初回セットアップ

```bash
# 1. リポジトリのクローン
git clone https://github.com/your-org/Construction-GRC-System.git
cd Construction-GRC-System

# 2. 環境変数ファイルの作成
cp .env.example .env.dev
# .env.dev を開いて必要な環境変数を設定

# 3. Docker イメージのビルド
docker compose -f docker/docker-compose.yml \
               -f docker/docker-compose.dev.yml \
               build

# 4. コンテナ起動
docker compose -f docker/docker-compose.yml \
               -f docker/docker-compose.dev.yml \
               up -d

# 5. データベースマイグレーション
docker compose -f docker/docker-compose.yml \
               -f docker/docker-compose.dev.yml \
               exec backend python manage.py migrate

# 6. 初期データ投入
docker compose -f docker/docker-compose.yml \
               -f docker/docker-compose.dev.yml \
               exec backend python manage.py loaddata initial_data

# 7. 管理者ユーザー作成
docker compose -f docker/docker-compose.yml \
               -f docker/docker-compose.dev.yml \
               exec backend python manage.py createsuperuser

# 8. 動作確認
curl http://localhost:3000        # フロントエンド
curl http://localhost:8000/health # バックエンド ヘルスチェック
```

### 4.2 日常のデプロイ（開発環境更新）

```bash
# 1. 最新コードの取得
git pull origin develop

# 2. イメージの再ビルド（変更がある場合）
docker compose -f docker/docker-compose.yml \
               -f docker/docker-compose.dev.yml \
               build --no-cache

# 3. コンテナの再起動
docker compose -f docker/docker-compose.yml \
               -f docker/docker-compose.dev.yml \
               up -d

# 4. マイグレーション（必要な場合）
docker compose -f docker/docker-compose.yml \
               -f docker/docker-compose.dev.yml \
               exec backend python manage.py migrate
```

### 4.3 開発環境 docker-compose.dev.yml

```yaml
# docker/docker-compose.dev.yml
version: '3.8'

services:
  backend:
    build:
      context: ../backend
      dockerfile: ../docker/backend/Dockerfile
      target: development
    volumes:
      - ../backend:/app
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
      - DATABASE_URL=postgresql://grc_dev:devpassword@postgres:5432/grc_dev
      - REDIS_URL=redis://redis:6379/0
    ports:
      - "8000:8000"
    command: python manage.py runserver 0.0.0.0:8000

  frontend:
    build:
      context: ../frontend
      dockerfile: ../docker/frontend/Dockerfile
      target: development
    volumes:
      - ../frontend/src:/app/src
    environment:
      - VITE_API_URL=http://localhost:8000
    ports:
      - "3000:3000"
    command: npm run dev

  postgres:
    image: postgres:16-alpine
    environment:
      - POSTGRES_DB=grc_dev
      - POSTGRES_USER=grc_dev
      - POSTGRES_PASSWORD=devpassword
    ports:
      - "5432:5432"
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_dev_data:
```

---

## 5. ステージング環境デプロイ手順

### 5.1 前提

- ステージング環境はCI/CDパイプライン（GitHub Actions）から自動デプロイ可能
- `release/*` ブランチへのプッシュで自動トリガー
- 手動デプロイも可能

### 5.2 自動デプロイ（GitHub Actions）

```yaml
# .github/workflows/deploy-staging.yml
name: Deploy to Staging

on:
  push:
    branches:
      - 'release/*'

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4

      - name: Run Tests
        run: |
          docker compose -f docker/docker-compose.yml \
                         -f docker/docker-compose.test.yml \
                         run --rm backend pytest --cov

      - name: Security Scan
        run: |
          docker compose -f docker/docker-compose.yml \
                         -f docker/docker-compose.test.yml \
                         run --rm backend pip-audit
          docker compose -f docker/docker-compose.yml \
                         -f docker/docker-compose.test.yml \
                         run --rm frontend npm audit

      - name: Build Images
        run: |
          docker compose -f docker/docker-compose.yml \
                         -f docker/docker-compose.staging.yml \
                         build

      - name: Push to Registry
        run: |
          docker tag grc-backend:latest ${{ secrets.REGISTRY }}/grc-backend:staging
          docker tag grc-frontend:latest ${{ secrets.REGISTRY }}/grc-frontend:staging
          docker push ${{ secrets.REGISTRY }}/grc-backend:staging
          docker push ${{ secrets.REGISTRY }}/grc-frontend:staging

      - name: Deploy to Staging Server
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.STAGING_HOST }}
          username: ${{ secrets.STAGING_USER }}
          key: ${{ secrets.STAGING_SSH_KEY }}
          script: |
            cd /opt/grc-system
            ./scripts/deploy.sh staging
```

### 5.3 手動デプロイ

```bash
# ステージングサーバーにSSH接続
ssh deploy@stg-grc-server.example.co.jp

# 1. デプロイディレクトリに移動
cd /opt/grc-system

# 2. 最新のリリースブランチをチェックアウト
git fetch origin
git checkout release/x.y.z
git pull origin release/x.y.z

# 3. 環境変数確認
diff .env.staging .env.staging.new  # 変更がある場合

# 4. バックアップ取得
./scripts/backup.sh staging

# 5. イメージのビルド
docker compose -f docker/docker-compose.yml \
               -f docker/docker-compose.staging.yml \
               build --no-cache

# 6. データベースマイグレーション（必要な場合）
docker compose -f docker/docker-compose.yml \
               -f docker/docker-compose.staging.yml \
               exec backend python manage.py migrate --check
# マイグレーションが必要な場合:
docker compose -f docker/docker-compose.yml \
               -f docker/docker-compose.staging.yml \
               exec backend python manage.py migrate

# 7. コンテナの更新（ゼロダウンタイム）
docker compose -f docker/docker-compose.yml \
               -f docker/docker-compose.staging.yml \
               up -d --remove-orphans

# 8. ヘルスチェック
./scripts/health-check.sh staging

# 9. スモークテスト
./scripts/smoke-test.sh staging
```

### 5.4 ステージング環境 docker-compose.staging.yml

```yaml
# docker/docker-compose.staging.yml
version: '3.8'

services:
  nginx:
    image: nginx:1.25-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/conf.d/staging.conf:/etc/nginx/conf.d/default.conf
      - ./nginx/ssl/staging:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend
    restart: always

  backend:
    build:
      context: ../backend
      dockerfile: ../docker/backend/Dockerfile
      target: production
    environment:
      - DEBUG=false
      - LOG_LEVEL=INFO
      - DATABASE_URL=${STAGING_DATABASE_URL}
      - REDIS_URL=${STAGING_REDIS_URL}
      - ALLOWED_HOSTS=stg.grc.example.co.jp
      - CORS_ORIGINS=https://stg.grc.example.co.jp
    restart: always
    deploy:
      replicas: 2

  frontend:
    build:
      context: ../frontend
      dockerfile: ../docker/frontend/Dockerfile
      target: production
      args:
        - VITE_API_URL=https://stg.grc.example.co.jp/api
    restart: always

  celery-worker:
    build:
      context: ../backend
      dockerfile: ../docker/backend/Dockerfile
      target: production
    command: celery -A config worker -l info -c 4
    environment:
      - DATABASE_URL=${STAGING_DATABASE_URL}
      - REDIS_URL=${STAGING_REDIS_URL}
    restart: always

  celery-beat:
    build:
      context: ../backend
      dockerfile: ../docker/backend/Dockerfile
      target: production
    command: celery -A config beat -l info
    environment:
      - DATABASE_URL=${STAGING_DATABASE_URL}
      - REDIS_URL=${STAGING_REDIS_URL}
    restart: always

  redis:
    image: redis:7-alpine
    restart: always
    volumes:
      - redis_staging_data:/data

  prometheus:
    image: prom/prometheus:v2.48.0
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_staging_data:/prometheus
    restart: always

  grafana:
    image: grafana/grafana:10.2.0
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_staging_data:/var/lib/grafana
    restart: always

volumes:
  redis_staging_data:
  prometheus_staging_data:
  grafana_staging_data:
```

---

## 6. 本番環境デプロイ手順

### 6.1 デプロイ前チェック

```bash
# 必須: 本番デプロイは2名以上のペア作業で実施すること

# 1. リリースチェックリスト（GRC-RM-002）の全項目確認済みであること
# 2. CAB承認が完了していること
# 3. メンテナンスウィンドウ内であること（毎月第3水曜日 22:00〜翌02:00 JST）

# デプロイ前確認
echo "=== 本番デプロイ前チェック ==="
echo "[ ] リリースチェックリスト全項目OK"
echo "[ ] CAB承認完了（承認者: ___________）"
echo "[ ] メンテナンスウィンドウ内"
echo "[ ] ペア作業者: ___________ / ___________"
echo "[ ] ロールバック手順確認済み"
echo "[ ] バックアップ最新確認済み"
echo "================================"
```

### 6.2 本番デプロイ手順

```bash
# 本番サーバーにSSH接続（踏み台サーバー経由）
ssh -J bastion@bastion.grc.example.co.jp deploy@prod-grc-server.example.co.jp

# ===== STEP 1: 準備 =====

# 1-1. デプロイディレクトリに移動
cd /opt/grc-system

# 1-2. 現在のバージョン確認
cat VERSION
docker compose -f docker/docker-compose.yml \
               -f docker/docker-compose.prod.yml \
               exec backend python manage.py version

# 1-3. ディスク容量確認
df -h /opt/grc-system

# ===== STEP 2: バックアップ =====

# 2-1. フルバックアップ取得
./scripts/backup.sh production --full

# 2-2. バックアップ検証
./scripts/backup.sh production --verify

# 2-3. 現在のDockerイメージタグ記録
docker images | grep grc > /tmp/current_images.txt
echo "Current version backup completed at $(date)"

# ===== STEP 3: メンテナンスモード =====

# 3-1. メンテナンスモード有効化
docker compose -f docker/docker-compose.yml \
               -f docker/docker-compose.prod.yml \
               exec backend python manage.py maintenance_mode --enable

# 3-2. メンテナンスページ表示確認
curl -s -o /dev/null -w "%{http_code}" https://grc.example.co.jp
# 期待値: 503

# ===== STEP 4: デプロイ =====

# 4-1. リリースブランチのチェックアウト
git fetch origin
git checkout main
git pull origin main

# 4-2. 環境変数の更新（変更がある場合）
# diff .env.production .env.production.new
# 確認後: cp .env.production.new .env.production

# 4-3. Dockerイメージのプル（事前ビルド済みの場合）
docker pull ${REGISTRY}/grc-backend:v${VERSION}
docker pull ${REGISTRY}/grc-frontend:v${VERSION}

# または、現地ビルド
docker compose -f docker/docker-compose.yml \
               -f docker/docker-compose.prod.yml \
               build --no-cache

# 4-4. データベースマイグレーション
docker compose -f docker/docker-compose.yml \
               -f docker/docker-compose.prod.yml \
               exec backend python manage.py migrate --check

# マイグレーションが必要な場合:
docker compose -f docker/docker-compose.yml \
               -f docker/docker-compose.prod.yml \
               exec backend python manage.py migrate

# 4-5. 静的ファイル収集
docker compose -f docker/docker-compose.yml \
               -f docker/docker-compose.prod.yml \
               exec backend python manage.py collectstatic --noinput

# 4-6. コンテナの更新
docker compose -f docker/docker-compose.yml \
               -f docker/docker-compose.prod.yml \
               up -d --remove-orphans

# ===== STEP 5: 検証 =====

# 5-1. コンテナ起動確認
docker compose -f docker/docker-compose.yml \
               -f docker/docker-compose.prod.yml \
               ps

# 5-2. ヘルスチェック
./scripts/health-check.sh production

# 5-3. ログ確認（エラーがないこと）
docker compose -f docker/docker-compose.yml \
               -f docker/docker-compose.prod.yml \
               logs --tail=50 backend

# 5-4. データベース接続確認
docker compose -f docker/docker-compose.yml \
               -f docker/docker-compose.prod.yml \
               exec backend python manage.py dbshell -c "SELECT 1;"

# ===== STEP 6: メンテナンスモード解除 =====

# 6-1. メンテナンスモード解除
docker compose -f docker/docker-compose.yml \
               -f docker/docker-compose.prod.yml \
               exec backend python manage.py maintenance_mode --disable

# 6-2. サービス正常応答確認
curl -s -o /dev/null -w "%{http_code}" https://grc.example.co.jp
# 期待値: 200

# ===== STEP 7: リリース後作業 =====

# 7-1. バージョン更新記録
echo "v${VERSION}" > VERSION
echo "Deployed at $(date)" >> DEPLOY_LOG

# 7-2. スモークテスト実行
./scripts/smoke-test.sh production

# 7-3. 監視ダッシュボード確認
echo "Grafana: https://monitoring.grc.example.co.jp"
echo "エラーレート、レスポンスタイム、CPU/メモリを確認"

# 7-4. 不要な旧イメージの削除
docker image prune -f
```

### 6.3 本番環境 docker-compose.prod.yml

```yaml
# docker/docker-compose.prod.yml
version: '3.8'

services:
  nginx:
    image: nginx:1.25-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/conf.d/production.conf:/etc/nginx/conf.d/default.conf
      - ./nginx/ssl/production:/etc/nginx/ssl
      - static_files:/var/www/static
    depends_on:
      - backend
      - frontend
    restart: always
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "5"

  backend:
    image: ${REGISTRY}/grc-backend:${VERSION}
    environment:
      - DEBUG=false
      - LOG_LEVEL=WARN
      - DATABASE_URL=${PROD_DATABASE_URL}
      - REDIS_URL=${PROD_REDIS_URL}
      - SECRET_KEY=${PROD_SECRET_KEY}
      - ALLOWED_HOSTS=grc.example.co.jp
      - CORS_ORIGINS=https://grc.example.co.jp
      - SECURE_SSL_REDIRECT=true
      - SESSION_COOKIE_SECURE=true
      - CSRF_COOKIE_SECURE=true
      - SECURE_HSTS_SECONDS=31536000
    volumes:
      - static_files:/app/static
      - media_files:/app/media
    restart: always
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '0.5'
          memory: 1G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "10"

  frontend:
    image: ${REGISTRY}/grc-frontend:${VERSION}
    restart: always
    deploy:
      replicas: 2

  celery-worker:
    image: ${REGISTRY}/grc-backend:${VERSION}
    command: celery -A config worker -l warning -c 8 -Q default,grc,audit,notification
    environment:
      - DATABASE_URL=${PROD_DATABASE_URL}
      - REDIS_URL=${PROD_REDIS_URL}
    restart: always
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1.0'
          memory: 2G

  celery-beat:
    image: ${REGISTRY}/grc-backend:${VERSION}
    command: celery -A config beat -l warning --scheduler django_celery_beat.schedulers:DatabaseScheduler
    environment:
      - DATABASE_URL=${PROD_DATABASE_URL}
      - REDIS_URL=${PROD_REDIS_URL}
    restart: always

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD} --maxmemory 2gb --maxmemory-policy allkeys-lru
    restart: always
    volumes:
      - redis_prod_data:/data

  prometheus:
    image: prom/prometheus:v2.48.0
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_prod_data:/prometheus
    restart: always

  grafana:
    image: grafana/grafana:10.2.0
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_SERVER_ROOT_URL=https://monitoring.grc.example.co.jp
    volumes:
      - grafana_prod_data:/var/lib/grafana
    restart: always

  loki:
    image: grafana/loki:2.9.0
    volumes:
      - loki_prod_data:/loki
    restart: always

volumes:
  static_files:
  media_files:
  redis_prod_data:
  prometheus_prod_data:
  grafana_prod_data:
  loki_prod_data:
```

---

## 7. デプロイスクリプト

### 7.1 共通デプロイスクリプト（scripts/deploy.sh）

```bash
#!/bin/bash
set -euo pipefail

# =============================================================================
# Construction-GRC-System デプロイスクリプト
# 使用方法: ./scripts/deploy.sh <environment> [--skip-backup] [--skip-migration]
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="${1:-}"
SKIP_BACKUP=false
SKIP_MIGRATION=false
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/var/log/grc-deploy/${ENVIRONMENT}_${TIMESTAMP}.log"

# 引数解析
for arg in "$@"; do
  case $arg in
    --skip-backup) SKIP_BACKUP=true ;;
    --skip-migration) SKIP_MIGRATION=true ;;
  esac
done

# 環境チェック
if [[ -z "$ENVIRONMENT" ]] || [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
  echo "ERROR: 環境を指定してください: development, staging, production"
  exit 1
fi

# ログ関数
log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$ENVIRONMENT] $1" | tee -a "$LOG_FILE"
}

# エラーハンドリング
trap 'log "ERROR: デプロイ中にエラーが発生しました（行: $LINENO）"; exit 1' ERR

log "===== デプロイ開始: $ENVIRONMENT ====="

# Compose ファイル指定
COMPOSE_CMD="docker compose -f ${PROJECT_DIR}/docker/docker-compose.yml"
case $ENVIRONMENT in
  development)  COMPOSE_CMD="$COMPOSE_CMD -f ${PROJECT_DIR}/docker/docker-compose.dev.yml" ;;
  staging)      COMPOSE_CMD="$COMPOSE_CMD -f ${PROJECT_DIR}/docker/docker-compose.staging.yml" ;;
  production)   COMPOSE_CMD="$COMPOSE_CMD -f ${PROJECT_DIR}/docker/docker-compose.prod.yml" ;;
esac

# バックアップ
if [[ "$SKIP_BACKUP" == false ]] && [[ "$ENVIRONMENT" != "development" ]]; then
  log "バックアップ取得中..."
  ${SCRIPT_DIR}/backup.sh "$ENVIRONMENT"
  log "バックアップ完了"
fi

# イメージビルド/プル
log "イメージ準備中..."
$COMPOSE_CMD build --no-cache
log "イメージ準備完了"

# マイグレーション
if [[ "$SKIP_MIGRATION" == false ]]; then
  log "マイグレーションチェック中..."
  if $COMPOSE_CMD exec -T backend python manage.py migrate --check 2>/dev/null; then
    log "マイグレーション不要"
  else
    log "マイグレーション実行中..."
    $COMPOSE_CMD exec -T backend python manage.py migrate
    log "マイグレーション完了"
  fi
fi

# コンテナ更新
log "コンテナ更新中..."
$COMPOSE_CMD up -d --remove-orphans
log "コンテナ更新完了"

# ヘルスチェック
log "ヘルスチェック実行中..."
${SCRIPT_DIR}/health-check.sh "$ENVIRONMENT"
log "ヘルスチェック完了"

log "===== デプロイ完了: $ENVIRONMENT ====="
```

### 7.2 ヘルスチェックスクリプト（scripts/health-check.sh）

```bash
#!/bin/bash
set -euo pipefail

# =============================================================================
# ヘルスチェックスクリプト
# 使用方法: ./scripts/health-check.sh <environment>
# =============================================================================

ENVIRONMENT="${1:-development}"
MAX_RETRIES=30
RETRY_INTERVAL=5

case $ENVIRONMENT in
  development)  BASE_URL="http://localhost" ;;
  staging)      BASE_URL="https://stg.grc.example.co.jp" ;;
  production)   BASE_URL="https://grc.example.co.jp" ;;
esac

echo "=== ヘルスチェック開始: $ENVIRONMENT ==="

# API ヘルスチェック
echo -n "API ヘルスチェック... "
for i in $(seq 1 $MAX_RETRIES); do
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/health" 2>/dev/null || echo "000")
  if [[ "$HTTP_CODE" == "200" ]]; then
    echo "OK (HTTP $HTTP_CODE)"
    break
  fi
  if [[ $i -eq $MAX_RETRIES ]]; then
    echo "FAILED (HTTP $HTTP_CODE after $MAX_RETRIES retries)"
    exit 1
  fi
  sleep $RETRY_INTERVAL
done

# フロントエンド ヘルスチェック
echo -n "フロントエンド ヘルスチェック... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/" 2>/dev/null || echo "000")
if [[ "$HTTP_CODE" == "200" ]]; then
  echo "OK (HTTP $HTTP_CODE)"
else
  echo "FAILED (HTTP $HTTP_CODE)"
  exit 1
fi

# データベース接続チェック
echo -n "データベース接続チェック... "
COMPOSE_CMD="docker compose -f docker/docker-compose.yml"
case $ENVIRONMENT in
  development)  COMPOSE_CMD="$COMPOSE_CMD -f docker/docker-compose.dev.yml" ;;
  staging)      COMPOSE_CMD="$COMPOSE_CMD -f docker/docker-compose.staging.yml" ;;
  production)   COMPOSE_CMD="$COMPOSE_CMD -f docker/docker-compose.prod.yml" ;;
esac

if $COMPOSE_CMD exec -T backend python manage.py dbshell -c "SELECT 1;" > /dev/null 2>&1; then
  echo "OK"
else
  echo "FAILED"
  exit 1
fi

echo "=== ヘルスチェック完了: 全チェック合格 ==="
```

---

## 8. SSL/TLS証明書管理

### 8.1 証明書一覧

| 環境 | ドメイン | 証明書種別 | 発行元 | 有効期限管理 |
|------|---------|----------|--------|------------|
| Development | localhost | 自己署名 | ローカル生成 | なし |
| Staging | stg.grc.example.co.jp | DV証明書 | Let's Encrypt | 自動更新（certbot） |
| Production | grc.example.co.jp | OV証明書 | 商用CA | 手動更新（60日前アラート） |

### 8.2 証明書更新手順（本番環境）

```bash
# 1. 新しい証明書ファイルを配置
cp new_cert.pem /opt/grc-system/docker/nginx/ssl/production/server.crt
cp new_key.pem /opt/grc-system/docker/nginx/ssl/production/server.key

# 2. 証明書の検証
openssl x509 -in /opt/grc-system/docker/nginx/ssl/production/server.crt -text -noout

# 3. Nginx再起動
docker compose -f docker/docker-compose.yml \
               -f docker/docker-compose.prod.yml \
               restart nginx

# 4. SSL接続確認
openssl s_client -connect grc.example.co.jp:443 -servername grc.example.co.jp
```

---

## 9. トラブルシューティング

### 9.1 よくある問題と対処法

| 問題 | 原因 | 対処法 |
|------|------|--------|
| コンテナが起動しない | ポート競合 | `docker compose ps` でポート確認、競合するコンテナを停止 |
| データベース接続エラー | 認証情報不正 | `.env` ファイルの `DATABASE_URL` を確認 |
| マイグレーション失敗 | スキーマ不整合 | `python manage.py showmigrations` で状態確認 |
| メモリ不足 | コンテナリソース制限 | `docker stats` で使用量確認、制限値を調整 |
| ビルド失敗 | キャッシュ不整合 | `docker compose build --no-cache` で再ビルド |
| SSL証明書エラー | 証明書期限切れ | 証明書の有効期限を確認し更新 |

### 9.2 ログ確認方法

```bash
# 全コンテナのログ
docker compose -f docker/docker-compose.yml \
               -f docker/docker-compose.prod.yml \
               logs --tail=100

# 特定コンテナのログ
docker compose -f docker/docker-compose.yml \
               -f docker/docker-compose.prod.yml \
               logs --tail=100 backend

# リアルタイムログ
docker compose -f docker/docker-compose.yml \
               -f docker/docker-compose.prod.yml \
               logs -f backend

# アプリケーションログ（コンテナ内）
docker compose -f docker/docker-compose.yml \
               -f docker/docker-compose.prod.yml \
               exec backend cat /app/logs/application.log
```

---

## 10. 改訂履歴

| バージョン | 日付 | 変更内容 | 変更者 |
|-----------|------|---------|--------|
| 1.0 | 2026-03-26 | 初版作成 | GRC開発チーム |
