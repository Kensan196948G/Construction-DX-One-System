# インフラ設計書（Infrastructure Design）

## 建設業 統合リスク＆コンプライアンス管理システム（Construction-GRC-System）

| 項目 | 内容 |
|------|------|
| **文書番号** | DES-GRC-007 |
| **バージョン** | 1.0.0 |
| **作成日** | 2026-03-26 |
| **最終更新日** | 2026-03-26 |
| **作成者** | みらい建設工業 IT部門 |
| **関連文書** | DES-GRC-001（システムアーキテクチャ設計書）、REQ-GRC-003（非機能要件一覧） |

---

## 改訂履歴

| バージョン | 日付 | 変更内容 | 変更者 |
|-----------|------|---------|--------|
| 1.0.0 | 2026-03-26 | 初版作成 | IT部門 |

---

## 1. インフラ設計方針

### 1.1 基本方針

| 方針 | 説明 |
|------|------|
| コンテナファースト | 全コンポーネントをDockerコンテナで管理 |
| Infrastructure as Code | Docker Compose / Azure Resource Managerによる構成管理 |
| 環境の一貫性 | 開発/ステージング/本番で同一コンテナイメージを使用 |
| スケーラビリティ | 水平・垂直スケーリングが可能な設計 |
| 障害復旧 | RTO 4時間、RPO 1時間の達成 |

---

## 2. Docker Compose構成（開発環境）

### 2.1 docker-compose.yml

```yaml
version: '3.9'

services:
  # ===== Nginx (Reverse Proxy) =====
  nginx:
    image: nginx:1.25-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./infrastructure/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./infrastructure/nginx/ssl:/etc/nginx/ssl:ro
      - static_files:/var/www/static:ro
      - media_files:/var/www/media:ro
    depends_on:
      - backend
      - frontend
    restart: unless-stopped

  # ===== Backend (Django + DRF) =====
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
      target: development
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - ./backend:/app
      - media_files:/app/media
      - static_files:/app/staticfiles
    environment:
      - DJANGO_SETTINGS_MODULE=grc.settings.development
      - DATABASE_URL=postgresql://grc_user:grc_password@db:5432/grc_db
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - SECRET_KEY=${DJANGO_SECRET_KEY:-development-secret-key}
      - DEBUG=true
      - ALLOWED_HOSTS=localhost,127.0.0.1,backend
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/api/health/')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # ===== Frontend (Vue.js 3 + Vuetify 3) =====
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      target: development
    command: npm run dev -- --host 0.0.0.0 --port 3000
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - VITE_API_BASE_URL=http://localhost:8000/api/v1
    ports:
      - "3000:3000"
    restart: unless-stopped

  # ===== PostgreSQL 16 =====
  db:
    image: postgres:16-alpine
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./infrastructure/db/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    environment:
      - POSTGRES_DB=grc_db
      - POSTGRES_USER=grc_user
      - POSTGRES_PASSWORD=grc_password
      - POSTGRES_INITDB_ARGS=--encoding=UTF-8 --locale=ja_JP.UTF-8
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U grc_user -d grc_db"]
      interval: 10s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 512M

  # ===== Redis 7 =====
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 128M

  # ===== Celery Worker =====
  celery:
    build:
      context: ./backend
      dockerfile: Dockerfile
      target: development
    command: celery -A grc worker --loglevel=info --concurrency=4
    volumes:
      - ./backend:/app
      - media_files:/app/media
    environment:
      - DJANGO_SETTINGS_MODULE=grc.settings.development
      - DATABASE_URL=postgresql://grc_user:grc_password@db:5432/grc_db
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 256M

  # ===== Celery Beat (Scheduler) =====
  celery_beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
      target: development
    command: celery -A grc beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    volumes:
      - ./backend:/app
    environment:
      - DJANGO_SETTINGS_MODULE=grc.settings.development
      - DATABASE_URL=postgresql://grc_user:grc_password@db:5432/grc_db
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

volumes:
  pgdata:
    driver: local
  redis_data:
    driver: local
  media_files:
    driver: local
  static_files:
    driver: local
```

### 2.2 Backend Dockerfile

```dockerfile
# Multi-stage build
FROM python:3.11-slim as base
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Development stage
FROM base as development
COPY requirements/base.txt requirements/development.txt ./requirements/
RUN pip install --no-cache-dir -r requirements/development.txt
COPY . .

# Production stage
FROM base as production
COPY requirements/base.txt requirements/production.txt ./requirements/
RUN pip install --no-cache-dir -r requirements/production.txt
COPY . .
RUN python manage.py collectstatic --noinput
CMD ["gunicorn", "grc.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--threads", "2", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
```

