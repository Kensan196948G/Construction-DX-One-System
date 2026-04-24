# デプロイメント手順書
## IT変更管理・リリース自動化プラットフォーム（IT-Change-CAB-Platform）

| 項目 | 内容 |
|------|------|
| **文書番号** | REL-CAB-002 |
| **バージョン** | 1.0.0 |
| **作成日** | 2026-03-26 |
| **作成者** | みらい建設工業 IT部門 |
| **対象リポジトリ** | Kensan196948G/IT-Change-CAB-Platform |

---

## 1. デプロイメント概要

### 1.1 デプロイメント方式

| 項目 | 内容 |
|------|------|
| コンテナ基盤 | Docker Compose |
| デプロイ方式 | ローリングアップデート（Docker Compose） |
| イメージ管理 | GitHub Container Registry (ghcr.io) |
| 環境変数管理 | .env ファイル（環境別） |
| マイグレーション | node-pg-migrate（自動実行） |

### 1.2 環境構成

| 環境 | 用途 | Docker Compose ファイル | URL |
|------|------|----------------------|-----|
| 開発 | 開発・デバッグ | docker-compose.dev.yml | http://localhost:3000 |
| ステージング | テスト・検証 | docker-compose.staging.yml | https://stg-cab.mirai-kensetsu.co.jp |
| 本番 | 本番運用 | docker-compose.prod.yml | https://cab.mirai-kensetsu.co.jp |

---

## 2. Docker Compose構成

### 2.1 本番環境 Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.9'

services:
  backend:
    image: ghcr.io/kensan196948g/cab-platform-backend:${APP_VERSION}
    restart: always
    environment:
      NODE_ENV: production
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
      REDIS_URL: redis://redis:6379/0
      JWT_SECRET: ${JWT_SECRET}
      TEAMS_WEBHOOK_URL: ${TEAMS_WEBHOOK_URL}
      SMTP_HOST: ${SMTP_HOST}
      SMTP_PORT: ${SMTP_PORT}
      SMTP_USER: ${SMTP_USER}
      SMTP_PASSWORD: ${SMTP_PASSWORD}
      LOG_LEVEL: info
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "5"

  frontend:
    image: ghcr.io/kensan196948g/cab-platform-frontend:${APP_VERSION}
    restart: always
    ports:
      - "3000:80"
    depends_on:
      - backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:80"]
      interval: 60s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M

  db:
    image: postgres:16-alpine
    restart: always
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./backup/db:/backup
    ports:
      - "127.0.0.1:5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d ${DB_NAME}"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
    command: >
      postgres
        -c max_connections=100
        -c shared_buffers=1GB
        -c effective_cache_size=3GB
        -c maintenance_work_mem=256MB
        -c checkpoint_completion_target=0.9
        -c wal_buffers=16MB
        -c default_statistics_target=100
        -c random_page_cost=1.1
        -c effective_io_concurrency=200
        -c log_min_duration_statement=1000
        -c log_statement=ddl

  redis:
    image: redis:7-alpine
    restart: always
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru --appendonly yes
    volumes:
      - redisdata:/data
    ports:
      - "127.0.0.1:6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 5s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M

  worker:
    image: ghcr.io/kensan196948g/cab-platform-backend:${APP_VERSION}
    restart: always
    command: node dist/jobs/worker.js
    environment:
      NODE_ENV: production
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
      REDIS_URL: redis://redis:6379/0
      TEAMS_WEBHOOK_URL: ${TEAMS_WEBHOOK_URL}
      SMTP_HOST: ${SMTP_HOST}
      SMTP_PORT: ${SMTP_PORT}
      SMTP_USER: ${SMTP_USER}
      SMTP_PASSWORD: ${SMTP_PASSWORD}
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2G

  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - backend
      - frontend

volumes:
  pgdata:
    driver: local
  redisdata:
    driver: local
```

---

## 3. デプロイ手順

### 3.1 通常デプロイ手順

#### Step 1: 事前準備

```bash
# 1. デプロイ対象バージョン確認
echo "デプロイバージョン: ${APP_VERSION}"

# 2. リリースチェックリスト確認（全項目チェック済みであること）

# 3. 本番サーバーにSSH接続
ssh cab-platform-prod

# 4. 作業ディレクトリに移動
cd /opt/cab-platform
```

#### Step 2: バックアップ取得

```bash
# 1. データベースバックアップ
./scripts/backup.sh
echo "バックアップファイル確認:"
ls -la /backup/db/ | tail -1

# 2. 現在のバージョン記録
docker compose exec backend node -e "console.log(require('./package.json').version)" > /tmp/prev_version.txt
cat /tmp/prev_version.txt

# 3. Docker イメージのタグ記録
docker compose images > /tmp/prev_images.txt
```

#### Step 3: メンテナンスモード有効化

```bash
# メンテナンスモード有効化
curl -X POST http://localhost:8000/api/v1/admin/maintenance \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "message": "システムアップデート中です。終了予定: XX:XX"
  }'
