# システム設計書
## IT変更管理・リリース自動化プラットフォーム（IT-Change-CAB-Platform）

| 項目 | 内容 |
|------|------|
| **文書番号** | DES-SYS-001 |
| **バージョン** | 1.0.0 |
| **作成日** | 2026-03-26 |
| **作成者** | みらい建設工業 IT部門 |
| **承認者** | IT部門長 |
| **対象リポジトリ** | Kensan196948G/IT-Change-CAB-Platform |

---

## 1. 設計方針

### 1.1 基本方針

| 方針 | 説明 |
|------|------|
| レイヤードアーキテクチャ | プレゼンテーション層・ビジネスロジック層・データアクセス層の明確な分離 |
| ドメイン駆動設計（DDD） | 変更管理ドメインのモデル化、境界づけられたコンテキストの定義 |
| イベント駆動 | BullMQによる非同期処理、ワークフロー状態遷移のイベントベース管理 |
| API First | OpenAPI 3.0準拠のREST API設計を先行 |
| セキュリティバイデザイン | 認証・認可・監査ログを設計段階から組み込み |
| テスタビリティ | 依存性注入（DI）による単体テスト容易性の確保 |

### 1.2 設計原則

| 原則 | 適用箇所 |
|------|---------|
| 単一責任の原則（SRP） | 各サービスクラスは1つの責務のみ |
| 開放/閉鎖原則（OCP） | 通知チャネル・ワークフローの拡張可能性 |
| 依存性逆転の原則（DIP） | リポジトリパターンによるデータアクセス抽象化 |
| インターフェース分離（ISP） | 外部連携のAdapter Pattern |

---

## 2. レイヤードアーキテクチャ

### 2.1 全体レイヤー構成

```
┌──────────────────────────────────────────────────────┐
│               プレゼンテーション層                       │
│   React 18 / TypeScript / Ant Design / FullCalendar   │
│   SPA（Single Page Application）                      │
├──────────────────────────────────────────────────────┤
│                    API Gateway層                      │
│   Express Router / 認証ミドルウェア / レート制限         │
│   CORS / バリデーション / エラーハンドリング              │
├──────────────────────────────────────────────────────┤
│               ビジネスロジック層（Service層）             │
│   RFC管理 / CAB承認ワークフロー / 影響分析               │
│   衝突検知 / 通知 / フリーズ期間管理                     │
├──────────────────────────────────────────────────────┤
│              データアクセス層（Repository層）             │
│   Knex.js Query Builder / PostgreSQL                  │
│   Redis Cache / BullMQ Job Queue                      │
├──────────────────────────────────────────────────────┤
│                 インフラストラクチャ層                    │
│   PostgreSQL / Redis / ファイルストレージ               │
│   外部API（Teams/ITSM/GitHub）                        │
└──────────────────────────────────────────────────────┘
```

### 2.2 各レイヤーの責務

| レイヤー | 責務 | 主要技術 |
|---------|------|---------|
| プレゼンテーション層 | ユーザインターフェース、入力バリデーション、状態管理 | React 18, TypeScript, Ant Design, Zustand |
| API Gateway層 | ルーティング、認証・認可、レート制限、リクエストバリデーション | Express, express-validator, Passport.js |
| ビジネスロジック層 | ドメインロジック、ワークフロー管理、ビジネスルール | TypeScript Service Classes |
| データアクセス層 | データ永続化、キャッシュ、クエリ最適化 | Knex.js, Redis, BullMQ |
| インフラストラクチャ層 | データベース、メッセージキュー、外部API接続 | PostgreSQL, Redis, HTTP Client |

---

## 3. モジュール分割

### 3.1 バックエンドモジュール構成

