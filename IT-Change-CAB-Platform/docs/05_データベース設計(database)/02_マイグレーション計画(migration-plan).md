# マイグレーション計画書
## IT変更管理・リリース自動化プラットフォーム（IT-Change-CAB-Platform）

| 項目 | 内容 |
|------|------|
| **文書番号** | DB-MIG-001 |
| **バージョン** | 1.0.0 |
| **作成日** | 2026-03-26 |
| **作成者** | みらい建設工業 IT部門 |
| **承認者** | IT部門長 |
| **対象リポジトリ** | Kensan196948G/IT-Change-CAB-Platform |

---

## 1. マイグレーション戦略

### 1.1 ツール選定

| 項目 | 内容 |
|------|------|
| マイグレーションツール | Knex.js Migrations |
| バージョニング方式 | タイムスタンプベース（YYYYMMDDHHMMSS_name.ts） |
| 実行方向 | Up（適用） / Down（ロールバック） |
| トランザクション | 各マイグレーションをトランザクション内で実行 |
| ロック機構 | Knex.jsのアドバイザリーロック（同時実行防止） |

### 1.2 バージョニングルール

| ルール | 説明 |
|--------|------|
| ファイル命名 | `YYYYMMDDHHMMSS_description.ts` |
| 説明部分 | スネークケース、英語、簡潔に変更内容を記述 |
| 例 | `20260326100000_create_users_table.ts` |
| 順序保証 | タイムスタンプ順に適用 |
| 不変性 | 一度適用したマイグレーションは修正しない |

---

## 2. マイグレーションファイル一覧

### 2.1 初期マイグレーション（Phase 1）

| 順序 | ファイル名 | 内容 | 依存 |
|------|-----------|------|------|
| 1 | 20260326100000_create_users_table.ts | usersテーブル作成 | なし |
| 2 | 20260326100100_create_change_requests_table.ts | change_requestsテーブル作成 | users |
| 3 | 20260326100200_create_cab_sessions_table.ts | cab_sessionsテーブル作成 | users |
| 4 | 20260326100300_create_cab_decisions_table.ts | cab_decisionsテーブル作成 | change_requests, cab_sessions |
| 5 | 20260326100400_create_cab_votes_table.ts | cab_votesテーブル作成 | cab_decisions, users |
| 6 | 20260326100500_create_execution_records_table.ts | execution_recordsテーブル作成 | change_requests, users |
| 7 | 20260326100600_create_checklists_table.ts | checklistsテーブル作成 | change_requests |
| 8 | 20260326100700_create_freeze_periods_table.ts | freeze_periodsテーブル作成 | users |
| 9 | 20260326100800_create_post_impl_reviews_table.ts | post_impl_reviewsテーブル作成 | change_requests, users |
| 10 | 20260326100900_create_rfc_comments_table.ts | rfc_commentsテーブル作成 | change_requests, users |
| 11 | 20260326101000_create_rfc_attachments_table.ts | rfc_attachmentsテーブル作成 | change_requests, users |
| 12 | 20260326101100_create_audit_logs_table.ts | audit_logsテーブル作成 | users |
| 13 | 20260326101200_create_notifications_table.ts | notificationsテーブル作成 | users, change_requests |
| 14 | 20260326101300_create_standard_change_templates.ts | standard_change_templatesテーブル作成 | users |
| 15 | 20260326101400_create_system_settings_table.ts | system_settingsテーブル作成 | users |
| 16 | 20260326101500_create_updated_at_trigger.ts | updated_at自動更新トリガー | 全テーブル |
| 17 | 20260326101600_create_indexes.ts | インデックス作成 | 全テーブル |
| 18 | 20260326101700_seed_initial_data.ts | 初期データ投入 | 全テーブル |

### 2.2 マイグレーションファイル例

