# 開発環境構築手順（Development Setup）

| 項目 | 内容 |
|------|------|
| 文書番号 | DEV-001 |
| バージョン | 1.0 |
| 作成日 | 2026-03-26 |
| 最終更新日 | 2026-03-26 |
| 作成者 | 開発チーム |
| 対象プロジェクト | 建設業 統合リスク＆コンプライアンス管理システム（Construction-GRC-System） |

---

## 1. 概要

本文書は、Construction-GRC-Systemの開発環境を構築するための手順を定める。新規メンバーのオンボーディングおよび環境再構築時に参照する。

---

## 2. 前提条件

### 2.1 必須ソフトウェア

| ソフトウェア | バージョン | 用途 |
|-------------|-----------|------|
| Python | 3.12.x | バックエンド開発（Django） |
| Node.js | 20.x LTS | フロントエンド開発（Vue.js） |
| npm | 10.x | パッケージ管理 |
| Docker | 24.x 以上 | コンテナ実行環境 |
| Docker Compose | 2.x 以上 | マルチコンテナ管理 |
| Git | 2.40 以上 | バージョン管理 |
| PostgreSQL | 16.x | データベース（Docker経由でも可） |
| Redis | 7.x | キャッシュ・メッセージブローカー（Docker経由でも可） |

### 2.2 推奨ツール

| ツール | 用途 |
|--------|------|
| Visual Studio Code | 統合開発環境 |
| DBeaver / pgAdmin | データベース管理 |
| Postman / Insomnia | API テスト |
| Docker Desktop | コンテナ管理GUI |

### 2.3 VS Code 推奨拡張機能

```
Python
Pylance
Ruff
Vue - Official (Volar)
ESLint
Prettier
Docker
GitLens
EditorConfig for VS Code
REST Client
```

### 2.4 ハードウェア要件

| 項目 | 最小要件 | 推奨要件 |
|------|---------|---------|
| CPU | 4コア | 8コア以上 |
| メモリ | 8GB | 16GB以上 |
| ストレージ | 20GB空き | 50GB空き（SSD推奨） |

---

## 3. セットアップ手順

### 3.1 リポジトリのクローン

```bash
# リポジトリをクローン
git clone https://github.com/<organization>/Construction-GRC-System.git
cd Construction-GRC-System
```

### 3.2 Docker を使用したセットアップ（推奨）

#### 3.2.1 環境変数ファイルの作成

```bash
# テンプレートからコピー
cp .env.example .env
```

`.env` ファイルを編集し、必要な値を設定する（詳細は「4. 環境変数設定」を参照）。

#### 3.2.2 Docker Compose によるサービス起動

```bash
# 全サービスをビルド＆起動
docker compose up -d --build

# ログ確認
docker compose logs -f

# サービス状態確認
docker compose ps
```

#### 3.2.3 データベースの初期化

```bash
# マイグレーション実行
docker compose exec backend python manage.py migrate

# 初期データ投入
docker compose exec backend python manage.py loaddata initial_data

# 管理者ユーザー作成
docker compose exec backend python manage.py createsuperuser
```

### 3.3 ローカル環境でのセットアップ

#### 3.3.1 Python環境のセットアップ

```bash
# Python バージョン確認
python3 --version  # 3.12.x であること

# 仮想環境の作成
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# pip のアップグレード
pip install --upgrade pip

# 依存パッケージのインストール
pip install -r requirements/development.txt

# 開発ツールのインストール
pip install -r requirements/dev-tools.txt
```

#### 3.3.2 Node.js環境のセットアップ

```bash
# Node.js バージョン確認
node --version  # 20.x であること

# フロントエンドディレクトリへ移動
cd frontend

# 依存パッケージのインストール
npm install

# 開発サーバー起動確認
npm run dev
```

#### 3.3.3 PostgreSQL のセットアップ

```bash
# Docker で PostgreSQL を起動（ローカルインストール不要）
docker run -d \
  --name grc-postgres \
  -e POSTGRES_DB=grc_db \
  -e POSTGRES_USER=grc_user \
  -e POSTGRES_PASSWORD=grc_password \
  -p 5432:5432 \
  postgres:16

# または、ローカルの PostgreSQL を使用
createdb grc_db
createuser grc_user
```

#### 3.3.4 Redis のセットアップ