```
backend/src/
├── api/                        # API Gateway層
│   ├── routes/                 # Express Router定義
│   │   ├── rfc.routes.ts       # RFC管理エンドポイント
│   │   ├── cab.routes.ts       # CAB管理エンドポイント
│   │   ├── execution.routes.ts # 変更実施エンドポイント
│   │   ├── review.routes.ts    # PIRエンドポイント
│   │   ├── calendar.routes.ts  # カレンダーエンドポイント
│   │   ├── report.routes.ts    # レポートエンドポイント
│   │   ├── admin.routes.ts     # 管理エンドポイント
│   │   └── auth.routes.ts      # 認証エンドポイント
│   ├── middleware/             # ミドルウェア
│   │   ├── auth.middleware.ts  # JWT認証
│   │   ├── rbac.middleware.ts  # ロールベースアクセス制御
│   │   ├── validator.middleware.ts # リクエストバリデーション
│   │   ├── rateLimit.middleware.ts # レート制限
│   │   ├── audit.middleware.ts # 監査ログ記録
│   │   └── error.middleware.ts # エラーハンドリング
│   └── validators/            # バリデーションスキーマ
│       ├── rfc.validator.ts
│       ├── cab.validator.ts
│       └── execution.validator.ts
│
├── services/                   # ビジネスロジック層
│   ├── rfc.service.ts          # RFC管理サービス
│   ├── cab.service.ts          # CAB管理サービス
│   ├── execution.service.ts    # 変更実施サービス
│   ├── review.service.ts       # PIRサービス
│   ├── impact-analyzer.ts      # 影響分析エンジン
│   ├── conflict-detector.ts    # 変更衝突検知
│   ├── approval-workflow.ts    # 承認ワークフロー
│   ├── notification.service.ts # 通知サービス
│   ├── calendar.service.ts     # カレンダーサービス
│   ├── kpi.service.ts          # KPI集計サービス
│   ├── freeze-period.service.ts # フリーズ期間管理
│   ├── checklist.service.ts    # チェックリスト管理
│   └── audit.service.ts        # 監査ログサービス
│
├── repositories/               # データアクセス層
│   ├── rfc.repository.ts       # RFC CRUD
│   ├── cab.repository.ts       # CAB CRUD
│   ├── execution.repository.ts # 実施記録 CRUD
│   ├── review.repository.ts    # PIR CRUD
│   ├── user.repository.ts      # ユーザ CRUD
│   ├── freeze.repository.ts    # フリーズ期間 CRUD
│   └── audit.repository.ts     # 監査ログ CRUD
│
├── models/                     # ドメインモデル
│   ├── rfc.model.ts            # RFC型定義
│   ├── cab.model.ts            # CAB型定義
│   ├── execution.model.ts      # 実施記録型定義
│   ├── review.model.ts         # PIR型定義
│   ├── user.model.ts           # ユーザ型定義
│   └── common.model.ts         # 共通型定義
│
├── jobs/                       # 非同期ジョブ（BullMQ）
│   ├── worker.ts               # ジョブワーカーエントリ
│   ├── cab-reminder.job.ts     # CAB会議リマインダー
│   ├── notification.job.ts     # 通知送信ジョブ
│   ├── overdue-alert.job.ts    # 期限超過アラート
│   ├── freeze-check.job.ts     # フリーズ期間チェック
│   └── report-generation.job.ts # レポート生成
│
├── integrations/               # 外部連携
│   ├── teams-webhook.ts        # Microsoft Teams連携
│   ├── email-sender.ts         # メール送信
│   ├── itsm-connector.ts       # ITSM連携
│   └── github-actions.ts       # GitHub Actions連携
│
├── config/                     # 設定
│   ├── database.ts             # DB設定
│   ├── redis.ts                # Redis設定
│   ├── auth.ts                 # 認証設定
│   └── app.ts                  # アプリ設定
│
├── utils/                      # ユーティリティ
│   ├── logger.ts               # ログユーティリティ
│   ├── date.ts                 # 日付ユーティリティ
│   └── rfc-number.ts           # RFC番号生成
│
├── db/                         # データベース
│   ├── migrations/             # マイグレーション
│   └── seeds/                  # シードデータ
│
└── app.ts                      # アプリケーションエントリ
```

### 3.2 フロントエンドモジュール構成