```typescript
// 20260326100000_create_users_table.ts
import { Knex } from 'knex';

export async function up(knex: Knex): Promise<void> {
  // UUID拡張有効化
  await knex.raw('CREATE EXTENSION IF NOT EXISTS "pgcrypto"');

  await knex.schema.createTable('users', (table) => {
    table.uuid('id').primary().defaultTo(knex.raw('gen_random_uuid()'));
    table.string('username', 50).unique().notNullable();
    table.string('email', 255).unique().notNullable();
    table.string('password_hash', 255).notNullable();
    table.string('display_name', 100).notNullable();
    table.string('role', 20).notNullable().defaultTo('requester');
    table.string('department', 100);
    table.string('phone', 20);
    table.boolean('is_active').notNullable().defaultTo(true);
    table.string('mfa_secret', 255);
    table.boolean('mfa_enabled').notNullable().defaultTo(false);
    table.timestamp('last_login_at', { useTz: true });
    table.timestamp('created_at', { useTz: true }).notNullable().defaultTo(knex.fn.now());
    table.timestamp('updated_at', { useTz: true }).notNullable().defaultTo(knex.fn.now());

    // CHECK制約
    table.check(
      "role IN ('admin','cab_chair','cab_member','requester','implementer','viewer','executive')"
    );

    // インデックス
    table.index('role');
    table.index('is_active');
  });
}

export async function down(knex: Knex): Promise<void> {
  await knex.schema.dropTableIfExists('users');
}
```

---

## 3. シードデータ

### 3.1 初期シードデータ

| シード | 内容 | 件数 |
|--------|------|------|
| 管理者ユーザ | システム管理者アカウント | 1件 |
| CABメンバー | CAB議長・技術メンバー | 5件 |
| システム設定 | デフォルト設定値 | 約30件 |
| 標準変更テンプレート | 初期テンプレート | 5件 |

### 3.2 システム設定初期値

| key | value | 説明 |
|-----|-------|------|
| cab_meeting_day | "friday" | 定期CAB会議曜日 |
| cab_meeting_time | "14:00" | 定期CAB会議時刻 |
| cab_notification_days | 3 | 会議招集通知日数 |
| normal_approval_deadline_days | 5 | Normal承認期限（営業日） |
| major_approval_deadline_days | 10 | Major承認期限（営業日） |
| emergency_approval_timeout_hours | 4 | Emergency承認タイムアウト |
| normal_min_approvals | 2 | Normal最低承認人数 |
| major_min_approvals | 3 | Major最低承認人数 |
| emergency_min_approvals | 1 | Emergency最低承認人数 |
| notification_email_enabled | true | メール通知有効 |
| notification_teams_enabled | true | Teams通知有効 |
| teams_webhook_url | "" | Teams Webhook URL |
| smtp_host | "" | SMTPホスト |
| smtp_port | 587 | SMTPポート |
| session_timeout_minutes | 30 | セッションタイムアウト |
| max_upload_size_mb | 50 | 最大アップロードサイズ |
| auto_pir_major | true | Major変更PIR自動発行 |
| auto_pir_emergency | true | Emergency変更PIR自動発行 |
| auto_pir_rollback | true | ロールバック時PIR自動発行 |

---

## 4. ロールバック戦略

### 4.1 マイグレーションロールバック手順

| ステップ | コマンド | 説明 |
|---------|---------|------|
| 1 | `npx knex migrate:status` | 現在のマイグレーション状態を確認 |
| 2 | `npx knex migrate:rollback` | 最後のバッチをロールバック |
| 3 | `npx knex migrate:rollback --all` | 全マイグレーションをロールバック |
| 4 | DB確認 | ロールバック後のテーブル状態を確認 |

### 4.2 ロールバック時の注意事項

| 注意事項 | 対策 |
|---------|------|
| データ損失リスク | ロールバック前にpg_dumpでバックアップ取得必須 |
| 外部キー制約 | 依存関係の逆順でテーブル削除 |
| インデックス削除 | テーブル削除時に自動削除 |
| トリガー削除 | テーブル削除時に自動削除 |
| 本番環境 | 必ずメンテナンスウィンドウ内で実施 |

### 4.3 データマイグレーション時のロールバック

| パターン | ロールバック方法 |
|---------|--------------|
| カラム追加 | down()でカラム削除（データ損失注意） |
| カラム名変更 | down()で元の名前に戻す |
| データ変換 | down()で逆変換を実行（可逆の場合） |
| テーブル分割 | down()で元テーブルに統合 |
| 不可逆変更 | ロールバック不可。バックアップからの復元のみ |

