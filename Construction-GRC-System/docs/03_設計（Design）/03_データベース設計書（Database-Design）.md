# データベース設計書（Database Design）

## 建設業 統合リスク＆コンプライアンス管理システム（Construction-GRC-System）

| 項目 | 内容 |
|------|------|
| **文書番号** | DES-GRC-003 |
| **バージョン** | 1.0.0 |
| **作成日** | 2026-03-26 |
| **最終更新日** | 2026-03-26 |
| **作成者** | みらい建設工業 IT部門 |
| **承認者** | 情報セキュリティ管理責任者（CISO） |
| **対象リポジトリ** | Kensan196948G/Construction-GRC-System |
| **準拠規格** | ISO27001:2022 / NIST CSF 2.0 / 建設業法 / 品確法 / 労安法 |
| **技術スタック** | Django+DRF / Vue.js 3+Vuetify 3 / PostgreSQL 16 / Redis 7 / Celery |

---

## 改訂履歴

| バージョン | 日付 | 変更内容 | 変更者 |
|-----------|------|---------|--------|
| 1.0.0 | 2026-03-26 | 初版作成 | IT部門 |

---

## 目次

1. [設計方針](#1-設計方針)
2. [ER図（テキスト表現）](#2-er図テキスト表現)
3. [テーブル定義](#3-テーブル定義)
4. [インデックス設計](#4-インデックス設計)
5. [パーティション戦略](#5-パーティション戦略)
6. [マイグレーション方針](#6-マイグレーション方針)

---

## 1. 設計方針

### 1.1 基本方針

| 項目 | 方針 |
|------|------|
| **主キー** | UUID v4（全テーブル統一） |
| **論理削除** | is_deleted + deleted_at フラグ方式 |
| **タイムスタンプ** | created_at / updated_at を全テーブルに付与 |
| **作成者・更新者** | created_by / updated_by を全テーブルに付与 |
| **文字コード** | UTF-8 |
| **照合順序** | ja_JP.UTF-8 |
| **外部キー制約** | PROTECT（参照先の安易な削除を防止） |
| **カスケード削除** | 親子関係が明確な場合のみCASCADE |

### 1.2 命名規約

| 対象 | 規約 | 例 |
|------|------|-----|
| テーブル名 | snake_case、Djangoアプリ名プレフィックス | `risks_risk`, `audits_audit` |
| カラム名 | snake_case | `risk_level`, `created_at` |
| 外部キー | 参照先テーブル名_id | `owner_id`, `framework_id` |
| インデックス | ix_{テーブル名}_{カラム名} | `ix_risks_risk_status` |
| ユニーク制約 | uq_{テーブル名}_{カラム名} | `uq_risks_risk_risk_id` |

---

## 2. ER図（テキスト表現）

### 2.1 全体ER図

```
┌──────────────────┐
│   accounts_user  │
│──────────────────│
│ PK id (UUID)     │
│    email         │
│    username      │
│    role          │
│    department    │
│    is_active     │
└────────┬─────────┘
         │ 1
         │
    ┌────┴───────────────────────────────────────────────────────┐
    │                        │               │                    │
    ▼ *                      ▼ *             ▼ *                  ▼ *
┌──────────────┐  ┌──────────────────┐  ┌──────────────┐  ┌──────────────┐
│  risks_risk  │  │compliance_       │  │controls_     │  │ audits_audit │
│──────────────│  │requirement       │  │control       │  │──────────────│
│ PK id        │  │──────────────────│  │──────────────│  │ PK id        │
│    risk_id   │  │ PK id            │  │ PK id        │  │    audit_id  │
│    title     │  │    requirement_id│  │    control_id│  │    title     │
│    category  │  │    title         │  │    title     │  │    scope     │
│ FK owner_id  │  │ FK framework_id  │  │    type      │  │ FK lead_     │
│    status    │  │    status        │  │ FK owner_id  │  │   auditor_id │
│    score     │  │ FK responsible_  │  │ FK framework_│  │    status    │
│    level     │  │    person_id     │  │    id        │  │              │
└──────┬───────┘  └────────┬─────────┘  └──────┬───────┘  └──────┬───────┘
       │                   │                    │                  │
       │ 1                 │ 1                  │ 1                │ 1
       │                   │                    │                  │
       ▼ *                 ▼ *                  ▼ *                ▼ *
┌──────────────┐  ┌──────────────────┐  ┌──────────────┐  ┌──────────────┐
│risk_evaluation│  │compliance_       │  │controls_     │  │audit_finding │
│──────────────│  │assessment        │  │control_test  │  │──────────────│
│ PK id        │  │──────────────────│  │──────────────│  │ PK id        │
│ FK risk_id   │  │ PK id            │  │ PK id        │  │ FK audit_id  │
│    likelihood│  │ FK requirement_id│  │ FK control_id│  │    finding_id│
│    impact    │  │    status        │  │    result    │  │    type      │
│    score     │  │    assessor_id   │  │ FK tester_id │  │    title     │
└──────────────┘  └──────────────────┘  └──────────────┘  └──────┬───────┘
       │                   │                    │                  │
       ▼                   ▼                    ▼                  ▼
┌──────────────┐  ┌──────────────────┐  ┌──────────────┐  ┌──────────────┐
│risk_treatment│  │gap_analysis      │  │evidence_file │  │corrective_   │
│_plan         │  │──────────────────│  │──────────────│  │action_request│
│──────────────│  │ PK id            │  │ PK id        │  │──────────────│
│ PK id        │  │ FK framework_id  │  │    file      │  │ PK id        │
│ FK risk_id   │  │    compliance_   │  │    sha256    │  │ FK finding_id│
│    strategy  │  │    rate          │  │    (Generic) │  │    due_date  │
│    due_date  │  └──────────────────┘  └──────────────┘  │    status    │
└──────────────┘                                           └──────────────┘

┌──────────────────┐     ┌──────────────────┐
│frameworks_       │     │frameworks_       │
│framework         │     │framework_control │
│──────────────────│     │──────────────────│
│ PK id            │ 1──*│ PK id            │
│    code          │     │ FK framework_id  │
│    name          │     │ FK category_id   │
│    version       │     │    code          │
└──────────────────┘     │    title         │
                          └──────────────────┘

┌──────────────────┐     ┌──────────────────┐
│common_audit_log  │     │reports_alert_rule│
│──────────────────│     │──────────────────│
│ PK id (BIGINT)   │     │ PK id            │
│    timestamp     │     │    name          │
│    user_id       │     │    trigger_type  │
│    action        │     │    is_active     │
│    resource_type │     └──────────────────┘
│    resource_id   │
└──────────────────┘
```

### 2.2 多対多リレーション

```
risks_risk ──*──*── controls_control
               │
        risks_risk_controls (中間テーブル)

risks_risk ──*──*── frameworks_framework_control
               │
        risks_risk_frameworks (中間テーブル)

compliance_requirement ──*──*── controls_control
               │
        compliance_requirement_controls (中間テーブル)

audits_audit ──*──*── accounts_user (team_members)
               │
        audits_audit_team_members (中間テーブル)
```

---

## 3. テーブル定義

### 3.1 accounts_user

| カラム名 | データ型 | NULL | デフォルト | 説明 |
|---------|---------|:----:|----------|------|
| id | UUID | NO | uuid4() | 主キー |
| email | VARCHAR(254) | NO | — | メールアドレス（UNIQUE） |
| username | VARCHAR(150) | NO | — | ユーザー名（UNIQUE） |
| password | VARCHAR(128) | NO | — | パスワードハッシュ（bcrypt） |
| first_name | VARCHAR(30) | NO | — | 名 |
| last_name | VARCHAR(30) | NO | — | 姓 |
| department | VARCHAR(100) | NO | — | 部門 |
| role | VARCHAR(30) | NO | — | ロール（admin/risk_owner/compliance_officer/auditor/executive/user） |
| is_active | BOOLEAN | NO | true | アクティブフラグ |
| is_staff | BOOLEAN | NO | false | 管理画面アクセス権 |
| is_superuser | BOOLEAN | NO | false | スーパーユーザーフラグ |
| login_failure_count | INTEGER | NO | 0 | ログイン失敗回数 |
| locked_at | TIMESTAMP | YES | NULL | アカウントロック日時 |
| last_login | TIMESTAMP | YES | NULL | 最終ログイン日時 |
| last_login_ip | INET | YES | NULL | 最終ログインIP |
| password_changed_at | TIMESTAMP | YES | NULL | パスワード変更日時 |
| created_at | TIMESTAMP | NO | now() | 作成日時 |
| updated_at | TIMESTAMP | NO | now() | 更新日時 |

### 3.2 risks_risk

| カラム名 | データ型 | NULL | デフォルト | 説明 |
|---------|---------|:----:|----------|------|
| id | UUID | NO | uuid4() | 主キー |
| risk_id | VARCHAR(20) | NO | — | リスクID（UNIQUE, RSK-YYYY-NNNN） |
| title | VARCHAR(200) | NO | — | リスク名 |
| description | TEXT | NO | — | リスク説明 |
| category | VARCHAR(50) | NO | — | リスクカテゴリ |
| sub_category | VARCHAR(50) | YES | '' | サブカテゴリ |
| owner_id | UUID(FK) | NO | — | リスクオーナー |
| department | VARCHAR(100) | NO | — | 担当部門 |
| project | VARCHAR(200) | YES | '' | 関連プロジェクト |
| status | VARCHAR(30) | NO | 'identified' | ステータス |
| inherent_likelihood | INTEGER | YES | NULL | 固有リスク発生確率（1-5） |
| inherent_impact | INTEGER | YES | NULL | 固有リスク影響度（1-5） |
| inherent_score | INTEGER | YES | NULL | 固有リスクスコア（自動計算） |
| inherent_level | VARCHAR(20) | YES | '' | 固有リスクレベル |
| residual_likelihood | INTEGER | YES | NULL | 残留リスク発生確率 |
| residual_impact | INTEGER | YES | NULL | 残留リスク影響度 |
| residual_score | INTEGER | YES | NULL | 残留リスクスコア |
| residual_level | VARCHAR(20) | YES | '' | 残留リスクレベル |
| is_deleted | BOOLEAN | NO | false | 論理削除フラグ |
| deleted_at | TIMESTAMP | YES | NULL | 削除日時 |
| created_by_id | UUID(FK) | YES | NULL | 作成者 |
| updated_by_id | UUID(FK) | YES | NULL | 更新者 |
| created_at | TIMESTAMP | NO | now() | 作成日時 |
| updated_at | TIMESTAMP | NO | now() | 更新日時 |

### 3.3 risks_riskevaluation

| カラム名 | データ型 | NULL | デフォルト | 説明 |
|---------|---------|:----:|----------|------|
| id | UUID | NO | uuid4() | 主キー |
| risk_id | UUID(FK) | NO | — | 対象リスク |
| evaluation_date | DATE | NO | — | 評価日 |
| likelihood | INTEGER | NO | — | 発生確率（1-5） |
| impact_financial | INTEGER | NO | — | 影響度：財務（1-5） |
| impact_operational | INTEGER | NO | — | 影響度：運用（1-5） |
| impact_legal | INTEGER | NO | — | 影響度：法令（1-5） |
| impact_safety | INTEGER | NO | — | 影響度：安全（1-5） |
| impact_reputation | INTEGER | NO | — | 影響度：信用（1-5） |
| max_impact | INTEGER | NO | — | 最大影響度（自動計算） |
| inherent_score | INTEGER | NO | — | 固有リスクスコア（自動計算） |
| control_effectiveness | VARCHAR(20) | NO | — | 統制有効性 |
| residual_score | INTEGER | NO | — | 残留リスクスコア（自動計算） |
| comments | TEXT | YES | '' | 評価コメント |
| evaluator_id | UUID(FK) | NO | — | 評価者 |
| created_at | TIMESTAMP | NO | now() | 作成日時 |
| updated_at | TIMESTAMP | NO | now() | 更新日時 |

### 3.4 compliance_compliancerequirement

| カラム名 | データ型 | NULL | デフォルト | 説明 |
|---------|---------|:----:|----------|------|
| id | UUID | NO | uuid4() | 主キー |
| requirement_id | VARCHAR(20) | NO | — | 要件ID（UNIQUE, CMP-YYYY-NNNN） |
| framework_id | UUID(FK) | NO | — | 対象フレームワーク |
| framework_control_id | UUID(FK) | YES | NULL | フレームワーク管理策 |
| title | VARCHAR(300) | NO | — | 要件名称 |
| description | TEXT | NO | — | 要件内容 |
| legal_reference | VARCHAR(200) | YES | '' | 法令参照 |
| scope | VARCHAR(50) | NO | — | 適用範囲 |
| responsible_department | VARCHAR(100) | NO | — | 責任部門 |
| responsible_person_id | UUID(FK) | NO | — | 責任者 |
| compliance_status | VARCHAR(30) | NO | 'not_assessed' | 準拠ステータス |
| due_date | DATE | YES | NULL | 準拠期限 |
| is_deleted | BOOLEAN | NO | false | 論理削除フラグ |
| created_at | TIMESTAMP | NO | now() | 作成日時 |
| updated_at | TIMESTAMP | NO | now() | 更新日時 |

### 3.5 controls_control

| カラム名 | データ型 | NULL | デフォルト | 説明 |
|---------|---------|:----:|----------|------|
| id | UUID | NO | uuid4() | 主キー |
| control_id | VARCHAR(20) | NO | — | 統制ID（UNIQUE, CTL-FW-NNNN） |
| title | VARCHAR(300) | NO | — | 統制項目名 |
| description | TEXT | NO | — | 説明 |
| control_type | VARCHAR(20) | NO | — | 統制タイプ |
| frequency | VARCHAR(20) | NO | — | 実施頻度 |
| owner_id | UUID(FK) | NO | — | 統制オーナー |
| framework_id | UUID(FK) | YES | NULL | 対象フレームワーク |
| framework_control_id | UUID(FK) | YES | NULL | フレームワーク管理策 |
| test_procedure | TEXT | YES | '' | テスト手順 |
| effectiveness | VARCHAR(20) | NO | 'not_assessed' | 有効性 |
| last_test_date | DATE | YES | NULL | 最終テスト日 |
| next_test_date | DATE | YES | NULL | 次回テスト日 |
| is_deleted | BOOLEAN | NO | false | 論理削除フラグ |
| created_at | TIMESTAMP | NO | now() | 作成日時 |
| updated_at | TIMESTAMP | NO | now() | 更新日時 |

### 3.6 controls_evidencefile

| カラム名 | データ型 | NULL | デフォルト | 説明 |
|---------|---------|:----:|----------|------|
| id | UUID | NO | uuid4() | 主キー |
| file | VARCHAR(255) | NO | — | ファイルパス |
| original_filename | VARCHAR(255) | NO | — | 元ファイル名 |
| file_size | INTEGER | NO | — | ファイルサイズ（bytes） |
| mime_type | VARCHAR(100) | NO | — | MIMEタイプ |
| sha256_hash | VARCHAR(64) | NO | — | SHA-256ハッシュ |
| description | TEXT | YES | '' | 説明 |
| tags | JSONB | NO | '[]' | タグ |
| content_type_id | INTEGER(FK) | NO | — | コンテンツタイプ（Generic FK） |
| object_id | UUID | NO | — | 対象オブジェクトID |
| is_deleted | BOOLEAN | NO | false | 論理削除フラグ |
| deleted_at | TIMESTAMP | YES | NULL | 削除日時 |
| delete_reason | TEXT | YES | '' | 削除理由 |
| created_by_id | UUID(FK) | YES | NULL | アップロード者 |
| created_at | TIMESTAMP | NO | now() | 作成日時 |
| updated_at | TIMESTAMP | NO | now() | 更新日時 |

### 3.7 audits_audit

| カラム名 | データ型 | NULL | デフォルト | 説明 |
|---------|---------|:----:|----------|------|
| id | UUID | NO | uuid4() | 主キー |
| audit_id | VARCHAR(20) | NO | — | 監査ID（UNIQUE, AUD-YYYY-NNNN） |
| title | VARCHAR(200) | NO | — | 監査名 |
| audit_type | VARCHAR(20) | NO | — | 監査種別 |
| scope | TEXT | NO | — | 監査スコープ |
| target_department | VARCHAR(100) | NO | — | 監査対象部門 |
| framework_id | UUID(FK) | YES | NULL | 対象フレームワーク |
| lead_auditor_id | UUID(FK) | NO | — | 主任監査員 |
| planned_start_date | DATE | NO | — | 計画開始日 |
| planned_end_date | DATE | NO | — | 計画終了日 |
| actual_start_date | DATE | YES | NULL | 実施開始日 |
| actual_end_date | DATE | YES | NULL | 実施終了日 |
| status | VARCHAR(20) | NO | 'draft' | ステータス |
| approved_by_id | UUID(FK) | YES | NULL | 承認者 |
| approved_at | TIMESTAMP | YES | NULL | 承認日時 |
| is_deleted | BOOLEAN | NO | false | 論理削除フラグ |
| created_at | TIMESTAMP | NO | now() | 作成日時 |
| updated_at | TIMESTAMP | NO | now() | 更新日時 |

### 3.8 audits_auditfinding

| カラム名 | データ型 | NULL | デフォルト | 説明 |
|---------|---------|:----:|----------|------|
| id | UUID | NO | uuid4() | 主キー |
| finding_id | VARCHAR(20) | NO | — | 所見ID（UNIQUE, FND-YYYY-NNNN） |
| audit_id | UUID(FK) | NO | — | 監査 |
| finding_type | VARCHAR(30) | NO | — | 所見タイプ |
| title | VARCHAR(200) | NO | — | 所見タイトル |
| description | TEXT | NO | — | 詳細説明 |
| reference_control_id | UUID(FK) | YES | NULL | 根拠統制項目 |
| impact_scope | VARCHAR(200) | NO | — | 影響範囲 |
| risk_level | VARCHAR(20) | YES | '' | リスクレベル |
| is_recurrence | BOOLEAN | NO | false | 再発フラグ |
| previous_finding_id | UUID(FK) | YES | NULL | 前回所見 |
| status | VARCHAR(20) | NO | 'open' | ステータス |
| is_deleted | BOOLEAN | NO | false | 論理削除フラグ |
| created_at | TIMESTAMP | NO | now() | 作成日時 |
| updated_at | TIMESTAMP | NO | now() | 更新日時 |

### 3.9 common_auditlog

| カラム名 | データ型 | NULL | デフォルト | 説明 |
|---------|---------|:----:|----------|------|
| id | BIGSERIAL | NO | auto | 主キー（連番） |
| timestamp | TIMESTAMP | NO | now() | タイムスタンプ |
| user_id | UUID(FK) | YES | NULL | 操作ユーザー |
| user_email | VARCHAR(254) | NO | — | ユーザーメール（非正規化） |
| action | VARCHAR(50) | NO | — | 操作種別 |
| resource_type | VARCHAR(100) | NO | — | リソースタイプ |
| resource_id | VARCHAR(100) | YES | '' | リソースID |
| description | TEXT | YES | '' | 説明 |
| ip_address | INET | YES | NULL | IPアドレス |
| user_agent | TEXT | YES | '' | User-Agent |
| request_data | JSONB | YES | NULL | リクエストデータ |
| response_status | INTEGER | YES | NULL | レスポンスステータス |
| changes | JSONB | YES | NULL | 変更差分 |

### 3.10 frameworks_framework / frameworks_frameworkcontrol

| テーブル | カラム名 | データ型 | NULL | 説明 |
|---------|---------|---------|:----:|------|
| frameworks_framework | id | UUID | NO | 主キー |
| | code | VARCHAR(50) | NO | コード（UNIQUE） |
| | name | VARCHAR(200) | NO | 名称 |
| | version | VARCHAR(20) | NO | バージョン |
| | description | TEXT | YES | 説明 |
| | is_active | BOOLEAN | NO | 有効フラグ |
| frameworks_frameworkcategory | id | UUID | NO | 主キー |
| | framework_id | UUID(FK) | NO | フレームワーク |
| | parent_id | UUID(FK) | YES | 親カテゴリ |
| | code | VARCHAR(50) | NO | コード |
| | name | VARCHAR(300) | NO | 名称 |
| | sort_order | INTEGER | NO | 並び順 |
| frameworks_frameworkcontrol | id | UUID | NO | 主キー |
| | framework_id | UUID(FK) | NO | フレームワーク |
| | category_id | UUID(FK) | NO | カテゴリ |
| | code | VARCHAR(50) | NO | コード |
| | title | VARCHAR(300) | NO | タイトル |
| | description | TEXT | NO | 説明 |
| | guidance | TEXT | YES | ガイダンス |
| | sort_order | INTEGER | NO | 並び順 |

---

## 4. インデックス設計

### 4.1 インデックス一覧

| テーブル | インデックス名 | カラム | 種別 | 目的 |
|---------|-------------|--------|------|------|
| accounts_user | uq_user_email | email | UNIQUE | ログイン検索 |
| accounts_user | uq_user_username | username | UNIQUE | ユーザー名検索 |
| accounts_user | ix_user_role | role | B-tree | ロール別フィルタ |
| accounts_user | ix_user_department | department | B-tree | 部門別フィルタ |
| risks_risk | uq_risk_risk_id | risk_id | UNIQUE | リスクID検索 |
| risks_risk | ix_risk_status | status | B-tree | ステータスフィルタ |
| risks_risk | ix_risk_category | category | B-tree | カテゴリフィルタ |
| risks_risk | ix_risk_owner | owner_id | B-tree | オーナー別検索 |
| risks_risk | ix_risk_level | inherent_level | B-tree | レベルフィルタ |
| risks_risk | ix_risk_deleted | is_deleted | B-tree (partial) | 論理削除フィルタ |
| risks_risk | ix_risk_score_level | (inherent_likelihood, inherent_impact) | B-tree | ヒートマップ集計 |
| risks_riskevaluation | ix_eval_risk | risk_id | B-tree | リスク別評価取得 |
| risks_riskevaluation | ix_eval_date | evaluation_date | B-tree | 日付範囲検索 |
| compliance_* | uq_compliance_req_id | requirement_id | UNIQUE | 要件ID検索 |
| compliance_* | ix_compliance_framework | framework_id | B-tree | フレームワーク別 |
| compliance_* | ix_compliance_status | compliance_status | B-tree | ステータスフィルタ |
| controls_control | uq_control_id | control_id | UNIQUE | 統制ID検索 |
| controls_control | ix_control_framework | framework_id | B-tree | フレームワーク別 |
| controls_control | ix_control_effectiveness | effectiveness | B-tree | 有効性フィルタ |
| controls_control | ix_control_next_test | next_test_date | B-tree | テストスケジュール |
| controls_controltest | ix_test_control | control_id | B-tree | 統制別テスト取得 |
| controls_controltest | ix_test_result | result | B-tree | 結果フィルタ |
| audits_audit | uq_audit_id | audit_id | UNIQUE | 監査ID検索 |
| audits_audit | ix_audit_status | status | B-tree | ステータスフィルタ |
| audits_auditfinding | uq_finding_id | finding_id | UNIQUE | 所見ID検索 |
| audits_auditfinding | ix_finding_audit | audit_id | B-tree | 監査別所見 |
| audits_auditfinding | ix_finding_status | status | B-tree | ステータスフィルタ |
| common_auditlog | ix_auditlog_timestamp | timestamp | B-tree | 時系列検索 |
| common_auditlog | ix_auditlog_user | user_id, timestamp | B-tree | ユーザー別検索 |
| common_auditlog | ix_auditlog_resource | resource_type, resource_id | B-tree | リソース別検索 |
| common_auditlog | ix_auditlog_action | action, timestamp | B-tree | 操作種別検索 |

### 4.2 部分インデックス

```sql
-- アクティブなリスクのみのインデックス（論理削除を除外）
CREATE INDEX ix_risk_active ON risks_risk (status, inherent_level)
WHERE is_deleted = false;

-- 未完了の是正措置のみ
CREATE INDEX ix_ca_active ON controls_correctiveaction (due_date, status)
WHERE status NOT IN ('completed') AND is_deleted = false;

-- オープンな監査所見のみ
CREATE INDEX ix_finding_open ON audits_auditfinding (finding_type, audit_id)
WHERE status = 'open' AND is_deleted = false;
```

---

## 5. パーティション戦略

### 5.1 監査ログテーブルのパーティション

```sql
-- 月次レンジパーティション
CREATE TABLE common_auditlog (
    id BIGSERIAL,
    timestamp TIMESTAMP NOT NULL,
    ...
) PARTITION BY RANGE (timestamp);

-- パーティション作成（月次）
CREATE TABLE common_auditlog_2026_01
    PARTITION OF common_auditlog
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE TABLE common_auditlog_2026_02
    PARTITION OF common_auditlog
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

-- 以降、月次で自動作成（pg_partman使用）
```

### 5.2 パーティション管理

| 設定 | 値 |
|------|-----|
| パーティション方式 | レンジパーティション（月次） |
| 対象テーブル | common_auditlog |
| 事前作成 | 3ヶ月先まで |
| 保持期間 | 84ヶ月（7年） |
| 自動管理 | pg_partman + Celery定期タスク |

---

## 6. マイグレーション方針

### 6.1 マイグレーション運用ルール

| 項目 | ルール |
|------|-------|
| マイグレーションファイル | Django makemigrations で自動生成 |
| 命名規則 | 自動生成番号 + 説明（例: 0001_initial, 0002_add_risk_level） |
| レビュー | PR時にマイグレーションSQLを確認 |
| ロールバック | 各マイグレーションにreverse操作を定義 |
| データマイグレーション | RunPython で別ファイルとして管理 |
| 本番適用 | CI/CDパイプラインで `python manage.py migrate` を実行 |

### 6.2 初期データ

| データ | 件数 | 投入方法 |
|-------|------|---------|
| ロール・権限定義 | 6ロール | データマイグレーション |
| ISO27001 Annex A管理策 | 93件 | fixtures (JSON) |
| NIST CSF 2.0カテゴリ | 6+22+106件 | fixtures (JSON) |
| 建設業法準拠要件 | 約30件 | fixtures (JSON) |
| リスクカテゴリマスタ | 6件 | データマイグレーション |
| デフォルトレポートテンプレート | 3件 | データマイグレーション |

### 6.3 本番デプロイ手順

```bash
# 1. バックアップ取得
pg_dump -Fc grc_db > backup_$(date +%Y%m%d).dump

# 2. マイグレーション実行（ダウンタイム最小化）
python manage.py migrate --plan  # 確認
python manage.py migrate         # 実行

# 3. 静的ファイル収集
python manage.py collectstatic --noinput

# 4. アプリケーション再起動
supervisorctl restart gunicorn
```