```
frontend/src/
├── pages/                      # ページコンポーネント
│   ├── rfc/
│   │   ├── RFCList.tsx         # RFC一覧
│   │   ├── RFCCreate.tsx       # RFC起票
│   │   ├── RFCEdit.tsx         # RFC編集
│   │   └── RFCDetail.tsx       # RFC詳細
│   ├── cab/
│   │   ├── CABDashboard.tsx    # CABダッシュボード
│   │   ├── CABSession.tsx      # CAB会議管理
│   │   └── CABMinutes.tsx      # 議事録表示
│   ├── execution/
│   │   ├── ExecutionView.tsx   # 実施管理画面
│   │   └── ChecklistView.tsx   # チェックリスト
│   ├── calendar/
│   │   └── ChangeCalendar.tsx  # 変更カレンダー
│   ├── kpi/
│   │   ├── KPIDashboard.tsx    # KPIダッシュボード
│   │   └── TrendAnalysis.tsx   # トレンド分析
│   ├── admin/
│   │   ├── UserManagement.tsx  # ユーザ管理
│   │   ├── SystemSettings.tsx  # システム設定
│   │   └── AuditLog.tsx        # 監査ログ
│   └── auth/
│       ├── Login.tsx           # ログイン
│       └── Profile.tsx         # プロフィール
│
├── components/                 # 共通コンポーネント
│   ├── layout/
│   │   ├── AppLayout.tsx       # メインレイアウト
│   │   ├── Sidebar.tsx         # サイドバー
│   │   └── Header.tsx          # ヘッダー
│   ├── rfc/
│   │   ├── RFCForm.tsx         # RFC入力フォーム
│   │   ├── ImpactAnalysis.tsx  # 影響分析表示
│   │   ├── ConflictAlert.tsx   # 衝突検知アラート
│   │   └── StatusBadge.tsx     # ステータスバッジ
│   ├── cab/
│   │   ├── ApprovalPanel.tsx   # 承認操作パネル
│   │   ├── VoteStatus.tsx      # 投票状況
│   │   └── AgendaList.tsx      # 議題一覧
│   └── common/
│       ├── DataTable.tsx       # データテーブル
│       ├── FilterBar.tsx       # フィルタバー
│       └── LoadingSpinner.tsx  # ローディング
│
├── hooks/                      # カスタムフック
│   ├── useRFC.ts               # RFC操作フック
│   ├── useCAB.ts               # CAB操作フック
│   ├── useAuth.ts              # 認証フック
│   └── useNotification.ts     # 通知フック
│
├── stores/                     # 状態管理（Zustand）
│   ├── authStore.ts            # 認証状態
│   ├── rfcStore.ts             # RFC状態
│   └── uiStore.ts              # UI状態
│
├── services/                   # APIクライアント
│   ├── api.ts                  # Axios設定
│   ├── rfc.api.ts              # RFC API
│   ├── cab.api.ts              # CAB API
│   └── auth.api.ts             # 認証API
│
├── types/                      # 型定義
│   ├── rfc.types.ts
│   ├── cab.types.ts
│   └── common.types.ts
│
└── utils/                      # ユーティリティ
    ├── constants.ts
    ├── formatters.ts
    └── validators.ts
```

---

## 4. 状態遷移設計

### 4.1 RFC状態遷移図

