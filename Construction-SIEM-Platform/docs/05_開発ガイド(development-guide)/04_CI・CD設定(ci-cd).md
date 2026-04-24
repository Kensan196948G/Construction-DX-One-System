# 🔄 CI/CD 設定（CI/CD Configuration）

> GitHub Actions による継続的インテグレーション/デリバリー

---

## 📋 概要

| 項目 | 値 |
|------|------|
| プラットフォーム | GitHub Actions |
| ワークフローファイル | `.github/workflows/claudeos-ci.yml` |
| トリガー | push, pull_request（main ブランチ対象） |
| ランナー | `ubuntu-latest` |
| Python バージョン | 3.12 |

---

## 🏗 パイプライン構成

```
┌──────────────────────────────────────────────────────────────────┐
│                     GitHub Actions CI Pipeline                    │
├──────────────┬───────────────┬────────────┬──────────────────────┤
│              │               │            │                      │
│  ┌────────┐  │  ┌──────────┐ │ ┌────────┐ │  ┌──────────────┐   │
│  │ Lint & │  │  │ Security │ │ │ Test   │ │  │ Docker Build │   │
│  │ Format │  │  │ Scan     │ │ │ Suite  │ │  │              │   │
│  └───┬────┘  │  └────┬─────┘ │ └───┬────┘ │  └──────┬───────┘   │
│      │       │       │       │     │      │         │           │
│      └───────┴───────┴───────┴─────┴──────┴─────────┘           │
│                              │                                    │
│                     ┌────────▼─────────┐                         │
│                     │   STABLE Gate    │                         │
│                     │ (全ジョブ成功時)  │                         │
│                     └──────────────────┘                         │
└──────────────────────────────────────────────────────────────────┘
```

---

## 📄 ワークフロー定義

### ジョブ一覧

| # | ジョブ名 | 依存 | 目的 | 失敗条件 |
|:-:|---------|------|------|---------|
| 1 | `lint-format` | なし | コードフォーマット検証 | black/isort/flake8 差分 |
| 2 | `security-scan` | なし | セキュリティ脆弱性検出 | bandit 検出 > 0 |
| 3 | `test-suite` | なし | テスト実行・カバレッジ | テスト失敗 or カバレッジ < 85% |
| 4 | `docker-build` | なし | Dockerイメージビルド | ビルドエラー |
| 5 | `stable-gate` | 1,2,3,4 全て | STABLE 判定 | いずれかのジョブ失敗 |

### 依存関係図

```
lint-format ──────────┐
                      │
security-scan ────────┤
                      ├──▶ stable-gate
test-suite ───────────┤
                      │
docker-build ─────────┘
```

> ジョブ 1〜4 は**並列実行**され、全て成功した場合のみ `stable-gate` が実行されます。

---

## 🔍 ジョブ詳細

### 1️⃣ Lint & Format

| ステップ | コマンド | 説明 |
|---------|---------|------|
| Black チェック | `black . --check --line-length 120` | フォーマット差分検出 |
| isort チェック | `isort . --check-only` | インポート順序検証 |
| flake8 | `flake8 api/ tests/` | リンティング |

```yaml
lint-format:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: '3.12'
    - run: pip install black isort flake8
    - name: Black check
      run: black . --check --line-length 120
    - name: isort check
      run: isort . --check-only
    - name: flake8
      run: flake8 api/ tests/ --max-line-length 120 --max-complexity 10
```

### 2️⃣ Security Scan

| ステップ | コマンド | 説明 |
|---------|---------|------|
| bandit | `bandit -r api/ -f json -o bandit-report.json` | セキュリティスキャン |
| 結果検証 | 結果の High/Medium/Low が全て 0 であること | ゼロトレランス |

```yaml
security-scan:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: '3.12'
    - run: pip install bandit
    - name: Bandit security scan
      run: bandit -r api/ -f json -o bandit-report.json
    - name: Upload report
      uses: actions/upload-artifact@v4
      if: always()
      with:
        name: bandit-report
        path: bandit-report.json
```

### 3️⃣ Test Suite

