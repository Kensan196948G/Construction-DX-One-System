# ER図・テーブル定義書
## IT変更管理・リリース自動化プラットフォーム（IT-Change-CAB-Platform）

| 項目 | 内容 |
|------|------|
| **文書番号** | DB-ER-001 |
| **バージョン** | 1.0.0 |
| **作成日** | 2026-03-26 |
| **作成者** | みらい建設工業 IT部門 |
| **承認者** | IT部門長 |
| **対象リポジトリ** | Kensan196948G/IT-Change-CAB-Platform |

---

## 1. ER図（テキスト表記）

```
┌──────────────┐       ┌──────────────────┐       ┌──────────────┐
│   users       │       │ change_requests   │       │ cab_sessions  │
│──────────────│       │──────────────────│       │──────────────│
│ PK id (UUID)  │◄──┐   │ PK id (UUID)      │   ┌──>│ PK id (UUID)  │
│ username      │   │   │ rfc_number        │   │   │ session_number│
│ email         │   │   │ title             │   │   │ scheduled_date│
│ password_hash │   │   │ description       │   │   │ status        │
│ display_name  │   ├───│ FK requester_id   │   │   │ FK chair_id   │──┐
│ role          │   ├───│ FK implementer_id │   │   │ attendees     │  │
│ department    │   │   │ change_type       │   │   │ minutes       │  │
│ is_active     │   │   │ priority          │   │   │ created_at    │  │
│ mfa_secret    │   │   │ status            │   │   └──────────────┘  │
│ created_at    │   │   │ target_systems    │   │                      │
│ updated_at    │   │   │ planned_start     │   │                      │
└──────────────┘   │   │ planned_end       │   │                      │
                    │   │ business_impact   │   │   ┌──────────────┐  │
                    │   │ technical_risk    │   │   │ cab_decisions  │  │
                    │   │ risk_assessment   │   │   │──────────────│  │
                    │   │ rollback_plan     │   │   │ PK id (UUID)  │  │
                    │   │ created_at        │   │   │ FK rfc_id     │──┘
                    │   │ updated_at        │   ├───│ FK session_id │
                    │   └────────┬─────────┘   │   │ decision      │
                    │            │              │   │ decision_reason│
                    │            │              │   │ conditions    │
                    │            │              │   │ votes (JSONB) │
                    │            │              │   │ decided_at    │
                    │            │              │   │ FK decided_by │──┐
                    │            │              │   └──────────────┘  │
                    │            │              │                      │
                    │            │              │   ┌──────────────┐  │
                    │            │              │   │cab_votes      │  │
                    │            │              │   │──────────────│  │
                    │            │              │   │ PK id (UUID)  │  │
                    │            │              ├───│ FK decision_id│  │
                    │            │              │   │ FK voter_id   │──┤
                    │            │              │   │ vote          │  │
                    │            │              │   │ comment       │  │
                    │            │              │   │ voted_at      │  │
                    │            │              │   └──────────────┘  │
                    │            │              │                      │
                    │   ┌────────▼─────────┐   │                      │
                    │   │execution_records  │   │   ┌──────────────┐  │
                    │   │──────────────────│   │   │freeze_periods │  │
                    │   │ PK id (UUID)      │   │   │──────────────│  │
                    │   │ FK rfc_id         │   │   │ PK id (UUID)  │  │
                    ├───│ FK implementer_id │   │   │ name          │  │
                    │   │ actual_start      │   │   │ start_date    │  │
                    │   │ actual_end        │   │   │ end_date      │  │
                    │   │ result            │   │   │ change_types_ │  │
                    │   │ details           │   │   │  blocked      │  │
                    │   │ deviation_notes   │   │   │ reason        │  │
                    │   │ created_at        │   │   │ FK created_by │──┤
                    │   └────────┬─────────┘   │   │ created_at    │  │
                    │            │              │   └──────────────┘  │
                    │   ┌────────▼─────────┐   │                      │
                    │   │checklists         │   │   ┌──────────────┐  │
                    │   │──────────────────│   │   │post_impl_     │  │
                    │   │ PK id (UUID)      │   │   │ reviews       │  │
                    │   │ FK rfc_id         │   │   │──────────────│  │
                    │   │ phase             │   │   │ PK id (UUID)  │  │
                    │   │ items (JSONB)     │   │   │ FK rfc_id     │──┘
                    │   │ completed_at      │   │   │ success_level │
                    │   │ created_at        │   │   │ variance_notes│
                    │   └──────────────────┘   │   │ incidents     │
                    │                           │   │ root_cause    │
                    │   ┌──────────────────┐   │   │ improvements  │
                    │   │rfc_comments       │   │   │ lessons_learned│
                    │   │──────────────────│   │   │ FK reviewer_id│──┐
                    │   │ PK id (UUID)      │   │   │ reviewed_at   │  │
                    │   │ FK rfc_id         │───┘   │ created_at    │  │
                    ├───│ FK author_id      │       └──────────────┘  │
                    │   │ content           │                          │
                    │   │ created_at        │   ┌──────────────┐      │
                    │   └──────────────────┘   │audit_logs     │      │
                    │                           │──────────────│      │
                    │                           │ PK id (UUID)  │      │
                    └───────────────────────────│ FK user_id    │      │
                                                │ action        │      │
                                                │ entity_type   │      │
                                                │ entity_id     │      │
                                                │ old_values    │      │
                                                │ new_values    │      │
                                                │ ip_address    │      │
                                                │ user_agent    │      │
                                                │ created_at    │      │
                                                └──────────────┘      │
                                                                       │
                    ┌──────────────────┐                                │
                    │notifications     │                                │
                    │──────────────────│                                │
                    │ PK id (UUID)      │                                │
                    │ FK recipient_id   │────────────────────────────────┘
                    │ FK rfc_id         │
                    │ type              │
                    │ channel           │
                    │ subject           │
                    │ body              │
                    │ status            │
                    │ sent_at           │
                    │ created_at        │
                    └──────────────────┘
```