```
                    ┌──────────────────────────────────┐
                    │                                  │
                    ▼                                  │
┌───────┐   提出   ┌──────────┐   Standard変更    ┌──────────────┐
│ draft │────────>│ submitted │───────────────>│ auto_approved │
│（下書き）│        │（提出済み） │                 │（自動承認済み） │
└───┬───┘         └─────┬────┘                 └──────┬───────┘
    │                   │                            │
    │ 取消し            │ Normal/Major/Emergency      │
    ▼                   ▼                            │
┌──────────┐    ┌────────────┐                      │
│ cancelled │    │ cab_review  │◄─────────────────────┘
│（取消し）  │    │（CAB審議中）│     ※auto_approvedの
└──────────┘    └──┬──┬──┬──┘      場合はスキップ
                   │  │  │
          承認     │  │  │ 却下        差戻し/保留
      ┌───────────┘  │  └──────────┐  ┌──────────┐
      ▼              │             ▼  │          │
┌──────────┐    追加情報要求   ┌──────────┐         │
│ approved  │         │       │ rejected  │         │
│（承認済み）│         │       │（却下）    │         │
└────┬─────┘         │       └──────────┘         │
     │                │                            │
     │ 実施開始        └──> deferred（保留）         │
     ▼                     └──> draft（差戻し）──────┘
┌──────────────┐
│ in_progress   │
│（実施中）      │
└──┬─────┬─────┘
   │     │
   │     │ ロールバック開始
   │     ▼
   │  ┌──────────────┐
   │  │ rolling_back  │
   │  │（ロールバック中）│
   │  └──────┬───────┘
   │         │
   │ 完了    │ ロールバック完了
   ▼         ▼
┌──────────┐  ┌──────────────┐
│ completed │  │ rolled_back   │
│（完了）    │  │（ロールバック）│
└──────────┘  └──────────────┘
      │              │
      └──────┬───────┘
             │
             ▼ PIR発行（自動/手動）
      ┌──────────────┐
      │ pir_pending   │
      │（PIR待ち）     │
      └──────┬───────┘
             │
             │ PIR完了
             ▼
      ┌──────────────┐
      │ closed        │
      │（クローズ）    │
      └──────────────┘
```

### 4.2 状態遷移マトリクス

| 現在の状態 | 遷移先状態 | トリガー | 条件 |
|-----------|----------|---------|------|
| draft | submitted | 提出操作 | 全必須項目入力済み、BLOCKING衝突なし |
| draft | cancelled | 取消し操作 | 取消し理由入力 |
| submitted | auto_approved | 自動判定 | Standard変更の場合 |
| submitted | cab_review | 自動判定 | Normal/Major/Emergency変更の場合 |
| cab_review | approved | 承認条件達成 | 必要承認人数・必須承認者の条件充足 |
| cab_review | rejected | 却下投票 | CAB議長の却下または多数却下 |
| cab_review | deferred | 保留決定 | 追加情報要求 |
| cab_review | draft | 差戻し | 修正要求 |
| approved | in_progress | 実施開始 | 実施前チェックリスト完了 |
| auto_approved | in_progress | 実施開始 | 実施前チェックリスト完了 |
| in_progress | completed | 実施完了 | 実施後チェックリスト完了 |
| in_progress | rolling_back | ロールバック開始 | ロールバック理由入力 |
| rolling_back | rolled_back | ロールバック完了 | ロールバック記録完了 |
| completed | pir_pending | PIR発行 | 自動（Major/Emergency/ロールバック） |
| rolled_back | pir_pending | PIR発行 | 自動（常時） |
| pir_pending | closed | PIR完了 | PIR記録完了 |

### 4.3 CABセッション状態遷移

| 状態 | 説明 | 遷移先 |
|------|------|--------|
| scheduled | スケジュール済み | in_session, cancelled |
| in_session | 会議中 | completed |
| completed | 完了 | - |
| cancelled | キャンセル | - |

---

## 5. 通知設計

### 5.1 通知イベントマトリクス

| イベント | 通知先 | チャネル | テンプレート |
|---------|--------|---------|------------|
| RFC提出 | CABメンバー | メール, Teams | CAB_REVIEW_REQUIRED |
| RFC承認 | 申請者, 実施者 | メール, Teams | RFC_APPROVED |
| RFC却下 | 申請者 | メール, Teams | RFC_REJECTED |
| RFC差戻し | 申請者 | メール | RFC_RETURNED |
| CAB会議招集 | CABメンバー | メール, Teams | CAB_MEETING_SCHEDULED |
| CABリマインダー | CABメンバー | メール, Teams | CAB_REMINDER |
| 実施開始 | 関係者 | メール, Teams | EXECUTION_STARTED |
| 実施完了 | 関係者 | メール, Teams | EXECUTION_COMPLETED |
| ロールバック開始 | 全関係者 | メール, Teams | ROLLBACK_STARTED |
| フリーズ期間警告 | 申請者 | メール | FREEZE_PERIOD_WARNING |
| 承認期限超過 | CAB議長 | メール, Teams | APPROVAL_OVERDUE |
| PIR発行 | 実施者 | メール | PIR_REQUIRED |