---

## 5. 本番デプロイ手順

### 5.1 マイグレーション実行手順

| ステップ | 実行者 | コマンド/操作 | 確認事項 |
|---------|--------|-------------|---------|
| 1 | DBA | `pg_dump -F c cab_platform > backup_YYYYMMDD.dump` | バックアップ完了確認 |
| 2 | DBA | マイグレーション実行前のテーブル状態確認 | テーブル一覧・件数 |
| 3 | 開発者 | `NODE_ENV=production npx knex migrate:latest` | マイグレーション成功確認 |
| 4 | DBA | マイグレーション実行後のテーブル状態確認 | 新テーブル・カラム確認 |
| 5 | 開発者 | アプリケーション動作確認 | 主要機能の正常動作 |
| 6 | DBA | `npx knex migrate:status` | 全マイグレーション適用済み確認 |

### 5.2 失敗時の復旧手順

| ステップ | 操作 | 説明 |
|---------|------|------|
| 1 | マイグレーションロールバック | `npx knex migrate:rollback` |
| 2 | ロールバック失敗時 | バックアップからリストア `pg_restore -d cab_platform backup.dump` |
| 3 | アプリケーション巻き戻し | 前バージョンのDockerイメージにロールバック |
| 4 | 原因調査 | マイグレーションスクリプトの修正 |
| 5 | 再実行 | 修正後にマイグレーション再実行 |

---

## 6. スキーマバージョン管理

### 6.1 Knex.jsマイグレーションテーブル

Knex.jsは以下の管理テーブルを自動作成する。

| テーブル | 用途 |
|---------|------|
| knex_migrations | 適用済みマイグレーション一覧 |
| knex_migrations_lock | 同時実行防止ロック |

### 6.2 バージョンとリリースの対応

| スキーマバージョン | アプリバージョン | 主要変更 |
|----------------|--------------|---------|
| v1.0.0 | v1.0.0 | 初期スキーマ（全テーブル作成） |
| v1.1.0 | v1.1.0 | Phase 2機能追加（CMDB連携カラム等） |
| v1.2.0 | v1.2.0 | Phase 3機能追加（全文検索インデックス等） |

---

## 7. データアーカイブ計画

### 7.1 アーカイブ対象

| テーブル | アーカイブ条件 | 保持期間 | アーカイブ先 |
|---------|-------------|---------|------------|
| change_requests | closed状態 + 3年経過 | 永久 | archive_change_requests |
| audit_logs | 7年経過 | 永久 | archive_audit_logs |
| notifications | sent状態 + 1年経過 | 3年 | 削除 |
| cab_sessions | completed状態 + 5年経過 | 永久 | archive_cab_sessions |

### 7.2 アーカイブ実行

```sql
-- アーカイブテーブルへのデータ移動（例）
INSERT INTO archive_change_requests
SELECT * FROM change_requests
WHERE status = 'closed'
  AND completed_at < NOW() - INTERVAL '3 years';

DELETE FROM change_requests
WHERE status = 'closed'
  AND completed_at < NOW() - INTERVAL '3 years';
```

---

## 8. パフォーマンスチューニング計画

### 8.1 初期インデックス戦略

| テーブル | インデックス | 種類 | 目的 |
|---------|-----------|------|------|
| change_requests | status | B-tree | ステータスによるフィルタリング |
| change_requests | planned_start | B-tree | 日程による検索 |
| change_requests | target_systems | GIN | 配列検索（対象システム） |
| change_requests | (title, description) | GIN (tsvector) | 全文検索（Phase 2） |
| audit_logs | (entity_type, entity_id) | B-tree | エンティティ別操作ログ検索 |
| audit_logs | created_at | B-tree | 日時範囲検索 |
| notifications | (recipient_id, status) | B-tree | ユーザ別未読通知 |

### 8.2 パーティショニング計画（Phase 3）

| テーブル | パーティション方式 | キー |
|---------|----------------|------|
| audit_logs | RANGE | created_at（月次） |
| notifications | RANGE | created_at（月次） |
| change_requests | なし（件数が少ないため不要） |

---

*文書管理：本文書はバージョン管理対象。変更履歴はGitリポジトリで管理する。*