---

## 2. テーブル定義

### 2.1 users（ユーザ）テーブル

| カラム名 | データ型 | NULL | デフォルト | 説明 |
|---------|---------|------|----------|------|
| id | UUID | NOT NULL | gen_random_uuid() | 主キー |
| username | VARCHAR(50) | NOT NULL | - | ユーザ名（一意） |
| email | VARCHAR(255) | NOT NULL | - | メールアドレス（一意） |
| password_hash | VARCHAR(255) | NOT NULL | - | bcryptハッシュ |
| display_name | VARCHAR(100) | NOT NULL | - | 表示名 |
| role | VARCHAR(20) | NOT NULL | 'requester' | admin/cab_chair/cab_member/requester/implementer/viewer/executive |
| department | VARCHAR(100) | NULL | - | 所属部門 |
| phone | VARCHAR(20) | NULL | - | 電話番号（緊急連絡用） |
| is_active | BOOLEAN | NOT NULL | TRUE | アカウント有効/無効 |
| mfa_secret | VARCHAR(255) | NULL | - | TOTP MFA秘密鍵（暗号化） |
| mfa_enabled | BOOLEAN | NOT NULL | FALSE | MFA有効/無効 |
| last_login_at | TIMESTAMPTZ | NULL | - | 最終ログイン日時 |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | 作成日時 |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | 更新日時 |

**インデックス:**

| インデックス名 | カラム | 種類 |
|-------------|--------|------|
| users_pkey | id | PRIMARY KEY |
| users_username_unique | username | UNIQUE |
| users_email_unique | email | UNIQUE |
| idx_users_role | role | INDEX |
| idx_users_active | is_active | INDEX |

