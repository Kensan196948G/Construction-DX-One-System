# CI/CD設計書（CI/CD Design）

| 項目 | 内容 |
|------|------|
| 文書番号 | DEV-004 |
| バージョン | 1.0 |
| 作成日 | 2026-03-26 |
| 最終更新日 | 2026-03-26 |
| 作成者 | 開発チーム |
| 対象プロジェクト | 建設業 統合リスク＆コンプライアンス管理システム（Construction-GRC-System） |

---

## 1. 概要

本文書は、Construction-GRC-SystemのCI/CD（継続的インテグレーション/継続的デリバリー）パイプラインの設計を定める。GitHub Actionsを使用し、コードの品質維持、自動テスト、自動デプロイを実現する。

---

## 2. CI/CD 全体アーキテクチャ

### 2.1 パイプライン概要図

```
Developer Push/PR
        │
        ▼
┌─────────────────────────────────────────┐
│           GitHub Actions                 │
│                                          │
│  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │  Lint &   │  │  Unit    │  │ Build  │ │
│  │  Format   │→ │  Test    │→ │ Check  │ │
│  └──────────┘  └──────────┘  └────────┘ │
│        │              │            │      │
│        ▼              ▼            ▼      │
│  ┌──────────────────────────────────────┐│
│  │         Quality Gate                  ││
│  │  (全ジョブ成功で通過)                  ││
│  └──────────────────────────────────────┘│
│                    │                      │
│         ┌─────────┴─────────┐            │
│         ▼                   ▼            │
│  ┌─────────────┐  ┌──────────────┐       │
│  │ Integration  │  │ Security     │       │
│  │ Test         │  │ Scan         │       │
│  └─────────────┘  └──────────────┘       │
│         │                   │            │
│         ▼                   ▼            │
│  ┌──────────────────────────────────────┐│
│  │         Deploy Gate                   ││
│  └──────────────────────────────────────┘│
│                    │                      │
│         ┌─────────┼─────────┐            │
│         ▼         ▼         ▼            │
│  ┌──────────┐ ┌────────┐ ┌──────────┐   │
│  │ Staging  │ │  E2E   │ │Production│   │
│  │ Deploy   │→│  Test  │→│ Deploy   │   │
│  └──────────┘ └────────┘ └──────────┘   │
└─────────────────────────────────────────┘
```

### 2.2 トリガー一覧

