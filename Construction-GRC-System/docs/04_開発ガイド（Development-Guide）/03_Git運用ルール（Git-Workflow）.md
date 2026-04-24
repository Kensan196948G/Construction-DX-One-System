# Git運用ルール（Git Workflow）

| 項目 | 内容 |
|------|------|
| 文書番号 | DEV-003 |
| バージョン | 1.0 |
| 作成日 | 2026-03-26 |
| 最終更新日 | 2026-03-26 |
| 作成者 | 開発チーム |
| 対象プロジェクト | 建設業 統合リスク＆コンプライアンス管理システム（Construction-GRC-System） |

---

## 1. 概要

本文書は、Construction-GRC-SystemにおけるGit運用ルールを定める。コードの品質維持、変更の追跡可能性、チーム開発の効率化を目的とする。

---

## 2. ブランチ戦略

### 2.1 ブランチ構成（Git Flow 変形）

```
main
├── develop
│   ├── feature/RSK-001-risk-assessment-form
│   ├── feature/CMP-015-compliance-dashboard
│   └── feature/CTL-003-control-matrix
├── release/v1.0.0
├── hotfix/fix-critical-auth-bug
└── staging
```

### 2.2 ブランチの種類と用途

| ブランチ | パターン | 用途 | ベース | マージ先 |
|---------|---------|------|--------|---------|
| main | `main` | 本番環境コード | - | - |
| develop | `develop` | 開発統合 | main | release |
| feature | `feature/<issue-id>-<description>` | 機能開発 | develop | develop |
| bugfix | `bugfix/<issue-id>-<description>` | バグ修正 | develop | develop |
| release | `release/v<version>` | リリース準備 | develop | main, develop |
| hotfix | `hotfix/<description>` | 緊急修正 | main | main, develop |
| staging | `staging` | ステージング検証 | develop | - |

### 2.3 ブランチ命名規則

```
feature/RSK-001-add-risk-assessment-form
feature/CMP-015-implement-compliance-dashboard
bugfix/AUD-023-fix-audit-report-pagination
hotfix/fix-authentication-token-expiry
release/v1.2.0
```

**命名規則の詳細**:

- 全て小文字（Issue IDは例外）
- 単語区切りはハイフン（`-`）
- Issue ID（GitHub Issue番号やモジュールID）を含める
- 簡潔で内容が分かる説明を付ける
- 長さは50文字以内を推奨

### 2.4 ブランチの保護ルール