```

#### Step 4: イメージ取得・更新

```bash
# 1. 環境変数ファイル更新（必要な場合）
vim .env.prod
# APP_VERSION=1.2.0 に更新

# 2. .env ファイルの読み込み
export $(cat .env.prod | xargs)

# 3. 新しいイメージのプル
docker compose -f docker-compose.prod.yml pull

# 4. イメージ確認
docker images | grep cab-platform
```

#### Step 5: データベースマイグレーション

```bash
# 1. マイグレーション内容確認（ドライラン）
docker compose -f docker-compose.prod.yml run --rm backend npm run migrate:status

# 2. マイグレーション実行
docker compose -f docker-compose.prod.yml run --rm backend npm run migrate:up

# 3. マイグレーション結果確認
docker compose -f docker-compose.prod.yml run --rm backend npm run migrate:status
```

#### Step 6: サービス更新

```bash
# 1. バックエンド + ワーカー更新
docker compose -f docker-compose.prod.yml up -d --no-deps backend worker

# 2. 起動確認（30秒待機）
sleep 30
docker compose -f docker-compose.prod.yml ps

# 3. ヘルスチェック
curl -f http://localhost:8000/api/v1/health
echo ""

# 4. フロントエンド更新
docker compose -f docker-compose.prod.yml up -d --no-deps frontend

# 5. 全サービス起動確認
docker compose -f docker-compose.prod.yml ps
```

#### Step 7: スモークテスト

```bash
# 1. APIヘルスチェック
curl -f http://localhost:8000/api/v1/health | jq .

# 2. フロントエンドアクセス確認
curl -f -o /dev/null -w "%{http_code}" http://localhost:3000

# 3. 認証テスト
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"smoke_test_user","password":"test_password"}' | jq .status

# 4. RFC一覧API確認
curl -f http://localhost:8000/api/v1/rfcs?limit=1 \
  -H "Authorization: Bearer $TEST_TOKEN" | jq .

# 5. バージョン確認
curl http://localhost:8000/api/v1/health | jq .version
```

#### Step 8: メンテナンスモード解除・完了

```bash
# 1. メンテナンスモード解除
curl -X POST http://localhost:8000/api/v1/admin/maintenance \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'

# 2. 古いDockerイメージ削除
docker image prune -f

# 3. デプロイ完了通知（Teams）
curl -X POST "$TEAMS_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d "{
    \"text\": \"CAB Platform v${APP_VERSION} デプロイ完了\"
  }"
```

---

## 4. ロールバック手順

### 4.1 ロールバック判断基準

| 条件 | 判断 |
|------|------|
| ヘルスチェック失敗 | 即時ロールバック |
| スモークテスト失敗 | 即時ロールバック |
| 重大バグ発見 | 30分以内にロールバック判断 |
| 性能劣化（応答時間2倍以上） | 1時間以内にロールバック判断 |

### 4.2 ロールバック手順

```bash
# 1. 前バージョンの確認
PREV_VERSION=$(cat /tmp/prev_version.txt)
echo "ロールバック先: v${PREV_VERSION}"

# 2. メンテナンスモード有効化
curl -X POST http://localhost:8000/api/v1/admin/maintenance \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"enabled": true, "message": "緊急メンテナンス中"}'

# 3. 環境変数を前バージョンに戻す
sed -i "s/APP_VERSION=.*/APP_VERSION=${PREV_VERSION}/" .env.prod
export $(cat .env.prod | xargs)

# 4. DBマイグレーション ロールバック（必要な場合）
docker compose -f docker-compose.prod.yml run --rm backend npm run migrate:down

# 5. 前バージョンのイメージでサービス再起動
docker compose -f docker-compose.prod.yml up -d --no-deps backend worker frontend

# 6. ヘルスチェック
sleep 30
curl -f http://localhost:8000/api/v1/health | jq .

# 7. メンテナンスモード解除
curl -X POST http://localhost:8000/api/v1/admin/maintenance \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"enabled": false}'

# 8. ロールバック通知
curl -X POST "$TEAMS_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d "{
    \"text\": \"[緊急] CAB Platform ロールバック実施: v${APP_VERSION} → v${PREV_VERSION}\"
  }"