```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username        VARCHAR(50) UNIQUE NOT NULL,
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    display_name    VARCHAR(100) NOT NULL,
    role            VARCHAR(20) NOT NULL DEFAULT 'requester'
                    CHECK (role IN ('admin','cab_chair','cab_member','requester','implementer','viewer','executive')),
    department      VARCHAR(100),
    phone           VARCHAR(20),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    mfa_secret      VARCHAR(255),
    mfa_enabled     BOOLEAN NOT NULL DEFAULT FALSE,
    last_login_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

### 2.2 change_requests（変更申請）テーブル

| カラム名 | データ型 | NULL | デフォルト | 説明 |
|---------|---------|------|----------|------|
| id | UUID | NOT NULL | gen_random_uuid() | 主キー |
| rfc_number | VARCHAR(20) | NOT NULL | - | RFC番号（RFC-YYYY-NNN形式、一意） |
| title | VARCHAR(300) | NOT NULL | - | 変更タイトル |
| description | TEXT | NOT NULL | - | 変更の詳細説明 |
| change_type | VARCHAR(20) | NOT NULL | - | standard/normal/major/emergency |
| priority | VARCHAR(20) | NOT NULL | 'medium' | low/medium/high/critical |
| status | VARCHAR(30) | NOT NULL | 'draft' | 状態（下記参照） |
| target_systems | VARCHAR(100)[] | NOT NULL | - | 対象システム配列 |
| target_ci_ids | UUID[] | NULL | - | CMDB CI ID配列 |
| affected_users | INTEGER | NULL | - | 影響ユーザ数 |
| planned_start | TIMESTAMPTZ | NOT NULL | - | 計画開始日時 |
| planned_end | TIMESTAMPTZ | NOT NULL | - | 計画終了日時 |
| actual_start | TIMESTAMPTZ | NULL | - | 実績開始日時 |
| actual_end | TIMESTAMPTZ | NULL | - | 実績終了日時 |
| business_impact | TEXT | NOT NULL | - | 業務への影響 |
| technical_risk | VARCHAR(20) | NOT NULL | - | low/medium/high/critical |
| risk_assessment | TEXT | NOT NULL | - | リスク評価詳細 |
| risk_score | INTEGER | NULL | - | 自動計算リスクスコア |
| rollback_plan | TEXT | NOT NULL | - | ロールバック手順 |
| rollback_trigger | VARCHAR(200) | NULL | - | ロールバック判断基準 |
| rollback_duration | VARCHAR(50) | NULL | - | ロールバック推定所要時間 |
| requester_id | UUID | NOT NULL | - | 申請者（FK: users） |
| implementer_id | UUID | NULL | - | 実施者（FK: users） |
| related_incident_id | UUID | NULL | - | 関連インシデントID |
| related_problem_id | UUID | NULL | - | 関連問題ID |
| is_freeze_override | BOOLEAN | NOT NULL | FALSE | フリーズ期間例外許可 |
| security_review_required | BOOLEAN | NOT NULL | FALSE | セキュリティレビュー必要 |
| auto_classified_type | VARCHAR(20) | NULL | - | 自動分類結果 |
| classification_override_reason | TEXT | NULL | - | 分類上書き理由 |
| submitted_at | TIMESTAMPTZ | NULL | - | 提出日時 |
| approved_at | TIMESTAMPTZ | NULL | - | 承認日時 |
| completed_at | TIMESTAMPTZ | NULL | - | 完了日時 |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | 作成日時 |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | 更新日時 |

**status列の許容値:**

| 状態 | 説明 |
|------|------|
| draft | 下書き |
| submitted | 提出済み |
| cab_review | CAB審議中 |
| auto_approved | 自動承認（Standard） |
| approved | 承認済み |
| rejected | 却下 |
| deferred | 保留 |
| in_progress | 実施中 |
| rolling_back | ロールバック中 |
| completed | 完了 |
| rolled_back | ロールバック済み |
| pir_pending | PIR待ち |
| closed | クローズ |
| cancelled | 取消し |

**インデックス:**

| インデックス名 | カラム | 種類 |
|-------------|--------|------|
| change_requests_pkey | id | PRIMARY KEY |
| change_requests_rfc_number_unique | rfc_number | UNIQUE |
| idx_cr_status | status | INDEX |
| idx_cr_change_type | change_type | INDEX |
| idx_cr_requester_id | requester_id | INDEX |
| idx_cr_implementer_id | implementer_id | INDEX |
| idx_cr_planned_start | planned_start | INDEX |
| idx_cr_created_at | created_at | INDEX |
| idx_cr_target_systems | target_systems | GIN INDEX |

```sql
CREATE TABLE change_requests (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rfc_number          VARCHAR(20) UNIQUE NOT NULL,
    title               VARCHAR(300) NOT NULL,
    description         TEXT NOT NULL,
    change_type         VARCHAR(20) NOT NULL
                        CHECK (change_type IN ('standard','normal','major','emergency')),
    priority            VARCHAR(20) NOT NULL DEFAULT 'medium'
                        CHECK (priority IN ('low','medium','high','critical')),
    status              VARCHAR(30) NOT NULL DEFAULT 'draft'
                        CHECK (status IN ('draft','submitted','cab_review','auto_approved',
                            'approved','rejected','deferred','in_progress','rolling_back',
                            'completed','rolled_back','pir_pending','closed','cancelled')),
    target_systems      VARCHAR(100)[] NOT NULL,
    target_ci_ids       UUID[],
    affected_users      INTEGER,
    planned_start       TIMESTAMPTZ NOT NULL,
    planned_end         TIMESTAMPTZ NOT NULL,
    actual_start        TIMESTAMPTZ,
    actual_end          TIMESTAMPTZ,
    business_impact     TEXT NOT NULL,
    technical_risk      VARCHAR(20) NOT NULL
                        CHECK (technical_risk IN ('low','medium','high','critical')),
    risk_assessment     TEXT NOT NULL,
    risk_score          INTEGER,
    rollback_plan       TEXT NOT NULL,
    rollback_trigger    VARCHAR(200),
    rollback_duration   VARCHAR(50),
    requester_id        UUID NOT NULL REFERENCES users(id),
    implementer_id      UUID REFERENCES users(id),
    related_incident_id UUID,
    related_problem_id  UUID,
    is_freeze_override  BOOLEAN NOT NULL DEFAULT FALSE,
    security_review_required BOOLEAN NOT NULL DEFAULT FALSE,
    auto_classified_type VARCHAR(20),
    classification_override_reason TEXT,
    submitted_at        TIMESTAMPTZ,
    approved_at         TIMESTAMPTZ,
    completed_at        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_planned_dates CHECK (planned_end > planned_start)
);

