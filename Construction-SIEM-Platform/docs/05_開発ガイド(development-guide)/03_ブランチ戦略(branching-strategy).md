# 🔀 ブランチ戦略（Branching Strategy）

> Git ブランチ運用ルールとワークフロー

---

## 📋 ブランチ構成

| ブランチ | 用途 | 保護 | マージ条件 |
|----------|------|:----:|-----------|
| `main` | 本番相当（STABLE のみ） | ✅ | CI全パス + STABLE判定 |
| `feature/*` | 機能開発 | ❌ | - |

---

## 🌳 ブランチフロー

```
main ─────────────────────────────────────────────▶
  │                                    ▲
  │ branch                             │ squash merge
  ▼                                    │
  feature/42-incident-sla ────────────┘
     │    │    │    │
    c1   c2   c3   c4
```

### フロー説明

| ステップ | アクション | 説明 |
|:--------:|-----------|------|
| 1️⃣ | ブランチ作成 | `main` から `feature/*` を作成 |
| 2️⃣ | 開発・コミット | Conventional Commits でコミット |
| 3️⃣ | CI 実行 | プッシュ時に自動で CI パイプライン実行 |
| 4️⃣ | PR 作成 | `feature/*` → `main` の PR を作成 |
| 5️⃣ | レビュー | 最低1名のレビュアーが承認 |
| 6️⃣ | STABLE 判定 | CI 全ジョブ成功 + N回連続パス |
| 7️⃣ | マージ | **Squash Merge** で `main` にマージ |

---

## 🏷 ブランチ命名規則

### フォーマット

```
feature/<issue-number>-<short-description>
```

### 命名例

| ブランチ名 | 説明 |
|-----------|------|
| `feature/42-incident-sla-timer` | Issue #42: SLAタイマー機能 |
| `feature/55-threat-intel-api` | Issue #55: 脅威インテリジェンスAPI |
| `feature/63-fix-auth-token` | Issue #63: 認証トークン修正 |
| `feature/71-add-correlation-tests` | Issue #71: 相関分析テスト追加 |

---

## 🛡 main ブランチ保護ルール

| ルール | 設定 |
|--------|------|
| ❌ 直接 push 禁止 | `main` への直接 push は不可 |
| ✅ PR 必須 | 全ての変更は PR 経由 |
| ✅ CI 必須 | 全ジョブが成功していること |
| ✅ レビュー必須 | 最低1名の承認 |
| ✅ Squash Merge | コミット履歴をクリーンに保つ |
| ✅ ブランチ削除 | マージ後に自動削除 |

---

## ⚙ CI パイプライン（GitHub Actions）

### ワークフロー: `.github/workflows/claudeos-ci.yml`

```
┌─────────────┐   ┌──────────────────┐   ┌────────────┐   ┌──────────────┐   ┌──────────────┐
│ Lint &       │──▶│ Security Scan    │──▶│ Test Suite │──▶│ Docker Build │──▶│ STABLE Gate  │
│ Format       │   │ (bandit)         │   │ (pytest)   │   │              │   │              │
└─────────────┘   └──────────────────┘   └────────────┘   └──────────────┘   └──────────────┘
```

| ジョブ | 内容 | 失敗条件 |
|--------|------|---------|
| 🔍 Lint & Format | black --check, isort --check, flake8 | フォーマット差分あり |
| 🛡 Security Scan | bandit -r api/ | High/Medium/Low > 0 |
| 🧪 Test Suite | pytest --cov | テスト失敗 or カバレッジ < 85% |
| 🐳 Docker Build | docker build | ビルド失敗 |
| ✅ STABLE Gate | 全ジョブ成功判定 | いずれかのジョブ失敗 |

---

## 🎯 STABLE 判定

### STABLE 条件

| 条件 | 説明 |
|------|------|
| ✅ テスト全パス | pytest の全テストが PASSED |
| ✅ CI 全パス | 全ジョブが成功 |
| ✅ Lint クリーン | フォーマット差分なし |
| ✅ Build 成功 | Docker ビルド成功 |
| ✅ セキュリティ | bandit 検出 0件 |
| ✅ エラー 0 | ランタイムエラーなし |

### 連続パス回数（N回）

| 変更の種類 | 必要回数（N） | 説明 |
|-----------|:------------:|------|
| 🟢 小規模（ドキュメント、スタイル） | 2 | ドキュメント修正、フォーマット |
| 🟡 通常（機能追加、バグ修正） | 3 | 新機能、既存機能修正 |
| 🔴 重要（セキュリティ、アーキテクチャ） | 5 | セキュリティ修正、大規模変更 |

---

## 🔄 ワークフロー例

### 通常の機能開発

```bash
# 1. main を最新に
git checkout main
git pull origin main

# 2. feature ブランチ作成
git checkout -b feature/42-incident-sla-timer

# 3. 開発・コミット
git add api/routes/incidents.py
git commit -m "feat(incidents): SLAタイマー自動開始機能を追加"

# 4. テスト実行
pytest tests/ -v

# 5. プッシュ
git push -u origin feature/42-incident-sla-timer

# 6. GitHub で PR を作成

# 7. CI が通り、レビュー承認後、Squash Merge
```

### CI 失敗時の対応

```bash
# 1. CI のログを確認
gh run view <run-id> --log

# 2. 修正を実施
black . --line-length 120
isort .

# 3. 修正をコミット・プッシュ
git add -A
git commit -m "style: black/isort フォーマット適用"
git push

# 4. CI の再実行を待つ
```

---

## 📊 ブランチ戦略の利点

| 利点 | 説明 |
|------|------|
| 🔒 安全性 | main は常に STABLE 状態 |
| 🧹 クリーンな履歴 | Squash Merge で1コミットに集約 |
| 🤖 自動化 | CI/CD による品質ゲート |
| 👥 コラボレーション | PR ベースのコードレビュー |
| 📋 追跡性 | Issue ↔ ブランチ ↔ PR の紐付け |