---

## 3. 本番環境設計（Azure）

### 3.1 Azure構成図

```
+------------------------------------------------------------------+
| Azure Subscription                                                |
|                                                                    |
|  +------------------+                                             |
|  | Azure Front Door |  (WAF / CDN / TLS Termination)              |
|  | + WAF Policy     |                                             |
|  +--------+---------+                                             |
|           |                                                        |
|  +--------v---------+                                             |
|  | App Service Plan  |  (Linux / P1v3)                            |
|  |                   |                                             |
|  | +---------------+ |  +-----------------------+                  |
|  | | App Service   | |  | Azure DB for          |                  |
|  | | (Django+      | +--| PostgreSQL             |                  |
|  | |  Gunicorn)    | |  | Flexible Server        |                  |
|  | | Instances: 2  | |  | (General Purpose D2s)  |                  |
|  | +---------------+ |  | HA: Zone Redundant     |                  |
|  +-------------------+  +-----------------------+                  |
|                                                                    |
|  +-------------------+  +-----------------------+                  |
|  | Azure Container   |  | Azure Cache for Redis  |                  |
|  | Instances         |  | (Standard C1)          |                  |
|  | (Celery Worker x2)|  | HA: Zone Redundant     |                  |
|  | (Celery Beat x1)  |  +-----------------------+                  |
|  +-------------------+                                             |
|                                                                    |
|  +-------------------+  +-----------------------+                  |
|  | Azure Blob        |  | Azure Key Vault        |                  |
|  | Storage           |  | (シークレット管理)       |                  |
|  | (証跡ファイル)     |  |                         |                  |
|  | GRS冗長           |  |                         |                  |
|  +-------------------+  +-----------------------+                  |
|                                                                    |
|  +-------------------+  +-----------------------+                  |
|  | Azure Monitor     |  | Log Analytics          |                  |
|  | (監視・アラート)   |  | Workspace              |                  |
|  |                   |  | (ログ集約・分析)         |                  |
|  +-------------------+  +-----------------------+                  |
|                                                                    |
|  +-------------------+                                             |
|  | Azure Backup      |                                             |
|  | (PostgreSQL自動    |                                             |
|  |  バックアップ)     |                                             |
|  +-------------------+                                             |
+------------------------------------------------------------------+
```

### 3.2 Azureリソース一覧

| リソース | SKU/プラン | 構成 | 月額概算 |
|---------|----------|------|---------|
| Azure Front Door | Standard | WAF + CDN | 4,000円 |
| App Service Plan | P1v3 (Linux) | 2 CPU / 8 GB RAM | 20,000円 |
| App Service | - | 2インスタンス | (Plan含む) |
| Azure DB for PostgreSQL | General Purpose D2s | 2 vCore / 8GB / 128GB | 25,000円 |
| Azure Cache for Redis | Standard C1 | 1GB | 8,000円 |
| Azure Container Instances | 2 vCPU / 4GB x3 | Worker x2 + Beat x1 | 15,000円 |
| Azure Blob Storage | StorageV2 GRS | 100GB | 3,000円 |
| Azure Key Vault | Standard | シークレット管理 | 500円 |
| Azure Monitor | - | メトリクス + アラート | 5,000円 |
| Log Analytics | Per GB | ログ集約 | 5,000円 |
| Azure Backup | - | PostgreSQL自動バックアップ | 3,000円 |
| **合計** | | | **約88,500円/月** |

### 3.3 ネットワーク構成

| 要素 | 構成 |
|------|------|
| Virtual Network | 10.0.0.0/16 |
| App Serviceサブネット | 10.0.1.0/24 |
| DBサブネット | 10.0.2.0/24（Private Endpoint） |
| Redisサブネット | 10.0.3.0/24（Private Endpoint） |
| NSG | App Service → DB (5432), App Service → Redis (6379) のみ許可 |

---

## 4. スケーリング戦略

### 4.1 水平スケーリング

| コンポーネント | スケーリング方式 | 最小 | 最大 | トリガー |
|--------------|---------------|------|------|---------|
| App Service | 自動スケール | 2 | 4 | CPU 70%超 / メモリ 80%超 |
| Celery Worker | 手動（ACI追加） | 2 | 4 | キュー長 100超 |
| Redis | 手動（SKU変更） | C1 | C3 | メモリ 80%超 |
| PostgreSQL | リードレプリカ追加 | 1 | 3 | Read IOPS上限 |

### 4.2 垂直スケーリング