CREATE INDEX idx_cr_status ON change_requests(status);
CREATE INDEX idx_cr_change_type ON change_requests(change_type);
CREATE INDEX idx_cr_requester_id ON change_requests(requester_id);
CREATE INDEX idx_cr_planned_start ON change_requests(planned_start);
CREATE INDEX idx_cr_target_systems ON change_requests USING GIN(target_systems);
```

---

### 2.3 cab_sessions（CABセッション）テーブル

| カラム名 | データ型 | NULL | デフォルト | 説明 |
|---------|---------|------|----------|------|
| id | UUID | NOT NULL | gen_random_uuid() | 主キー |
| session_number | VARCHAR(20) | NOT NULL | - | セッション番号（CAB-YYYY-NNN） |
| session_type | VARCHAR(20) | NOT NULL | 'regular' | regular/emergency/special |
| scheduled_date | TIMESTAMPTZ | NOT NULL | - | 予定日時 |
| scheduled_end | TIMESTAMPTZ | NOT NULL | - | 予定終了日時 |
| actual_start | TIMESTAMPTZ | NULL | - | 実績開始日時 |
| actual_end | TIMESTAMPTZ | NULL | - | 実績終了日時 |
| status | VARCHAR(20) | NOT NULL | 'scheduled' | scheduled/in_session/completed/cancelled |
| chair_id | UUID | NOT NULL | - | 議長（FK: users） |
| attendees | UUID[] | NULL | - | 出席者ID配列 |
| absentees | UUID[] | NULL | - | 欠席者ID配列 |
| agenda_notes | TEXT | NULL | - | 議題補足 |
| minutes | TEXT | NULL | - | 議事録テキスト |
| minutes_pdf_path | VARCHAR(500) | NULL | - | 議事録PDF保存パス |
| action_items | JSONB | NULL | - | アクションアイテム |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | 作成日時 |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | 更新日時 |

```sql
CREATE TABLE cab_sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_number  VARCHAR(20) UNIQUE NOT NULL,
    session_type    VARCHAR(20) NOT NULL DEFAULT 'regular'
                    CHECK (session_type IN ('regular','emergency','special')),
    scheduled_date  TIMESTAMPTZ NOT NULL,
    scheduled_end   TIMESTAMPTZ NOT NULL,
    actual_start    TIMESTAMPTZ,
    actual_end      TIMESTAMPTZ,
    status          VARCHAR(20) NOT NULL DEFAULT 'scheduled'
                    CHECK (status IN ('scheduled','in_session','completed','cancelled')),
    chair_id        UUID NOT NULL REFERENCES users(id),
    attendees       UUID[],
    absentees       UUID[],
    agenda_notes    TEXT,
    minutes         TEXT,
    minutes_pdf_path VARCHAR(500),
    action_items    JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

