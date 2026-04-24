# 開発環境構築ガイド
## IT変更管理・リリース自動化プラットフォーム（IT-Change-CAB-Platform）

| 項目 | 内容 |
|------|------|
| **文書番号** | DEV-CAB-001 |
| **バージョン** | 1.0.0 |
| **作成日** | 2026-03-26 |
| **作成者** | みらい建設工業 IT部門 |
| **対象リポジトリ** | Kensan196948G/IT-Change-CAB-Platform |

---

## 1. 前提条件

### 1.1 必要なソフトウェア

| ソフトウェア | バージョン | 用途 |
|------------|-----------|------|
| Node.js | 20.x LTS | バックエンド/フロントエンド実行環境 |
| npm | 10.x | パッケージ管理 |
| Docker | 24.x 以上 | コンテナ実行環境 |
| Docker Compose | v2.x | マルチコンテナ管理 |
| Git | 2.x | バージョン管理 |
| VS Code | 最新版 | 推奨エディタ |

### 1.2 推奨スペック

| 項目 | 最小要件 | 推奨 |
|------|---------|------|
| CPU | 2コア | 4コア以上 |
| メモリ | 8GB | 16GB以上 |
| ディスク | 20GB空き | 50GB以上空き |
| OS | Windows 10/11、macOS 12+、Ubuntu 22.04+ | - |

---

## 2. 環境構築手順

### 2.1 リポジトリのクローン

```bash
# リポジトリのクローン
git clone https://github.com/Kensan196948G/IT-Change-CAB-Platform.git
cd IT-Change-CAB-Platform
```

### 2.2 Docker開発環境の起動

```bash
# 開発用Docker Compose起動
docker compose -f docker-compose.dev.yml up -d

# 起動確認
docker compose -f docker-compose.dev.yml ps

# 期待される出力:
# NAME         SERVICE     STATUS    PORTS
# cab-db       db          running   0.0.0.0:5432->5432/tcp
# cab-redis    redis       running   0.0.0.0:6379->6379/tcp
# cab-mailhog  mailhog     running   0.0.0.0:1025->1025/tcp, 0.0.0.0:8025->8025/tcp
```

### 2.3 バックエンドのセットアップ

```bash
# バックエンドディレクトリに移動
cd backend

# パッケージインストール
npm install

# 環境変数ファイルの作成
cp .env.example .env.development

# 環境変数の編集（必要に応じて）
# .env.development の内容:
# DATABASE_URL=postgresql://admin:password@localhost:5432/cab_platform_dev
# REDIS_URL=redis://localhost:6379/0
# JWT_SECRET=dev-jwt-secret-key-do-not-use-in-production
# NODE_ENV=development
# PORT=8000
# LOG_LEVEL=debug
# SMTP_HOST=localhost
# SMTP_PORT=1025
# CORS_ORIGIN=http://localhost:3000

# データベースマイグレーション実行
npm run migrate:up

# シードデータ投入（テスト用データ）
npm run seed

# バックエンド起動（開発モード：ホットリロード有効）
npm run dev
```

### 2.4 フロントエンドのセットアップ

```bash
# フロントエンドディレクトリに移動（別ターミナル）
cd frontend

# パッケージインストール
npm install

# 環境変数ファイルの作成
cp .env.example .env.development

# 環境変数の編集
# .env.development の内容:
# VITE_API_URL=http://localhost:8000/api/v1
# VITE_APP_TITLE=CAB Platform (Dev)

# フロントエンド起動（開発モード：ホットリロード有効）
npm run dev
```

### 2.5 動作確認

| 確認項目 | URL | 期待結果 |
|---------|-----|---------|
| フロントエンド | http://localhost:3000 | ログイン画面が表示される |
| バックエンドAPI | http://localhost:8000/api/v1/health | `{"status":"healthy"}` が返却される |
| メール確認（MailHog） | http://localhost:8025 | MailHog UIが表示される |
| PostgreSQL | localhost:5432 | DB接続可能 |
| Redis | localhost:6379 | PING → PONG |

### 2.6 テスト用アカウント（シードデータ）

| ユーザー | メール | パスワード | ロール |
|---------|--------|-----------|--------|
| 管理者 | admin@mirai-kensetsu.co.jp | admin123 | admin |
| CAB議長 | cab-chair@mirai-kensetsu.co.jp | cab123 | cab_chair |
| CABメンバー1 | cab-member1@mirai-kensetsu.co.jp | cab123 | cab_member |
| CABメンバー2 | cab-member2@mirai-kensetsu.co.jp | cab123 | cab_member |
| 一般ユーザー | user1@mirai-kensetsu.co.jp | user123 | user |

---