```

### 4.3 データベースロールバック（重大な場合）

```bash
# バックアップからのフルリストア
BACKUP_FILE=$(ls -t /backup/db/*.dump | head -1)
echo "リストア元: ${BACKUP_FILE}"

# サービス停止
docker compose -f docker-compose.prod.yml stop backend worker

# データベースリストア
docker compose -f docker-compose.prod.yml exec -T db pg_restore \
  -U ${DB_USER} -d ${DB_NAME} --clean --if-exists < ${BACKUP_FILE}

# サービス再起動
docker compose -f docker-compose.prod.yml up -d backend worker
```

---

## 5. 環境変数管理

### 5.1 環境変数一覧

| 変数名 | 説明 | 開発 | ステージング | 本番 |
|--------|------|------|------------|------|
| `NODE_ENV` | 実行環境 | development | staging | production |
| `APP_VERSION` | アプリバージョン | latest | リリース版 | リリース版 |
| `DATABASE_URL` | DB接続文字列 | localhost | stg-db | prod-db |
| `REDIS_URL` | Redis接続文字列 | localhost | stg-redis | prod-redis |
| `JWT_SECRET` | JWT署名鍵 | dev-secret | stg-secret | 本番用強力な鍵 |
| `TEAMS_WEBHOOK_URL` | Teams通知URL | テスト用 | テスト用 | 本番用 |
| `SMTP_HOST` | メールサーバー | mailhog | stg-smtp | prod-smtp |
| `SMTP_PORT` | メールポート | 1025 | 587 | 587 |
| `SMTP_USER` | メールユーザー | - | stg-user | prod-user |
| `SMTP_PASSWORD` | メールパスワード | - | stg-pass | 本番用パスワード |
| `DB_USER` | DBユーザー | admin | stg_admin | prod_admin |
| `DB_PASSWORD` | DBパスワード | password | stg-pass | 本番用強力なパスワード |
| `DB_NAME` | DB名 | cab_platform_dev | cab_platform_stg | cab_platform |
| `LOG_LEVEL` | ログレベル | debug | info | info |
| `CORS_ORIGIN` | CORS許可オリジン | * | stg-domain | prod-domain |

### 5.2 機密情報の管理

| 機密情報 | 管理方法 |
|---------|---------|
| JWT_SECRET | 環境変数ファイル（.env.prod）、サーバー上のみ保管 |
| DB_PASSWORD | 環境変数ファイル、定期ローテーション（90日） |
| SMTP_PASSWORD | 環境変数ファイル |
| TEAMS_WEBHOOK_URL | 環境変数ファイル |

**注意事項:**
- `.env.prod` ファイルはGitリポジトリにコミットしない（`.gitignore`に追加済み）
- 本番環境の機密情報はサーバー上のみに保管
- アクセス権限は運用担当者のみに限定（chmod 600）

---

## 6. CI/CDパイプライン

### 6.1 GitHub Actions ワークフロー

```yaml
# .github/workflows/deploy.yml
name: Build and Deploy

on:
  push:
    tags:
      - 'v*'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - run: npm run lint
      - run: npm run type-check
      - run: npm test -- --coverage

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Docker イメージビルド
        run: |
          docker build -t ghcr.io/kensan196948g/cab-platform-backend:${{ github.ref_name }} ./backend
          docker build -t ghcr.io/kensan196948g/cab-platform-frontend:${{ github.ref_name }} ./frontend
      - name: GitHub Container Registry にプッシュ
        run: |
          echo "${{ secrets.GITHUB_TOKEN }}" | docker login ghcr.io -u ${{ github.actor }} --password-stdin
          docker push ghcr.io/kensan196948g/cab-platform-backend:${{ github.ref_name }}
          docker push ghcr.io/kensan196948g/cab-platform-frontend:${{ github.ref_name }}

  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - name: ステージング環境デプロイ
        run: |
          ssh ${{ secrets.STG_SSH_HOST }} "
            cd /opt/cab-platform
            export APP_VERSION=${{ github.ref_name }}
            docker compose -f docker-compose.staging.yml pull
            docker compose -f docker-compose.staging.yml up -d
          "

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: 本番環境デプロイ（手動承認後）
        run: |
          ssh ${{ secrets.PROD_SSH_HOST }} "
            cd /opt/cab-platform
            ./scripts/backup.sh
            export APP_VERSION=${{ github.ref_name }}
            docker compose -f docker-compose.prod.yml pull
            docker compose -f docker-compose.prod.yml up -d
            sleep 30
            curl -f http://localhost:8000/api/v1/health
          "
```

---

## 7. トラブルシューティング

| 問題 | 原因 | 対処 |
|------|------|------|
| コンテナが起動しない | イメージ取得失敗 | `docker compose pull` を再実行、ネットワーク確認 |
| DB接続エラー | マイグレーション未実行 | `npm run migrate:up` を実行 |
| ヘルスチェック失敗 | 依存サービス未起動 | `docker compose ps` で確認、依存サービスを先に起動 |
| ポート競合 | 別プロセスがポート使用中 | `lsof -i :8000` で確認、競合プロセス停止 |
| ディスク容量不足 | 古いイメージ蓄積 | `docker system prune -f` で不要リソース削除 |
| 環境変数未設定 | .env ファイル未読込 | `export $(cat .env.prod \| xargs)` で読込 |

---

*文書管理：本文書はバージョン管理対象。変更時はバージョン番号を更新すること。*