```bash
# Docker で Redis を起動
docker run -d \
  --name grc-redis \
  -p 6379:6379 \
  redis:7-alpine
```

#### 3.3.5 バックエンドの起動

```bash
# マイグレーション
python manage.py migrate

# 開発サーバー起動
python manage.py runserver 0.0.0.0:8000
```

#### 3.3.6 Celery ワーカーの起動

```bash
# Celery ワーカー起動
celery -A config worker -l info

# Celery Beat（定期タスク）起動
celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

#### 3.3.7 フロントエンドの起動

```bash
cd frontend
npm run dev
```

### 3.4 起動確認

| サービス | URL | 説明 |
|---------|-----|------|
| フロントエンド | http://localhost:3000 | Vue.js 開発サーバー |
| バックエンドAPI | http://localhost:8000/api/ | Django REST Framework |
| API ドキュメント | http://localhost:8000/api/docs/ | Swagger UI |
| Django管理画面 | http://localhost:8000/admin/ | 管理者用画面 |
| Flower（Celery監視） | http://localhost:5555 | タスクモニタリング |

---

## 4. 環境変数設定

### 4.1 環境変数一覧

```ini
# ===========================================
# アプリケーション設定
# ===========================================
DJANGO_SETTINGS_MODULE=config.settings.development
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# ===========================================
# データベース設定
# ===========================================
DATABASE_URL=postgres://grc_user:grc_password@localhost:5432/grc_db
DB_HOST=localhost
DB_PORT=5432
DB_NAME=grc_db
DB_USER=grc_user
DB_PASSWORD=grc_password

# ===========================================
# Redis設定
# ===========================================
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# ===========================================
# メール設定（開発環境）
# ===========================================
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# ===========================================
# ログ設定
# ===========================================
LOG_LEVEL=DEBUG

# ===========================================
# CORS設定
# ===========================================
CORS_ALLOWED_ORIGINS=http://localhost:3000

# ===========================================
# JWT設定
# ===========================================
JWT_ACCESS_TOKEN_LIFETIME=60  # 分
JWT_REFRESH_TOKEN_LIFETIME=1440  # 分（24時間）

# ===========================================
# ファイルアップロード設定
# ===========================================
MAX_UPLOAD_SIZE=10485760  # 10MB
MEDIA_ROOT=/app/media
```

### 4.2 環境別設定ファイル

| 環境 | 設定ファイル | 用途 |
|------|-------------|------|
| 開発 | `.env.development` | ローカル開発環境 |
| テスト | `.env.test` | テスト実行環境 |
| ステージング | `.env.staging` | ステージング環境 |
| 本番 | `.env.production` | 本番環境（シークレット管理サービス使用） |

---

## 5. 開発用コマンド一覧

### 5.1 バックエンド

```bash
# マイグレーション作成
python manage.py makemigrations

# マイグレーション実行
python manage.py migrate

# テスト実行
pytest

# テスト（カバレッジ付き）
pytest --cov=apps --cov-report=html

# リンター実行
ruff check .

# フォーマッター実行
ruff format .

# 型チェック
mypy apps/

# シェル起動
python manage.py shell_plus

# 静的ファイル収集
python manage.py collectstatic
```

### 5.2 フロントエンド

```bash
cd frontend

# 開発サーバー起動
npm run dev

# ビルド
npm run build

# プレビュー
npm run preview

# リンター
npm run lint

# フォーマッター
npm run format

# 型チェック
npm run type-check

# ユニットテスト
npm run test:unit

# E2Eテスト
npm run test:e2e
```

### 5.3 Docker

```bash
# 全サービス起動
docker compose up -d

# 全サービス停止
docker compose down

# ログ確認
docker compose logs -f [サービス名]

# コンテナ内でコマンド実行
docker compose exec backend <コマンド>

# イメージ再ビルド
docker compose build --no-cache