### 2.4 cab_decisions（CAB審議決定）テーブル

| カラム名 | データ型 | NULL | デフォルト | 説明 |
|---------|---------|------|----------|------|
| id | UUID | NOT NULL | gen_random_uuid() | 主キー |
| rfc_id | UUID | NOT NULL | - | 対象RFC（FK: change_requests） |
| session_id | UUID | NULL | - | CABセッション（FK: cab_sessions） |
| decision | VARCHAR(20) | NULL | - | approved/rejected/deferred/more_info |
| decision_reason | TEXT | NULL | - | 決定理由 |
| conditions | TEXT | NULL | - | 条件付き承認の条件 |
| approved_count | SMALLINT | NOT NULL | 0 | 承認票数 |
| rejected_count | SMALLINT | NOT NULL | 0 | 却下票数 |
| decided_at | TIMESTAMPTZ | NULL | - | 決定日時 |
| decided_by | UUID | NULL | - | 決定者（FK: users） |
| approval_deadline | TIMESTAMPTZ | NULL | - | 承認期限 |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | 作成日時 |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | 更新日時 |

```sql
CREATE TABLE cab_decisions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rfc_id          UUID NOT NULL REFERENCES change_requests(id),
    session_id      UUID REFERENCES cab_sessions(id),
    decision        VARCHAR(20)
                    CHECK (decision IN ('approved','rejected','deferred','more_info')),
    decision_reason TEXT,
    conditions      TEXT,
    approved_count  SMALLINT NOT NULL DEFAULT 0,
    rejected_count  SMALLINT NOT NULL DEFAULT 0,
    decided_at      TIMESTAMPTZ,
    decided_by      UUID REFERENCES users(id),
    approval_deadline TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_cd_rfc_id ON cab_decisions(rfc_id);
CREATE INDEX idx_cd_session_id ON cab_decisions(session_id);
```

---

### 2.5 cab_votes（CAB投票）テーブル

| カラム名 | データ型 | NULL | デフォルト | 説明 |
|---------|---------|------|----------|------|
| id | UUID | NOT NULL | gen_random_uuid() | 主キー |
| decision_id | UUID | NOT NULL | - | CAB決定（FK: cab_decisions） |
| voter_id | UUID | NOT NULL | - | 投票者（FK: users） |
| vote | VARCHAR(20) | NOT NULL | - | approve/reject/defer/abstain |
| comment | TEXT | NULL | - | コメント |
| voted_at | TIMESTAMPTZ | NOT NULL | NOW() | 投票日時 |