| コンポーネント | 初期 | 最大 | スケールアップ条件 |
|--------------|------|------|----------------|
| App Service | P1v3 (2C/8G) | P3v3 (8C/32G) | 持続的なCPU/メモリ不足 |
| PostgreSQL | D2s (2C/8G) | D8s (8C/32G) | クエリ性能劣化 |
| Redis | C1 (1GB) | C3 (6GB) | ヒット率低下 |

---

## 5. バックアップ・DR設計

### 5.1 バックアップ戦略

| バックアップ種別 | 頻度 | 保持期間 | 保管場所 | 方式 |
|---------------|------|---------|---------|------|
| PostgreSQL フルバックアップ | 日次 2:00 | 3世代（3日分） | Azure Backup | Azure自動バックアップ |
| PostgreSQL 差分バックアップ | 6時間ごと | 直近24時間 | Azure Backup | Azure自動バックアップ |
| PostgreSQL WALログ | 15分ごと | 直近72時間 | Azure Backup | PITR対応 |
| Blob Storage（証跡） | GRS自動複製 | - | 別リージョン | Azure自動レプリケーション |
| システム設定 | 変更時 | 10世代 | Git | IaC管理 |

### 5.2 リストア手順サマリ

| シナリオ | 手順 | 想定時間 |
|---------|------|---------|
| DBデータ破損 | Azure PostgreSQL のPITR（ポイントインタイムリカバリ） | 30分〜1時間 |
| 証跡ファイル消失 | Blob Storage GRSからの復元 | 1時間 |
| AZリージョン障害 | DRリージョンへの切替 | 2〜4時間 |
| アプリケーション障害 | 前バージョンへのロールバック | 10分 |

### 5.3 DR（災害復旧）設計

| 項目 | 設計値 |
|------|--------|
| RTO（目標復旧時間） | 4時間 |
| RPO（目標復旧時点） | 1時間 |
| DR方式 | ウォームスタンバイ（別リージョン） |
| DRリージョン | Japan West（東京→大阪） |
| データ同期 | PostgreSQL: Geo-Replication / Blob: GRS |
| DRテスト | 年2回の切替テスト |

---

## 6. 監視・アラート設計

### 6.1 監視項目

| 監視対象 | メトリクス | 閾値 | アラート先 |
|---------|----------|------|----------|
| App Service | CPU使用率 | 80%超（5分継続） | Slack + メール |
| App Service | メモリ使用率 | 90%超 | Slack + メール |
| App Service | HTTP 5xx率 | 1%超 | Slack + PagerDuty |
| App Service | 応答時間（p95） | 3秒超 | Slack |
| PostgreSQL | CPU使用率 | 80%超 | Slack + メール |
| PostgreSQL | ストレージ使用率 | 80%超 | Slack + メール |
| PostgreSQL | 接続数 | 80%超 | Slack |
| PostgreSQL | スロークエリ | 1秒超 | ログ記録 |
| Redis | メモリ使用率 | 80%超 | Slack |
| Redis | ヒット率 | 90%未満 | ログ記録 |
| Celery | キュー長 | 100超 | Slack |
| Celery | タスク失敗率 | 5%超 | Slack + メール |

### 6.2 ログ集約

| ログソース | 送信先 | 保持期間 |
|-----------|--------|---------|
| App Service ログ | Log Analytics | 90日 |
| PostgreSQL ログ | Log Analytics | 90日 |
| Nginx アクセスログ | Log Analytics | 90日 |
| 監査ログ | Log Analytics + PostgreSQL | 5年（PostgreSQL） |
| セキュリティログ | Log Analytics + Sentinel | 5年 |

### 6.3 ヘルスチェック

| エンドポイント | チェック内容 | 間隔 |
|-------------|-----------|------|
| /api/health/ | Django起動確認 | 30秒 |
| /api/health/db/ | PostgreSQL接続確認 | 30秒 |
| /api/health/redis/ | Redis接続確認 | 30秒 |
| /api/health/celery/ | Celery Worker応答確認 | 60秒 |

---

## 7. CI/CD パイプライン

### 7.1 CI パイプライン（GitHub Actions）