# ボリューム含めて完全削除
docker compose down -v
```

---

## 6. ディレクトリ構成

```
Construction-GRC-System/
├── backend/                    # Django バックエンド
│   ├── apps/                   # Django アプリケーション
│   │   ├── accounts/           # ユーザー・認証管理
│   │   ├── risks/              # リスク管理（RSK）
│   │   ├── compliance/         # コンプライアンス管理（CMP）
│   │   ├── controls/           # 統制管理（CTL）
│   │   ├── audits/             # 監査管理（AUD）
│   │   ├── reports/            # レポート管理（RPT）
│   │   ├── notifications/      # 通知管理
│   │   └── common/             # 共通モジュール
│   ├── config/                 # Django 設定
│   │   ├── settings/           # 環境別設定
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── celery.py
│   ├── requirements/           # pip 依存パッケージ
│   ├── tests/                  # テストコード
│   └── manage.py
├── frontend/                   # Vue.js フロントエンド
│   ├── src/
│   │   ├── assets/             # 静的リソース
│   │   ├── components/         # 共通コンポーネント
│   │   ├── composables/        # Composition API
│   │   ├── layouts/            # レイアウト
│   │   ├── pages/              # ページコンポーネント
│   │   ├── plugins/            # プラグイン（Vuetify等）
│   │   ├── router/             # ルーティング
│   │   ├── services/           # API通信
│   │   ├── stores/             # Pinia ストア
│   │   ├── types/              # TypeScript型定義
│   │   └── utils/              # ユーティリティ
│   ├── public/
│   ├── tests/
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── docker/                     # Docker 設定
│   ├── backend/
│   ├── frontend/
│   └── nginx/
├── docs/                       # ドキュメント
├── docker-compose.yml
├── docker-compose.override.yml # 開発用オーバーライド
├── .env.example
├── .gitignore
└── README.md
```

---

## 7. トラブルシューティング

### 7.1 Docker関連

#### Docker Compose が起動しない

```
ERROR: Cannot connect to the Docker daemon
```

**原因**: Docker デーモンが起動していない。

**対処法**:
```bash
# Linux
sudo systemctl start docker

# macOS/Windows
# Docker Desktop を起動する
```

#### ポートが既に使用されている

```
ERROR: Bind for 0.0.0.0:5432 failed: port is already allocated
```

**対処法**:
```bash
# 使用中のプロセスを確認
lsof -i :5432

# プロセスを停止するか、docker-compose.override.yml でポートを変更
```

#### コンテナのディスク容量不足

**対処法**:
```bash
# 不要なイメージ・コンテナ・ボリュームを削除
docker system prune -a --volumes
```

### 7.2 Python/Django関連

#### ImportError: モジュールが見つからない

**対処法**:
```bash
# 仮想環境が有効か確認
which python

# パッケージを再インストール
pip install -r requirements/development.txt
```

#### マイグレーションの競合

**対処法**:
```bash
# マイグレーションの状態確認
python manage.py showmigrations

# マイグレーションのマージ
python manage.py makemigrations --merge
```

#### データベース接続エラー

**対処法**:
```bash
# PostgreSQL が起動しているか確認
docker compose ps postgres

# 接続テスト
psql -h localhost -U grc_user -d grc_db
```

### 7.3 Node.js/Vue.js関連

#### npm install が失敗する

**対処法**:
```bash
# キャッシュをクリア
npm cache clean --force

# node_modules を削除して再インストール
rm -rf node_modules package-lock.json
npm install
```

#### Vite 開発サーバーが起動しない

**対処法**:
```bash
# Node.js バージョンを確認（20.x必須）
node --version

# ポートの競合を確認
lsof -i :3000
```

### 7.4 Celery関連

#### Celery ワーカーが Redis に接続できない

**対処法**:
```bash
# Redis が起動しているか確認
docker compose ps redis

# Redis への接続テスト
redis-cli ping
```

#### タスクが実行されない

**対処法**:
```bash
# ワーカーのログを確認
celery -A config inspect active

# タスクの登録状況確認
celery -A config inspect registered
```

---

## 8. 開発環境のリセット

開発環境を完全にリセットする場合は以下の手順を実行する。

```bash
# 全コンテナ・ボリュームを削除
docker compose down -v

# Python仮想環境を再作成
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements/development.txt

# フロントエンドの依存を再インストール
cd frontend
rm -rf node_modules
npm install

# Docker環境を再構築
cd ..
docker compose up -d --build

# データベースの再初期化
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py loaddata initial_data
docker compose exec backend python manage.py createsuperuser
```

---

## 改訂履歴

| バージョン | 日付 | 変更内容 | 変更者 |
|-----------|------|---------|--------|
| 1.0 | 2026-03-26 | 初版作成 | 開発チーム |
