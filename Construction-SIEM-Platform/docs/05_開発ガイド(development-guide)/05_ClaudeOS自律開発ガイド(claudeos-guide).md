# 🤖 ClaudeOS 自律開発ガイド（ClaudeOS Guide）

> ClaudeOS v4 による自律開発ワークフローとAgent Teams構成

---

## 📋 概要

| 項目 | 値 |
|------|------|
| バージョン | ClaudeOS v4 |
| 最大作業時間 | **8時間** |
| ループ構成 | Monitor → Development → Verify → Improvement |
| 品質基準 | STABLE 判定 |
| 連携 | GitHub Projects / Issues / PR / Actions |

---

## ⏱ ループ構成

### 8時間タイムライン

```
 0h        1h        3h        5h        8h
 │─────────│─────────│─────────│─────────│
 │ Monitor │  Dev    │ Verify  │ Improve │
 │  (1h)   │  (2h)  │  (2h)  │  (3h)   │
 └─────────┴─────────┴─────────┴─────────┘
```

### 各フェーズの詳細

| フェーズ | 時間 | 目的 | 主な作業 |
|---------|:----:|------|---------|
| 🔍 Monitor | 1h | 状況把握 | Issues確認、Projects更新、優先度判定 |
| 🛠 Development | 2h | 実装 | コーディング、feature ブランチ作成 |
| ✅ Verify | 2h | 検証 | テスト実行、CI確認、セキュリティスキャン |
| 🔄 Improvement | 3h | 改善 | コードレビュー修正、リファクタリング、ドキュメント |

---

## 🔍 Monitor フェーズ（1時間）

### 実施内容

| # | タスク | 説明 |
|:-:|--------|------|
| 1 | GitHub Issues 確認 | 新規Issue、アサインされたIssue |
| 2 | GitHub Projects 更新 | ステータス遷移 |
| 3 | CI/CD 状態確認 | 直近のワークフロー結果 |
| 4 | 優先度判定 | P1-P4 の判定と着手順序決定 |
| 5 | 作業計画策定 | 今回のループで実施する作業の決定 |

### GitHub Projects ステータス遷移

```
Inbox → Backlog → Ready → Development → Verify → Deploy Gate → Done
                                                       │
                                                       ▼
                                                    Blocked
```

| ステータス | 説明 |
|-----------|------|
| 📥 Inbox | 新規登録（未トリアージ） |
| 📋 Backlog | トリアージ済み（未着手） |
| ✅ Ready | 着手可能（依存関係解消済み） |
| 🛠 Development | 開発中 |
| 🔍 Verify | 検証中（CI/テスト） |
| 🚀 Deploy Gate | デプロイ待ち |
| ✅ Done | 完了 |
| ⛔ Blocked | ブロック中 |

---

## 🛠 Development フェーズ（2時間）

### 実施内容

| # | タスク | 説明 |
|:-:|--------|------|
| 1 | WorkTree 作成 | `git worktree add` で並列開発環境 |
| 2 | feature ブランチ作成 | `feature/<issue>-<description>` |
| 3 | コーディング | 規約に準拠した実装 |
| 4 | ローカルテスト | `pytest` で基本動作確認 |
| 5 | コミット | Conventional Commits 形式 |

### WorkTree 並列開発

```bash
# WorkTree 作成
git worktree add ../siem-feature-42 feature/42-incident-sla

# WorkTree で作業
cd ../siem-feature-42
# ... 開発作業 ...

# WorkTree 削除
git worktree remove ../siem-feature-42
```

---

## ✅ Verify フェーズ（2時間）

### 実施内容

| # | タスク | ツール | 基準 |
|:-:|--------|--------|------|
| 1 | ユニットテスト | pytest | 全テスト PASSED |
| 2 | カバレッジ | pytest-cov | 85% 以上 |
| 3 | リンティング | black, isort, flake8 | 差分 0 |
| 4 | セキュリティ | bandit | 検出 0件 |
| 5 | CI 確認 | GitHub Actions | 全ジョブ成功 |
| 6 | Docker ビルド | docker build | ビルド成功 |

### CI 失敗時の自動修復フロー

```
Verify 失敗
    │
    ▼
┌─────────────────┐
│ CI Manager       │ ← 失敗ジョブを特定
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Auto Repair      │ ← 自動修復を試行
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 再 Verify        │ ← 修復後に再検証
└─────────────────┘
```

---