```sql
CREATE TABLE cab_votes (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_id UUID NOT NULL REFERENCES cab_decisions(id),
    voter_id    UUID NOT NULL REFERENCES users(id),
    vote        VARCHAR(20) NOT NULL
                CHECK (vote IN ('approve','reject','defer','abstain')),
    comment     TEXT,
    voted_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(decision_id, voter_id)
);
```

---

### 2.6 execution_records（変更実施記録）テーブル

| カラム名 | データ型 | NULL | デフォルト | 説明 |
|---------|---------|------|----------|------|
| id | UUID | NOT NULL | gen_random_uuid() | 主キー |
| rfc_id | UUID | NOT NULL | - | 対象RFC（FK: change_requests） |
| implementer_id | UUID | NOT NULL | - | 実施者（FK: users） |
| actual_start | TIMESTAMPTZ | NOT NULL | - | 実績開始日時 |
| actual_end | TIMESTAMPTZ | NULL | - | 実績終了日時 |
| result | VARCHAR(20) | NULL | - | success/partial_success/failed/rolled_back |
| details | TEXT | NULL | - | 実施内容詳細 |
| deviation_notes | TEXT | NULL | - | 計画からの逸脱事項 |
| rollback_reason | TEXT | NULL | - | ロールバック理由 |
| rollback_start | TIMESTAMPTZ | NULL | - | ロールバック開始日時 |
| rollback_end | TIMESTAMPTZ | NULL | - | ロールバック完了日時 |
| attachments | JSONB | NULL | - | 添付ファイル情報 |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | 作成日時 |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | 更新日時 |

```sql
CREATE TABLE execution_records (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rfc_id          UUID NOT NULL REFERENCES change_requests(id),
    implementer_id  UUID NOT NULL REFERENCES users(id),
    actual_start    TIMESTAMPTZ NOT NULL,
    actual_end      TIMESTAMPTZ,
    result          VARCHAR(20)
                    CHECK (result IN ('success','partial_success','failed','rolled_back')),
    details         TEXT,
    deviation_notes TEXT,
    rollback_reason TEXT,
    rollback_start  TIMESTAMPTZ,
    rollback_end    TIMESTAMPTZ,
    attachments     JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_er_rfc_id ON execution_records(rfc_id);
```

---

### 2.7 checklists（チェックリスト）テーブル

| カラム名 | データ型 | NULL | デフォルト | 説明 |
|---------|---------|------|----------|------|
| id | UUID | NOT NULL | gen_random_uuid() | 主キー |
| rfc_id | UUID | NOT NULL | - | 対象RFC（FK: change_requests） |
| phase | VARCHAR(20) | NOT NULL | - | pre/during/post |
| items | JSONB | NOT NULL | - | チェック項目配列 |
| completed_by | UUID | NULL | - | 完了者（FK: users） |
| completed_at | TIMESTAMPTZ | NULL | - | 完了日時 |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | 作成日時 |

**items JSONB構造:**
```json
[
  {
    "id": "chk-001",
    "label": "CAB承認確認",
    "required": true,
    "checked": true,
    "checked_at": "2026-04-01T21:50:00Z",
    "checked_by": "user-uuid",
    "comment": "承認済み確認"
  }
]
```

```sql
CREATE TABLE checklists (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rfc_id      UUID NOT NULL REFERENCES change_requests(id),
    phase       VARCHAR(20) NOT NULL CHECK (phase IN ('pre','during','post')),
    items       JSONB NOT NULL,
    completed_by UUID REFERENCES users(id),
    completed_at TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(rfc_id, phase)
);
```

---

### 2.8 freeze_periods（フリーズ期間）テーブル

