# デプロイガイド -- Construction-GRC-System

## 前提条件
- Docker 24+ / Docker Compose v2
- PostgreSQL 16
- Redis 7
- ドメイン名 + SSL証明書（本番）

## クイックデプロイ（Docker Compose）

### 1. 環境変数設定
```bash
cp .env.production.example .env.production
vi .env.production  # SECRET_KEY, DB設定等を編集
```

### 2. ビルド & 起動
```bash
docker compose -f docker-compose.prod.yml up -d --build
```

### 3. 初期データ投入
```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
docker compose -f docker-compose.prod.yml exec backend python manage.py loaddata apps/frameworks/fixtures/frameworks.json
docker compose -f docker-compose.prod.yml exec backend python manage.py loaddata apps/frameworks/fixtures/iso27001_controls.json
docker compose -f docker-compose.prod.yml exec backend python manage.py loaddata apps/frameworks/fixtures/nist_csf_2.json
docker compose -f docker-compose.prod.yml exec backend python manage.py loaddata apps/frameworks/fixtures/construction_regs.json
```

### 4. 確認
```bash
curl http://localhost/api/health/
```

## SSL (Let's Encrypt)
certbot による証明書取得の手順（Nginx設定変更が必要）

## ローリングアップデート
```bash
git pull origin main
docker compose -f docker-compose.prod.yml up -d --build --no-deps backend frontend
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate --no-input
```

## ロールバック
```bash
docker compose -f docker-compose.prod.yml down
git checkout <previous-tag>
docker compose -f docker-compose.prod.yml up -d --build
```