### 5.2 通知優先度

| 優先度 | 送信方法 | 対象イベント |
|--------|---------|------------|
| 緊急 | メール + Teams即時 | ロールバック開始、ECAB承認依頼 |
| 高 | メール + Teams | RFC承認/却下、実施開始/完了 |
| 中 | メール | CAB招集、リマインダー、PIR発行 |
| 低 | メールダイジェスト | 情報通知、コメント追加 |

---

## 6. エラーハンドリング設計

### 6.1 エラー分類

| エラーコード | 分類 | HTTP Status | 説明 |
|------------|------|-------------|------|
| ERR_VALIDATION | バリデーション | 400 | 入力値不正 |
| ERR_AUTH | 認証 | 401 | 認証失敗 |
| ERR_FORBIDDEN | 認可 | 403 | 権限不足 |
| ERR_NOT_FOUND | リソース | 404 | リソース未存在 |
| ERR_CONFLICT | 競合 | 409 | データ競合（楽観的ロック） |
| ERR_STATE | 状態遷移 | 422 | 許可されない状態遷移 |
| ERR_FREEZE | フリーズ | 422 | フリーズ期間中の変更 |
| ERR_INTERNAL | 内部 | 500 | 内部エラー |
| ERR_EXTERNAL | 外部連携 | 502 | 外部API呼び出し失敗 |

### 6.2 エラーレスポンス形式

```json
{
  "error": {
    "code": "ERR_VALIDATION",
    "message": "入力値が不正です",
    "details": [
      {
        "field": "planned_start",
        "message": "計画開始日時は現在日時より後の日時を指定してください"
      }
    ],
    "timestamp": "2026-03-26T10:00:00Z",
    "requestId": "req_abc123"
  }
}
```

---

## 7. キャッシュ設計

### 7.1 キャッシュ戦略

| データ | キャッシュ先 | TTL | 無効化条件 |
|--------|-----------|-----|-----------|
| ユーザ情報 | Redis | 30分 | ユーザ更新時 |
| システム一覧 | Redis | 1時間 | 設定変更時 |
| フリーズ期間 | Redis | 15分 | フリーズ期間変更時 |
| 依存関係マップ | メモリ | アプリ起動時 | 設定変更時に再読み込み |
| KPI集計結果 | Redis | 5分 | 変更完了時 |
| RFC一覧（ページネーション） | Redis | 1分 | RFC変更時 |

---

## 8. ジョブキュー設計（BullMQ）

### 8.1 キュー定義

| キュー名 | 用途 | 優先度 | リトライ回数 | タイムアウト |
|---------|------|--------|------------|-----------|
| notification | 通知送信 | 高 | 3回 | 30秒 |
| cab-reminder | CABリマインダー | 中 | 2回 | 60秒 |
| report-generation | レポート生成 | 低 | 2回 | 120秒 |
| overdue-alert | 期限超過アラート | 中 | 3回 | 30秒 |
| freeze-check | フリーズ期間チェック | 中 | 2回 | 30秒 |
| audit-log | 監査ログ書き込み | 高 | 5回 | 10秒 |

### 8.2 定期ジョブスケジュール

| ジョブ | スケジュール | 説明 |
|--------|-----------|------|
| CAB会議リマインダー | 毎営業日 9:00 | 翌日CAB会議のリマインダー送信 |
| 承認期限チェック | 毎時 | 承認期限超過RFCの検知・アラート |
| フリーズ期間チェック | 毎日 0:00 | フリーズ期間開始/終了の通知 |
| KPI再集計 | 毎日 1:00 | 日次KPIの再集計 |
| 古いセッションクリーンアップ | 毎日 3:00 | 期限切れセッションの削除 |

---

*文書管理：本文書はバージョン管理対象。変更履歴はGitリポジトリで管理する。*