| ステップ | コマンド | 説明 |
|---------|---------|------|
| 依存インストール | `pip install -r requirements.txt` | テスト依存含む |
| pytest 実行 | `pytest tests/ -v --cov=api --cov-report=xml` | カバレッジ付き |
| カバレッジ検証 | カバレッジ 85% 以上 | 最低ライン |

```yaml
test-suite:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: '3.12'
    - run: pip install -r requirements.txt
    - name: Run tests with coverage
      run: pytest tests/ -v --cov=api --cov-report=xml --cov-report=term-missing --cov-fail-under=85
    - name: Upload coverage
      uses: actions/upload-artifact@v4
      with:
        name: coverage-report
        path: coverage.xml
```

### 4️⃣ Docker Build

| ステップ | コマンド | 説明 |
|---------|---------|------|
| Docker ビルド | `docker build -t siem-platform:test .` | イメージビルド |
| ヘルスチェック | コンテナ起動 → /health 確認 | 起動確認 |

```yaml
docker-build:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Build Docker image
      run: docker build -t siem-platform:test .
    - name: Health check
      run: |
        docker run -d --name siem-test -p 8000:8000 siem-platform:test
        sleep 5
        curl -f http://localhost:8000/health
        docker stop siem-test
```

### 5️⃣ STABLE Gate

| 条件 | 説明 |
|------|------|
| 全ジョブ成功 | lint-format, security-scan, test-suite, docker-build |
| ラベル付与 | `STABLE` ラベルをPRに付与 |

```yaml
stable-gate:
  runs-on: ubuntu-latest
  needs: [lint-format, security-scan, test-suite, docker-build]
  steps:
    - name: STABLE判定
      run: echo "All checks passed. Build is STABLE."
    - name: Add STABLE label
      if: github.event_name == 'pull_request'
      uses: actions/github-script@v7
      with:
        script: |
          github.rest.issues.addLabels({
            owner: context.repo.owner,
            repo: context.repo.repo,
            issue_number: context.issue.number,
            labels: ['STABLE']
          })
```

---

## 🔧 Auto Repair（自動修復）

### CI 失敗時の自動修復フロー

```
CI失敗
  │
  ▼
┌─────────────────┐
│ 失敗ジョブ特定   │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
 Lint失敗   Test失敗
    │         │
    ▼         ▼
 auto-fix   調査・修正
 black/isort  │
    │         ▼
    ▼      コミット
 コミット     │
    │         ▼
    ▼      再プッシュ
 再プッシュ
    │
    ▼
 CI再実行
```

### 自動修復対象

| 失敗種別 | 自動修復 | 方法 |
|---------|:-------:|------|
| 🟢 black フォーマット | ✅ | `black . --line-length 120` で自動修正 |
| 🟢 isort インポート順 | ✅ | `isort .` で自動修正 |
| 🟡 flake8 警告 | ⚠ | 一部自動修正可能（`autopep8`） |
| 🔴 bandit 検出 | ❌ | 手動修正が必要 |
| 🔴 テスト失敗 | ❌ | 手動修正が必要 |
| 🔴 Docker ビルド失敗 | ❌ | 手動修正が必要 |

---

## 📊 CI メトリクス

### 品質ゲート基準

| メトリクス | 基準値 | 現在の値 |
|-----------|--------|---------|
| テスト数 | 200以上 | 210 |
| カバレッジ | 85%以上 | 83%（改善中） |
| bandit 検出 | 0件 | 0件 |
| ビルド時間 | 10分以内 | 約5分 |

### ワークフロー実行時間の目安

| ジョブ | 平均時間 |
|--------|---------|
| Lint & Format | ~30秒 |
| Security Scan | ~45秒 |
| Test Suite | ~2分 |
| Docker Build | ~2分 |
| STABLE Gate | ~10秒 |
| **合計** | **約5分** |

---

## 🔔 通知設定

### CI 結果通知

| イベント | 通知先 | 条件 |
|---------|--------|------|
| ✅ STABLE 達成 | Slack | STABLE Gate 成功 |
| ❌ CI 失敗 | Slack + Teams | いずれかのジョブ失敗 |
| 🔴 セキュリティ検出 | Slack + Teams + Email | bandit 検出 > 0 |