| カラム名 | データ型 | NULL | デフォルト | 説明 |
|---------|---------|------|----------|------|
| id | UUID | NOT NULL | gen_random_uuid() | 主キー |
| name | VARCHAR(200) | NOT NULL | - | フリーズ期間名 |
| start_date | DATE | NOT NULL | - | 開始日 |
| end_date | DATE | NOT NULL | - | 終了日 |
| change_types_blocked | VARCHAR(20)[] | NOT NULL | - | ブロック対象変更種別 |
| reason | TEXT | NULL | - | 理由 |
| is_active | BOOLEAN | NOT NULL | TRUE | 有効/無効 |
| created_by | UUID | NOT NULL | - | 作成者（FK: users） |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | 作成日時 |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | 更新日時 |

```sql
CREATE TABLE freeze_periods (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                VARCHAR(200) NOT NULL,
    start_date          DATE NOT NULL,
    end_date            DATE NOT NULL,
    change_types_blocked VARCHAR(20)[] NOT NULL,
    reason              TEXT,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_by          UUID NOT NULL REFERENCES users(id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_freeze_dates CHECK (end_date >= start_date)
);
```

---

### 2.9 post_impl_reviews（事後レビュー）テーブル

| カラム名 | データ型 | NULL | デフォルト | 説明 |
|---------|---------|------|----------|------|
| id | UUID | NOT NULL | gen_random_uuid() | 主キー |
| rfc_id | UUID | NOT NULL | - | 対象RFC（FK: change_requests） |
| success_level | VARCHAR(20) | NOT NULL | - | success/partial_success/failed/rolled_back |
| variance_notes | TEXT | NULL | - | 計画と実績の差異 |
| incidents | JSONB | NULL | - | 発生インシデント |
| root_cause | TEXT | NULL | - | 根本原因分析 |
| improvements | JSONB | NULL | - | 改善事項 |
| lessons_learned | TEXT | NULL | - | レッスンラーンド |
| reviewer_id | UUID | NOT NULL | - | レビュー者（FK: users） |
| reviewed_at | TIMESTAMPTZ | NULL | - | レビュー完了日時 |
| status | VARCHAR(20) | NOT NULL | 'pending' | pending/completed |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | 作成日時 |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | 更新日時 |

**improvements JSONB構造:**
```json
[
  {
    "id": "imp-001",
    "description": "テスト環境での事前検証を必須化",
    "assignee_id": "user-uuid",
    "due_date": "2026-05-01",
    "status": "open",
    "completed_at": null
  }
]
```

```sql
CREATE TABLE post_impl_reviews (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rfc_id          UUID NOT NULL REFERENCES change_requests(id),
    success_level   VARCHAR(20) NOT NULL
                    CHECK (success_level IN ('success','partial_success','failed','rolled_back')),
    variance_notes  TEXT,
    incidents       JSONB,
    root_cause      TEXT,
    improvements    JSONB,
    lessons_learned TEXT,
    reviewer_id     UUID NOT NULL REFERENCES users(id),
    reviewed_at     TIMESTAMPTZ,
    status          VARCHAR(20) NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending','completed')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_pir_rfc_id ON post_impl_reviews(rfc_id);
```

---

### 2.10 rfc_comments（RFCコメント）テーブル

```sql
CREATE TABLE rfc_comments (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rfc_id      UUID NOT NULL REFERENCES change_requests(id),
    author_id   UUID NOT NULL REFERENCES users(id),
    content     TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_rc_rfc_id ON rfc_comments(rfc_id);
```

---

### 2.11 rfc_attachments（RFC添付ファイル）テーブル

```sql
CREATE TABLE rfc_attachments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rfc_id          UUID NOT NULL REFERENCES change_requests(id),
    file_name       VARCHAR(255) NOT NULL,
    file_path       VARCHAR(500) NOT NULL,
    file_size       BIGINT NOT NULL,
    mime_type       VARCHAR(100) NOT NULL,
    uploaded_by     UUID NOT NULL REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ra_rfc_id ON rfc_attachments(rfc_id);
```

---

### 2.12 audit_logs（監査ログ）テーブル