| ブランチ | 保護設定 |
|---------|---------|
| main | PRマージのみ、2名以上のレビュー必須、CI通過必須、force push禁止 |
| develop | PRマージのみ、1名以上のレビュー必須、CI通過必須 |
| staging | PRマージのみ、CI通過必須 |
| release/* | PRマージのみ、2名以上のレビュー必須、CI通過必須 |

---

## 3. コミットメッセージ規約

### 3.1 Conventional Commits

[Conventional Commits](https://www.conventionalcommits.org/) 仕様に準拠する。

#### フォーマット

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 3.2 Type（種別）

| Type | 用途 | 例 |
|------|------|-----|
| `feat` | 新機能 | `feat(risk): リスク評価フォームを追加` |
| `fix` | バグ修正 | `fix(auth): トークン更新の不具合を修正` |
| `docs` | ドキュメント変更 | `docs(api): API仕様書を更新` |
| `style` | コードスタイル変更（ロジック変更なし） | `style(risk): フォーマッターを適用` |
| `refactor` | リファクタリング | `refactor(compliance): サービス層を分離` |
| `perf` | パフォーマンス改善 | `perf(report): レポート生成のクエリを最適化` |
| `test` | テスト追加・修正 | `test(risk): リスク評価APIのテストを追加` |
| `build` | ビルド設定変更 | `build(docker): Dockerfile を最適化` |
| `ci` | CI設定変更 | `ci: GitHub Actions のワークフローを追加` |
| `chore` | その他の変更 | `chore(deps): Django を 5.1 にアップデート` |
| `revert` | コミットの取り消し | `revert: feat(risk): リスク評価フォームを追加` |

### 3.3 Scope（影響範囲）

| Scope | 対象 |
|-------|------|
| `risk` | リスク管理（RSK） |
| `compliance` | コンプライアンス管理（CMP） |
| `control` | 統制管理（CTL） |
| `audit` | 監査管理（AUD） |
| `report` | レポート管理（RPT） |
| `auth` | 認証・認可 |
| `api` | API共通 |
| `ui` | フロントエンド共通 |
| `db` | データベース |
| `docker` | Docker設定 |
| `deps` | 依存パッケージ |

### 3.4 コミットメッセージの例

#### 良い例

```
feat(risk): リスクマトリクス表示機能を追加

ダッシュボードにリスクマトリクスのヒートマップを表示する機能を実装。
発生確率と影響度の2軸でリスクの分布を可視化する。

Refs: #123
```

```
fix(compliance): 法令更新通知のメール送信が失敗する問題を修正

Celeryタスクのタイムアウト設定が短すぎたため、
大量の通知対象がある場合にタスクが中断されていた。
タイムアウトを300秒に延長し、バッチ処理に変更。

Fixes: #456
```

#### 悪い例

```
# 曖昧
修正

# 範囲が広すぎる
いろいろ修正した

# 英語と日本語の混在（統一されていない）
fix bug
```

### 3.5 コミットの粒度

- 1つのコミットには1つの論理的変更のみを含める
- 「動作する状態」でコミットする
- WIP（Work In Progress）コミットはPRマージ前にスカッシュする
- ファイルの追加・変更・削除は意味のある単位でまとめる

---

## 4. プルリクエスト（PR）規約

### 4.1 PR テンプレート

```markdown
## 概要
<!-- この PR で何をしたか、なぜ必要かを記載 -->

## 関連 Issue
<!-- 関連する Issue 番号 -->
Closes #

## 変更内容
<!-- 主な変更点をリスト形式で記載 -->
-
-

## 変更種別
- [ ] 新機能（feat）
- [ ] バグ修正（fix）
- [ ] リファクタリング（refactor）
- [ ] テスト追加・修正（test）
- [ ] ドキュメント（docs）
- [ ] その他

## テスト
<!-- 実施したテストの内容 -->
- [ ] ユニットテスト追加/更新
- [ ] 結合テスト追加/更新
- [ ] 手動テスト実施

## スクリーンショット
<!-- UI 変更がある場合、Before/After のスクリーンショットを貼付 -->

## チェックリスト
- [ ] コーディング規約に準拠している
- [ ] テストが全て通る
- [ ] ドキュメントを更新した（必要な場合）
- [ ] マイグレーションファイルを含めている（必要な場合）
- [ ] セキュリティに関する考慮をした
```

### 4.2 PR の命名規則

```
[Type] 簡潔な説明

例:
[feat] リスク評価フォームの実装
[fix] 認証トークンの有効期限切れ対応
[refactor] コンプライアンス管理のサービス層分離
```

### 4.3 PR のサイズガイドライン

| サイズ | 変更行数 | レビュー目安時間 | 推奨度 |
|--------|---------|----------------|--------|
| XS | ~50行 | ~15分 | 最も推奨 |
| S | ~200行 | ~30分 | 推奨 |
| M | ~500行 | ~1時間 | 許容 |
| L | ~1000行 | ~2時間 | 分割を検討 |
| XL | 1000行~ | 2時間以上 | 原則禁止（分割必須） |

### 4.4 PR マージ方針

| マージ方式 | 使用場面 |
|-----------|---------|
| Squash and Merge | feature → develop（コミット履歴を整理） |
| Merge Commit | release → main（マージ履歴を残す） |
| Merge Commit | hotfix → main / develop |

---

## 5. コードレビュー基準

### 5.1 レビューの観点

#### 必須チェック項目

| カテゴリ | チェック項目 |
|---------|------------|
| 機能性 | 要件を正しく実装しているか |
| 機能性 | エッジケースを考慮しているか |
| セキュリティ | SQLインジェクション、XSS等の脆弱性がないか |
| セキュリティ | 認証・認可が適切に実装されているか |
| セキュリティ | 機密情報がハードコードされていないか |
| テスト | テストが適切に記述されているか |
| テスト | テストカバレッジが基準を満たしているか（80%以上） |
| パフォーマンス | N+1クエリが発生していないか |
| パフォーマンス | 不要なデータの取得がないか |

#### 推奨チェック項目

| カテゴリ | チェック項目 |
|---------|------------|
| 可読性 | コードが理解しやすいか |
| 可読性 | 命名が適切か |
| 設計 | 単一責任の原則に従っているか |
| 設計 | 適切な抽象化がされているか |
| 保守性 | 将来の変更に対応しやすいか |
| 規約 | コーディング規約に準拠しているか |

### 5.2 レビューコメントの種別

コメントにはプレフィックスを付けて意図を明確にする。

| プレフィックス | 意味 | 対応 |
|--------------|------|------|
| `[must]` | 必ず修正が必要 | マージブロック |
| `[should]` | 修正を推奨 | 議論可 |
| `[nit]` | 細かい指摘 | 修正は任意 |
| `[question]` | 質問・確認 | 回答必要 |
| `[praise]` | 良い実装への賞賛 | 対応不要 |
| `[suggestion]` | 代替案の提案 | 検討必要 |

### 5.3 レビュー対応のルール

- レビューコメントには必ず返信する
- `[must]` コメントは全て対応してから再レビューを依頼する
- 議論が平行線の場合はテックリードが最終判断する
- レビュー依頼から24時間以内にレビューを開始する

---

## 6. Git ワークフロー

### 6.1 機能開発フロー

```
1. Issue を確認し、担当をアサインする
2. develop から feature ブランチを作成する
   $ git checkout develop
   $ git pull origin develop
   $ git checkout -b feature/RSK-001-risk-assessment-form

3. 機能を実装し、コミットする
   $ git add <files>
   $ git commit -m "feat(risk): リスク評価フォームのUIを実装"

4. 定期的に develop の変更を取り込む
   $ git fetch origin
   $ git rebase origin/develop

5. リモートにプッシュする
   $ git push origin feature/RSK-001-risk-assessment-form

6. PR を作成し、レビューを依頼する

7. レビュー指摘を修正し、再プッシュする

8. CI が通り、レビュー承認を得たらマージする
   （Squash and Merge）

9. feature ブランチを削除する
```

### 6.2 リリースフロー

```
1. develop から release ブランチを作成する
   $ git checkout -b release/v1.0.0 develop

2. バージョン番号を更新する
   $ git commit -m "chore: バージョンを v1.0.0 に更新"

3. リリース候補のテスト・修正を行う

4. main にマージする（PR経由）

5. タグを付与する
   $ git tag -a v1.0.0 -m "Release v1.0.0"
   $ git push origin v1.0.0

6. develop にもマージする

7. release ブランチを削除する
```

### 6.3 ホットフィックスフロー

```
1. main から hotfix ブランチを作成する
   $ git checkout -b hotfix/fix-critical-auth-bug main

2. 修正を実施する
   $ git commit -m "fix(auth): 認証トークンの検証不備を修正"

3. main にマージする（PR経由、緊急レビュー）

4. タグを付与する（パッチバージョンアップ）
   $ git tag -a v1.0.1 -m "Hotfix v1.0.1"

5. develop にもマージする

6. hotfix ブランチを削除する
```

---

## 7. バージョニング

### 7.1 セマンティックバージョニング

[Semantic Versioning 2.0.0](https://semver.org/) に準拠する。

```
MAJOR.MINOR.PATCH

例: v1.2.3
```

| 要素 | 更新タイミング | 例 |
|------|--------------|-----|
| MAJOR | 後方互換性のない変更 | API仕様の破壊的変更 |
| MINOR | 後方互換性のある機能追加 | 新しいAPIエンドポイントの追加 |
| PATCH | バグ修正 | 既存機能の不具合修正 |

### 7.2 プレリリースバージョン

```
v1.0.0-alpha.1   # アルファ版
v1.0.0-beta.1    # ベータ版
v1.0.0-rc.1      # リリース候補
```

---

## 8. Git 設定

### 8.1 推奨 .gitconfig

```ini
[core]
  autocrlf = input
  eol = lf

[pull]
  rebase = true

[fetch]
  prune = true

[diff]
  algorithm = histogram

[merge]
  conflictstyle = zdiff3
```

### 8.2 .gitignore（主要項目）

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
venv/
.venv/

# Node.js
node_modules/
dist/

# IDE
.vscode/
.idea/

# 環境変数
.env
.env.local
.env.*.local

# データベース
*.sqlite3

# メディア
media/

# ログ
*.log

# Docker
docker-compose.override.yml

# OS
.DS_Store
Thumbs.db

# カバレッジ
htmlcov/
.coverage
coverage/
```

---

## 9. 禁止事項

| 禁止事項 | 理由 |
|---------|------|
| `main` / `develop` への直接プッシュ | コードレビューをバイパスするため |
| `--force` プッシュ（共有ブランチ） | 他メンバーの変更が消失するため |
| 機密情報のコミット | セキュリティリスク |
| 大きなバイナリファイルのコミット | リポジトリサイズの肥大化 |
| マージコミットを含む feature ブランチ | 履歴が複雑になるため（rebase を使用） |

---

## 改訂履歴

| バージョン | 日付 | 変更内容 | 変更者 |
|-----------|------|---------|--------|
| 1.0 | 2026-03-26 | 初版作成 | 開発チーム |