| イベント | トリガー | 実行パイプライン |
|---------|---------|----------------|
| Pull Request 作成/更新 | `pull_request` → develop, main | CI（Lint + Test + Build） |
| develop へのマージ | `push` → develop | CI + Staging Deploy |
| release/* ブランチ作成 | `push` → release/* | CI + Staging Deploy + E2E |
| main へのマージ | `push` → main | CI + Production Deploy |
| タグ作成 | `push` → tags v* | Release Build + Deploy |
| 定期実行 | `schedule` (毎日深夜) | Security Scan + Dependency Check |
| 手動実行 | `workflow_dispatch` | 任意のワークフロー |

---

## 3. ワークフロー設計

### 3.1 CI ワークフロー（ci.yml）

```yaml
name: CI

on:
  pull_request:
    branches: [develop, main]
  push:
    branches: [develop, main]

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

env:
  PYTHON_VERSION: "3.12"
  NODE_VERSION: "20"
  POSTGRES_DB: test_grc_db
  POSTGRES_USER: test_user
  POSTGRES_PASSWORD: test_password

jobs:
  # ========================================
  # バックエンド Lint & Format チェック
  # ========================================
  backend-lint:
    name: Backend Lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: "pip"

      - name: Install dependencies
        run: pip install -r requirements/dev-tools.txt

      - name: Run Ruff linter
        run: ruff check . --output-format=github

      - name: Run Ruff formatter check
        run: ruff format --check .

      - name: Run mypy
        run: mypy apps/ --ignore-missing-imports

  # ========================================
  # フロントエンド Lint & Format チェック
  # ========================================
  frontend-lint:
    name: Frontend Lint
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: npm ci

      - name: Run ESLint
        run: npm run lint

      - name: Run Prettier check
        run: npm run format:check

      - name: Run TypeScript check
        run: npm run type-check

  # ========================================
  # バックエンド ユニットテスト
  # ========================================
  backend-test:
    name: Backend Test
    runs-on: ubuntu-latest
    needs: [backend-lint]
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: ${{ env.POSTGRES_DB }}
          POSTGRES_USER: ${{ env.POSTGRES_USER }}
          POSTGRES_PASSWORD: ${{ env.POSTGRES_PASSWORD }}
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: "pip"

      - name: Install dependencies
        run: pip install -r requirements/test.txt

      - name: Run migrations
        run: python manage.py migrate
        env:
          DATABASE_URL: postgres://${{ env.POSTGRES_USER }}:${{ env.POSTGRES_PASSWORD }}@localhost:5432/${{ env.POSTGRES_DB }}

      - name: Run tests with coverage
        run: |
          pytest \
            --cov=apps \
            --cov-report=xml:coverage.xml \
            --cov-report=html:htmlcov \
            --junitxml=test-results.xml \
            -v
        env:
          DATABASE_URL: postgres://${{ env.POSTGRES_USER }}:${{ env.POSTGRES_PASSWORD }}@localhost:5432/${{ env.POSTGRES_DB }}
          REDIS_URL: redis://localhost:6379/0

      - name: Upload coverage report
        uses: actions/upload-artifact@v4
        with:
          name: backend-coverage
          path: htmlcov/

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: backend-test-results
          path: test-results.xml

      - name: Check coverage threshold
        run: |
          coverage report --fail-under=80

  # ========================================
  # フロントエンド ユニットテスト
  # ========================================
  frontend-test:
    name: Frontend Test
    runs-on: ubuntu-latest
    needs: [frontend-lint]
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: npm ci

      - name: Run unit tests
        run: npm run test:unit -- --coverage --reporter=junit --outputFile=test-results.xml

      - name: Upload coverage report
        uses: actions/upload-artifact@v4
        with:
          name: frontend-coverage
          path: frontend/coverage/

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: frontend-test-results
          path: frontend/test-results.xml

  # ========================================
  # ビルドチェック
  # ========================================
  build-check:
    name: Build Check
    runs-on: ubuntu-latest
    needs: [backend-test, frontend-test]
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build backend image
        uses: docker/build-push-action@v5
        with:
          context: .
          file: docker/backend/Dockerfile
          push: false
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Build frontend image
        uses: docker/build-push-action@v5
        with:
          context: ./frontend
          file: docker/frontend/Dockerfile
          push: false
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # ========================================
  # 品質ゲート
  # ========================================
  quality-gate:
    name: Quality Gate
    runs-on: ubuntu-latest
    needs: [backend-lint, frontend-lint, backend-test, frontend-test, build-check]
    steps:
      - name: Quality Gate Passed
        run: echo "All quality checks passed!"
```

### 3.2 セキュリティスキャン ワークフロー（security.yml）

```yaml
name: Security Scan

on:
  schedule:
    - cron: "0 0 * * *"  # 毎日UTC 0:00
  pull_request:
    branches: [main]
  workflow_dispatch:

jobs:
  # ========================================
  # 依存パッケージの脆弱性チェック
  # ========================================
  dependency-check:
    name: Dependency Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Trivy (Python)
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: "fs"
          scan-ref: "."
          format: "sarif"
          output: "trivy-python.sarif"

      - name: Upload Trivy results
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: "trivy-python.sarif"

  # ========================================
  # コードセキュリティ分析
  # ========================================
  code-security:
    name: Code Security Analysis
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Initialize CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: python, javascript

      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v3

  # ========================================
  # Dockerイメージ脆弱性スキャン
  # ========================================
  container-scan:
    name: Container Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build backend image
        run: docker build -t grc-backend:scan -f docker/backend/Dockerfile .

      - name: Run Trivy container scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: "grc-backend:scan"
          format: "sarif"
          output: "trivy-container.sarif"
          severity: "CRITICAL,HIGH"

      - name: Upload scan results
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: "trivy-container.sarif"

  # ========================================
  # シークレットスキャン
  # ========================================
  secret-scan:
    name: Secret Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Run Gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### 3.3 デプロイ ワークフロー（deploy.yml）

```yaml
name: Deploy

on:
  push:
    branches: [develop, main]
    tags: ["v*"]
  workflow_dispatch:
    inputs:
      environment:
        description: "Deploy target environment"
        required: true
        type: choice
        options:
          - staging
          - production

jobs:
  # ========================================
  # ステージング デプロイ
  # ========================================
  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop' || github.event.inputs.environment == 'staging'
    environment:
      name: staging
      url: https://staging.grc-system.example.com
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ vars.CONTAINER_REGISTRY }}
          username: ${{ secrets.REGISTRY_USERNAME }}
          password: ${{ secrets.REGISTRY_PASSWORD }}

      - name: Build and push backend
        uses: docker/build-push-action@v5
        with:
          context: .
          file: docker/backend/Dockerfile
          push: true
          tags: |
            ${{ vars.CONTAINER_REGISTRY }}/grc-backend:staging
            ${{ vars.CONTAINER_REGISTRY }}/grc-backend:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Build and push frontend
        uses: docker/build-push-action@v5
        with:
          context: ./frontend
          file: docker/frontend/Dockerfile
          push: true
          tags: |
            ${{ vars.CONTAINER_REGISTRY }}/grc-frontend:staging
            ${{ vars.CONTAINER_REGISTRY }}/grc-frontend:${{ github.sha }}

      - name: Deploy to staging server
        run: |
          echo "Deploying to staging environment..."
          # デプロイスクリプトの実行
          # ssh, kubectl apply, docker compose up 等

      - name: Run database migrations
        run: |
          echo "Running migrations on staging..."

      - name: Health check
        run: |
          echo "Running health check..."
          curl -sf https://staging.grc-system.example.com/api/health/ || exit 1

      - name: Notify deployment
        if: always()
        run: |
          echo "Staging deployment completed: ${{ job.status }}"

  # ========================================
  # E2Eテスト（ステージングデプロイ後）
  # ========================================
  e2e-test:
    name: E2E Test on Staging
    runs-on: ubuntu-latest
    needs: [deploy-staging]
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"

      - name: Install Playwright
        run: |
          cd frontend
          npm ci
          npx playwright install --with-deps

      - name: Run E2E tests
        run: |
          cd frontend
          npx playwright test --config=playwright.staging.config.ts
        env:
          BASE_URL: https://staging.grc-system.example.com

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: e2e-test-results
          path: frontend/playwright-report/

  # ========================================
  # 本番 デプロイ
  # ========================================
  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' || startsWith(github.ref, 'refs/tags/v')
    needs: [e2e-test]
    environment:
      name: production
      url: https://grc-system.example.com
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ vars.CONTAINER_REGISTRY }}
          username: ${{ secrets.REGISTRY_USERNAME }}
          password: ${{ secrets.REGISTRY_PASSWORD }}

      - name: Determine version tag
        id: version
        run: |
          if [[ "${{ github.ref }}" == refs/tags/* ]]; then
            echo "tag=${GITHUB_REF#refs/tags/}" >> $GITHUB_OUTPUT
          else
            echo "tag=latest" >> $GITHUB_OUTPUT
          fi

      - name: Build and push backend
        uses: docker/build-push-action@v5
        with:
          context: .
          file: docker/backend/Dockerfile
          push: true
          tags: |
            ${{ vars.CONTAINER_REGISTRY }}/grc-backend:${{ steps.version.outputs.tag }}
            ${{ vars.CONTAINER_REGISTRY }}/grc-backend:${{ github.sha }}

      - name: Build and push frontend
        uses: docker/build-push-action@v5
        with:
          context: ./frontend
          file: docker/frontend/Dockerfile
          push: true
          tags: |
            ${{ vars.CONTAINER_REGISTRY }}/grc-frontend:${{ steps.version.outputs.tag }}
            ${{ vars.CONTAINER_REGISTRY }}/grc-frontend:${{ github.sha }}

      - name: Create database backup
        run: |
          echo "Creating pre-deployment database backup..."

      - name: Deploy to production
        run: |
          echo "Deploying to production environment..."

      - name: Run database migrations
        run: |
          echo "Running migrations on production..."

      - name: Health check
        run: |
          curl -sf https://grc-system.example.com/api/health/ || exit 1

      - name: Smoke test
        run: |
          echo "Running smoke tests..."

      - name: Notify deployment
        if: always()
        run: |
          echo "Production deployment completed: ${{ job.status }}"
```

---

## 4. 品質ゲート定義

### 4.1 PR マージ品質ゲート

PRがマージ可能となるための必須条件。

| ゲート項目 | 基準 | ブロック |
|-----------|------|---------|
| Ruff Lint | エラー 0 件 | Yes |
| Ruff Format | フォーマット差分 0 件 | Yes |
| ESLint | エラー 0 件 | Yes |
| Prettier | フォーマット差分 0 件 | Yes |
| TypeScript 型チェック | エラー 0 件 | Yes |
| mypy 型チェック | エラー 0 件 | Yes |
| バックエンドテスト | 全件パス | Yes |
| フロントエンドテスト | 全件パス | Yes |
| テストカバレッジ（Backend） | 80% 以上 | Yes |
| テストカバレッジ（Frontend） | 70% 以上 | Yes |
| Docker ビルド | 成功 | Yes |
| セキュリティスキャン | CRITICAL 0 件 | Yes（main向けPR） |
| レビュー承認 | develop: 1名以上, main: 2名以上 | Yes |

### 4.2 デプロイ品質ゲート

本番デプロイの前提条件。

| ゲート項目 | 基準 |
|-----------|------|
| CI品質ゲート | 全て通過 |
| E2Eテスト | 全件パス |
| ステージング検証 | 動作確認完了 |
| セキュリティスキャン | CRITICAL/HIGH 0件 |
| パフォーマンステスト | 基準値クリア |
| リリース承認 | プロジェクトマネージャーの承認 |
| データベースバックアップ | 完了 |

---

## 5. 環境構成

### 5.1 環境一覧

| 環境 | 用途 | URL | デプロイトリガー |
|------|------|-----|----------------|
| Development | ローカル開発 | localhost | - |
| CI | テスト実行 | - | PR作成/更新 |
| Staging | 結合テスト・受入テスト | staging.grc-system.example.com | develop マージ |
| Production | 本番運用 | grc-system.example.com | main マージ + タグ |

### 5.2 シークレット管理

| シークレット名 | 用途 | 管理場所 |
|---------------|------|---------|
| `REGISTRY_USERNAME` | コンテナレジストリ認証 | GitHub Secrets |
| `REGISTRY_PASSWORD` | コンテナレジストリ認証 | GitHub Secrets |
| `DATABASE_URL` | データベース接続 | GitHub Environment Secrets |
| `DJANGO_SECRET_KEY` | Django秘密鍵 | GitHub Environment Secrets |
| `DEPLOY_SSH_KEY` | デプロイ先SSH鍵 | GitHub Secrets |
| `SLACK_WEBHOOK_URL` | 通知用Webhook | GitHub Secrets |

---

## 6. 通知設計

### 6.1 通知チャネル

| イベント | 通知先 | 条件 |
|---------|--------|------|
| CI 失敗 | PR コメント + Slack | 自動 |
| CI 成功 | PR コメント | 自動 |
| デプロイ成功 | Slack #deploy チャンネル | 自動 |
| デプロイ失敗 | Slack #deploy チャンネル + 担当者メンション | 自動 |
| セキュリティアラート | Slack #security チャンネル + メール | 自動 |
| 定期スキャン結果 | Slack #security チャンネル | 脆弱性検出時 |

### 6.2 通知メッセージフォーマット

```
🔵 [CI] PR #123 - Backend Test Passed
🔴 [CI] PR #123 - Frontend Lint Failed
🟢 [Deploy] Staging deployment successful (v1.2.0)
🔴 [Deploy] Production deployment failed - Rollback initiated
⚠️ [Security] 3 vulnerabilities found in dependency scan
```

---

## 7. パフォーマンス最適化

### 7.1 CI実行時間の目標

| ジョブ | 目標時間 | 現状 |
|--------|---------|------|
| Backend Lint | 2分以内 | - |
| Frontend Lint | 2分以内 | - |
| Backend Test | 5分以内 | - |
| Frontend Test | 3分以内 | - |
| Build Check | 5分以内 | - |
| 合計（並列実行時） | 10分以内 | - |

### 7.2 最適化施策

| 施策 | 効果 |
|------|------|
| 依存パッケージのキャッシュ | インストール時間の短縮 |
| Docker レイヤーキャッシュ（GHA cache） | ビルド時間の短縮 |
| テストの並列実行（pytest-xdist） | テスト時間の短縮 |
| 変更ファイルに基づくジョブスキップ | 不要なジョブの回避 |
| concurrency 設定 | 同一ブランチの重複実行防止 |

---

## 8. 障害対応

### 8.1 デプロイ失敗時のロールバック手順

```
1. デプロイ失敗を検知（自動通知）
2. 影響範囲を確認
3. ロールバックを実行
   - 前バージョンのイメージをデプロイ
   - データベースマイグレーションのロールバック（必要時）
4. 正常動作を確認（ヘルスチェック）
5. 原因調査・修正
6. 再デプロイ
```

### 8.2 ロールバックコマンド

```bash
# 前バージョンのタグを確認
git tag --sort=-creatordate | head -5

# 前バージョンでデプロイ（手動トリガー）
gh workflow run deploy.yml -f environment=production -f version=v1.1.0
```

---

## 改訂履歴

| バージョン | 日付 | 変更内容 | 変更者 |
|-----------|------|---------|--------|
| 1.0 | 2026-03-26 | 初版作成 | 開発チーム |