| カラム名 | データ型 | NULL | デフォルト | 説明 |
|---------|---------|------|----------|------|
| id | UUID | NOT NULL | gen_random_uuid() | 主キー |
| user_id | UUID | NULL | - | 操作ユーザ（FK: users） |
| action | VARCHAR(50) | NOT NULL | - | CREATE/UPDATE/DELETE/LOGIN/LOGOUT/APPROVE/REJECT |
| entity_type | VARCHAR(50) | NOT NULL | - | テーブル名 |
| entity_id | UUID | NULL | - | 対象レコードID |
| old_values | JSONB | NULL | - | 変更前の値 |
| new_values | JSONB | NULL | - | 変更後の値 |
| ip_address | INET | NULL | - | IPアドレス |
| user_agent | VARCHAR(500) | NULL | - | ユーザエージェント |
| request_id | VARCHAR(50) | NULL | - | リクエスト相関ID |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | 作成日時 |

```sql
CREATE TABLE audit_logs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID REFERENCES users(id),
    action      VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id   UUID,
    old_values  JSONB,
    new_values  JSONB,
    ip_address  INET,
    user_agent  VARCHAR(500),
    request_id  VARCHAR(50),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_al_user_id ON audit_logs(user_id);
CREATE INDEX idx_al_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_al_action ON audit_logs(action);
CREATE INDEX idx_al_created_at ON audit_logs(created_at);
```

---

### 2.13 notifications（通知）テーブル

```sql
CREATE TABLE notifications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recipient_id    UUID NOT NULL REFERENCES users(id),
    rfc_id          UUID REFERENCES change_requests(id),
    type            VARCHAR(50) NOT NULL,
    channel         VARCHAR(20) NOT NULL CHECK (channel IN ('email','teams','in_app')),
    subject         VARCHAR(300) NOT NULL,
    body            TEXT NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending','sent','failed','cancelled')),
    error_message   TEXT,
    sent_at         TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_notif_recipient ON notifications(recipient_id);
CREATE INDEX idx_notif_rfc ON notifications(rfc_id);
CREATE INDEX idx_notif_status ON notifications(status);
```

---

### 2.14 standard_change_templates（標準変更テンプレート）テーブル

```sql
CREATE TABLE standard_change_templates (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(200) NOT NULL,
    description     TEXT NOT NULL,
    target_systems  VARCHAR(100)[] NOT NULL,
    max_affected_users INTEGER NOT NULL DEFAULT 10,
    checklist_items JSONB,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_by      UUID NOT NULL REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

### 2.15 system_settings（システム設定）テーブル

```sql
CREATE TABLE system_settings (
    key         VARCHAR(100) PRIMARY KEY,
    value       JSONB NOT NULL,
    description VARCHAR(300),
    updated_by  UUID REFERENCES users(id),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## 3. 共通トリガー

### 3.1 updated_at自動更新トリガー

```sql
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 各テーブルに適用
CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_change_requests_updated_at
    BEFORE UPDATE ON change_requests
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- 以下、全テーブルに同様に適用
```

---

## 4. テーブル関連図サマリ

| テーブル | 件数想定(年間) | 主要関連 |
|---------|-------------|---------|
| users | 50件 | 全テーブル |
| change_requests | 500件 | cab_decisions, execution_records, post_impl_reviews |
| cab_sessions | 52件（週次） | cab_decisions |
| cab_decisions | 500件 | cab_votes, change_requests |
| cab_votes | 1500件 | cab_decisions, users |
| execution_records | 500件 | change_requests |
| checklists | 1500件 | change_requests |
| freeze_periods | 10件 | - |
| post_impl_reviews | 100件 | change_requests |
| rfc_comments | 2000件 | change_requests |
| rfc_attachments | 500件 | change_requests |
| audit_logs | 50000件 | users |
| notifications | 10000件 | users, change_requests |
| standard_change_templates | 20件 | - |
| system_settings | 30件 | - |

---

*文書管理：本文書はバージョン管理対象。変更履歴はGitリポジトリで管理する。*