## 3. 開発用Docker Compose

```yaml
# docker-compose.dev.yml
version: '3.9'

services:
  db:
    image: postgres:16-alpine
    container_name: cab-db
    environment:
      POSTGRES_DB: cab_platform_dev
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - pgdata_dev:/var/lib/postgresql/data
      - ./backend/src/database/init.sql:/docker-entrypoint-initdb.d/init.sql

  redis:
    image: redis:7-alpine
    container_name: cab-redis
    ports:
      - "6379:6379"
    volumes:
      - redisdata_dev:/data

  mailhog:
    image: mailhog/mailhog:latest
    container_name: cab-mailhog
    ports:
      - "1025:1025"   # SMTP
      - "8025:8025"   # Web UI

  bullmq-dashboard:
    image: taskforcesh/bullmq-dashboard:latest
    container_name: cab-bullmq-ui
    environment:
      REDIS_HOST: redis
      REDIS_PORT: 6379
    ports:
      - "4735:4735"
    depends_on:
      - redis

volumes:
  pgdata_dev:
  redisdata_dev:
```

---

## 4. VS Code推奨設定

### 4.1 推奨拡張機能

| 拡張機能 | 用途 |
|---------|------|
| ESLint | コード品質チェック |
| Prettier | コードフォーマット |
| TypeScript Importer | import文の自動補完 |
| Docker | Docker管理 |
| PostgreSQL | DB管理・クエリ実行 |
| REST Client | API動作確認 |
| GitLens | Git履歴・blame確認 |
| Error Lens | エラー・警告のインライン表示 |

### 4.2 ワークスペース設定

```json
// .vscode/settings.json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": "explicit"
  },
  "typescript.preferences.importModuleSpecifier": "relative",
  "typescript.tsdk": "node_modules/typescript/lib",
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

---

## 5. 開発用コマンド一覧

### 5.1 バックエンドコマンド

| コマンド | 説明 |
|---------|------|
| `npm run dev` | 開発サーバー起動（ホットリロード） |
| `npm run build` | TypeScriptビルド |
| `npm test` | テスト実行 |
| `npm run test:watch` | テストウォッチモード |
| `npm run test:coverage` | カバレッジ付きテスト |
| `npm run lint` | ESLintチェック |
| `npm run lint:fix` | ESLint自動修正 |
| `npm run type-check` | TypeScript型チェック |
| `npm run migrate:up` | マイグレーション実行 |
| `npm run migrate:down` | マイグレーションロールバック |
| `npm run migrate:create <名前>` | マイグレーションファイル作成 |
| `npm run seed` | テストデータ投入 |
| `npm run seed:reset` | DB初期化 + シード再投入 |

### 5.2 フロントエンドコマンド

| コマンド | 説明 |
|---------|------|
| `npm run dev` | 開発サーバー起動（Vite HMR） |
| `npm run build` | プロダクションビルド |
| `npm run preview` | ビルド結果のプレビュー |
| `npm test` | テスト実行 |
| `npm run test:watch` | テストウォッチモード |
| `npm run test:coverage` | カバレッジ付きテスト |
| `npm run lint` | ESLintチェック |
| `npm run type-check` | TypeScript型チェック |
| `npm run storybook` | Storybookの起動 |

### 5.3 Docker管理コマンド

| コマンド | 説明 |
|---------|------|
| `docker compose -f docker-compose.dev.yml up -d` | 開発環境起動 |
| `docker compose -f docker-compose.dev.yml down` | 開発環境停止 |
| `docker compose -f docker-compose.dev.yml logs -f db` | DBログ確認 |
| `docker compose -f docker-compose.dev.yml exec db psql -U admin -d cab_platform_dev` | DB直接接続 |
| `docker compose -f docker-compose.dev.yml exec redis redis-cli` | Redis直接接続 |

---

## 6. トラブルシューティング

| 問題 | 原因 | 対処法 |
|------|------|--------|
| `npm install` 失敗 | Node.jsバージョン不一致 | `node -v` でバージョン確認、nvm で切替 |
| DB接続エラー | Docker未起動 / ポート競合 | `docker compose ps` で確認、ポート変更 |
| マイグレーション失敗 | DB未作成 | Docker Compose再起動、initスクリプト確認 |
| フロントエンドビルドエラー | 型エラー | `npm run type-check` でエラー箇所特定 |
| ホットリロードが効かない | ファイル監視上限 | `sysctl fs.inotify.max_user_watches=524288` |
| ポート3000が使用中 | 別プロセスが使用 | `lsof -i :3000` で確認して停止 |

---

*文書管理：本文書はバージョン管理対象。変更時はバージョン番号を更新すること。*