```yaml
# .github/workflows/ci.yml
name: CI
on:
  pull_request:
    branches: [main, develop]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Python Lint (flake8, black, isort)
        run: |
          pip install flake8 black isort mypy
          flake8 backend/
          black --check backend/
          isort --check-only backend/
      - name: Frontend Lint (ESLint)
        run: |
          cd frontend && npm ci && npm run lint

  test-backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: test_grc
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
        ports: ["5432:5432"]
      redis:
        image: redis:7-alpine
        ports: ["6379:6379"]
    steps:
      - uses: actions/checkout@v4
      - name: Run Tests
        run: |
          cd backend
          pip install -r requirements/development.txt
          pytest --cov=apps --cov-report=xml -v
      - name: Coverage Check
        run: |
          coverage report --fail-under=80

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Tests
        run: |
          cd frontend && npm ci && npm run test

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Python Security (Bandit + Safety)
        run: |
          pip install bandit safety
          bandit -r backend/apps/ -ll
          safety check -r backend/requirements/base.txt
      - name: Container Scan (Trivy)
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          severity: 'CRITICAL,HIGH'

  build:
    runs-on: ubuntu-latest
    needs: [lint, test-backend, test-frontend, security]
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker Images
        run: |
          docker compose build --no-cache
```

### 7.2 CD パイプライン

```yaml
# .github/workflows/cd.yml
name: CD
on:
  push:
    branches: [main]

jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - name: Build & Push to ACR
        run: |
          docker build -t grc-backend:${{ github.sha }} ./backend --target production
          az acr login --name grcregistry
          docker push grcregistry.azurecr.io/grc-backend:${{ github.sha }}
      - name: Deploy to Staging
        run: |
          az webapp config container set --name grc-staging ...

  deploy-production:
    runs-on: ubuntu-latest
    needs: deploy-staging
    environment: production  # 手動承認必須
    steps:
      - name: Deploy to Production
        run: |
          az webapp config container set --name grc-production ...
      - name: Health Check
        run: |
          curl -f https://grc.example.com/api/health/ || exit 1
```

---

## 8. 環境構成

### 8.1 環境一覧

| 環境 | 用途 | インフラ | データ | URL |
|------|------|---------|--------|-----|
| 開発（Dev） | ローカル開発 | Docker Compose | テストデータ | http://localhost:3000 |
| ステージング（Stg） | 結合テスト・UAT | Azure（本番同等） | 匿名化本番データ | https://grc-stg.example.com |
| 本番（Prod） | 実運用 | Azure（冗長構成） | 本番データ | https://grc.example.com |

### 8.2 環境変数管理

| 変数 | 開発 | ステージング | 本番 |
|------|------|-----------|------|
| DJANGO_SETTINGS_MODULE | grc.settings.development | grc.settings.staging | grc.settings.production |
| DEBUG | true | false | false |
| DATABASE_URL | .env | Azure Key Vault | Azure Key Vault |
| SECRET_KEY | .env | Azure Key Vault | Azure Key Vault |
| ALLOWED_HOSTS | localhost | grc-stg.example.com | grc.example.com |
| CORS_ALLOWED_ORIGINS | http://localhost:3000 | https://grc-stg.example.com | https://grc.example.com |

---

## 9. 運用設計

### 9.1 定期メンテナンス

| 作業 | 頻度 | 時間帯 | 影響 |
|------|------|--------|------|
| OS/ランタイムパッチ | 月次 | 日曜 0:00-4:00 | サービス停止（ローリングアップデート時は無停止） |
| PostgreSQL VACUUM | 週次（自動） | 深夜 | 軽微な性能影響 |
| PostgreSQL REINDEX | 月次 | 日曜 2:00 | 軽微な性能影響 |
| ログアーカイブ | 月次 | 月初 1:00 | なし |
| リストアテスト | 月次 | 任意 | なし（テスト環境） |
| SSL証明書更新 | 自動（Let's Encrypt）/ 年次（Azure） | - | なし |

### 9.2 デプロイ手順

| ステップ | 手順 | ロールバック |
|---------|------|-----------|
| 1 | PRマージ → CI自動実行 | - |
| 2 | Dockerイメージビルド・プッシュ | - |
| 3 | ステージングデプロイ（自動） | 前バージョンイメージに切替 |
| 4 | ステージングテスト | - |
| 5 | 本番デプロイ（手動承認後） | 前バージョンイメージに切替 |
| 6 | ヘルスチェック | 異常時は自動ロールバック |
| 7 | スモークテスト | - |

### 9.3 障害対応

| 障害レベル | 定義 | 初動 | 復旧目標 |
|-----------|------|------|---------|
| P1（緊急） | 全サービス停止 | 15分以内 | 2時間 |
| P2（重大） | 主要機能停止 | 30分以内 | 4時間 |
| P3（中度） | 一部機能障害 | 1時間以内 | 8時間 |
| P4（軽微） | 軽微な不具合 | 4時間以内 | 次営業日 |

---

*文書管理: 本文書はバージョン管理対象とし、インフラ構成変更時は改訂履歴を更新すること。*