## 🔄 Improvement フェーズ（3時間）

### 実施内容

| # | タスク | 説明 |
|:-:|--------|------|
| 1 | コードレビュー対応 | PR のレビューコメント修正 |
| 2 | リファクタリング | コード品質改善 |
| 3 | テスト追加 | カバレッジ向上 |
| 4 | ドキュメント更新 | API仕様・ガイド更新 |
| 5 | パフォーマンス改善 | ボトルネック対応 |
| 6 | 次フェーズ計画 | 残タスク整理・Issue更新 |

---

## 🎯 STABLE 判定条件

### 必須条件

| 条件 | 説明 |
|------|------|
| ✅ テスト全パス | pytest の全テスト PASSED |
| ✅ CI 全パス | GitHub Actions 全ジョブ成功 |
| ✅ Lint クリーン | black/isort/flake8 差分なし |
| ✅ Build 成功 | Docker ビルド成功 |
| ✅ セキュリティ 0 | bandit 検出 0件 |
| ✅ エラー 0 | ランタイムエラーなし |

### 連続パス回数（N）

| 変更の規模 | N回 | 例 |
|-----------|:---:|------|
| 🟢 small | 2 | ドキュメント、スタイル修正 |
| 🟡 normal | 3 | 機能追加、バグ修正 |
| 🔴 critical | 5 | セキュリティ修正、アーキテクチャ変更 |

---

## 👥 Agent Teams 構成

### チーム一覧

| エージェント | 役割 | 主な責務 |
|-------------|------|---------|
| 🎯 CTO | 最高技術責任者 | 最終判断、アーキテクチャ決定 |
| 🏗 Architect | アーキテクト | 設計レビュー、技術選定 |
| 💻 Developer | 開発者 | コーディング、実装 |
| 👀 Reviewer | レビュアー | コードレビュー、品質チェック |
| 🧪 QA | 品質保証 | テスト設計・実行 |
| 🛡 Security | セキュリティ | 脆弱性スキャン、セキュリティレビュー |
| 🚀 DevOps | デブオプス | CI/CD、インフラ、デプロイ |

### 連携フロー

```
CTO ──▶ Architect ──▶ Developer ──▶ Reviewer ──▶ QA
 ▲                                                │
 │                                                ▼
 └──────────────── Security ◀──── DevOps ◀────────┘
```

---

## ✅ 自動承認と慎重対象

### 🟢 自動承認対象（Auto Approve）

| カテゴリ | 例 |
|---------|------|
| フォーマット修正 | black/isort の適用 |
| ドキュメント更新 | typo修正、説明追記 |
| テスト追加 | 既存機能のテスト追加 |
| 依存パッケージ更新 | パッチバージョンアップ |
| CI設定微調整 | タイムアウト値変更等 |

### 🔴 慎重対象（Manual Review Required）

| カテゴリ | 例 | 必要なレビュー |
|---------|------|--------------|
| セキュリティ変更 | 認証ロジック変更、暗号化方式変更 | Security + CTO |
| アーキテクチャ変更 | データベーススキーマ変更、API破壊的変更 | Architect + CTO |
| インフラ変更 | Docker構成変更、CI/CD パイプライン変更 | DevOps + CTO |
| 権限変更 | RBAC ロール追加、パーミッション変更 | Security + Reviewer |
| データ削除 | マイグレーション、データクリーンアップ | CTO |

---

## 🛑 停止条件

| 条件 | 対応 |
|------|------|
| ⏱ 8時間到達 | 自動停止、最終報告出力 |
| 🔁 Loop Guard 発動 | 無限ループ検出時に停止 |
| 🔴 クリティカルエラー | 即時停止、CTO 判断待ち |
| 🛡 セキュリティインシデント | 即時停止、Security エージェント報告 |

---

## 📊 最終報告フォーマット

ループ終了時に以下のフォーマットで報告を出力します。

```markdown
# ClaudeOS 作業報告

## 開発内容
- [ ] 実装した機能の一覧

## テスト / CI 結果
- テスト数: xxx passed / xxx failed
- カバレッジ: xx%
- CI ステータス: PASSED / FAILED

## PR / Merge
- PR #xx: タイトル (MERGED / OPEN / DRAFT)

## デプロイ
- デプロイ対象: あり / なし
- デプロイステータス: 完了 / 未実施

## 残課題
- Issue #xx: 説明

## 次フェーズ
- 次に取り組むべきタスク
```
