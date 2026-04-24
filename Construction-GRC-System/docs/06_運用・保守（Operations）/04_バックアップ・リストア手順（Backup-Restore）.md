# バックアップ・リストア手順（Backup & Restore Procedures）

| 項目 | 内容 |
|------|------|
| 文書番号 | GRC-OPS-004 |
| バージョン | 1.0.0 |
| 作成日 | 2026-03-26 |
| 最終更新日 | 2026-03-26 |
| 作成者 | インフラチーム |
| 承認者 | システム運用責任者 |
| 分類 | 社外秘 |
| 対象プロジェクト | 建設業 統合リスク＆コンプライアンス管理システム（Construction-GRC-System） |
| 準拠規格 | ISO27001:2022 / NIST CSF 2.0 / 建設業法 / 品確法 / 労安法 |

---

## 1. 概要

### 1.1 目的

本文書は、Construction-GRC-Systemのデータバックアップおよびリストアに関する手順を定める。データの保全とシステム復旧を確実に行い、事業継続性を確保する。

### 1.2 復旧目標

| 指標 | 目標値 | 説明 |
|------|--------|------|
| RTO（Recovery Time Objective） | 4時間 | サービス復旧までの最大許容時間 |
| RPO（Recovery Point Objective） | 24時間 | 許容データ損失の最大時間幅 |

### 1.3 関連文書

| 文書番号 | 文書名 |
|---------|--------|
| GRC-OPS-001 | 運用手順書 |
| GRC-OPS-003 | 障害対応手順書 |
| GRC-OPS-005 | 保守計画 |
| GRC-REL-004 | ロールバック手順書 |

---

## 2. バックアップ設計

### 2.1 バックアップ対象一覧

| No. | 対象 | データ種別 | バックアップ方式 | 頻度 | 保持世代 |
|-----|------|-----------|----------------|------|---------|
| 1 | PostgreSQL全データ | データベース | pg_dump（論理） | 日次 | 3世代 |
| 2 | PostgreSQL WAL | トランザクションログ | WALアーカイブ | 継続的 | 7日分 |
| 3 | アップロードファイル | ファイル | rsync | 日次 | 3世代 |
| 4 | アプリケーション設定 | 設定ファイル | rsync | 変更時 | 5世代 |
| 5 | Elasticsearch インデックス | 検索データ | Snapshot API | 日次 | 3世代 |
| 6 | Redis データ | キャッシュ・セッション | RDB Snapshot | 日次 | 1世代 |
| 7 | SSL証明書・鍵 | セキュリティ | 暗号化コピー | 変更時 | 3世代 |
| 8 | 監査ログ | ログ | 圧縮アーカイブ | 日次 | 1年分 |

### 2.2 バックアップスケジュール

```
┌──────────────────────────────────────────────────┐
│              日次バックアップスケジュール            │
│                                                  │
│  01:00  Redis RDB Snapshot                       │
│  02:00  Elasticsearch Snapshot                   │
│  03:00  アップロードファイル rsync                  │
│  04:00  PostgreSQL pg_dump（フルバックアップ）      │
│  05:00  監査ログアーカイブ                         │
│  05:30  バックアップ検証（チェックサム）             │
│  06:00  古い世代の削除（3世代管理）                 │
│                                                  │
│  常時   PostgreSQL WALアーカイブ（継続的）          │
└──────────────────────────────────────────────────┘
```

### 2.3 3世代管理

| 世代 | 保持期間 | 保管場所 | 説明 |
|------|---------|---------|------|
| 第1世代（最新） | 当日分 | ローカルストレージ | 直近のバックアップ |
| 第2世代 | 前日分 | ローカルストレージ | 前日のバックアップ |
| 第3世代 | 前々日分 | リモートストレージ | 最も古い保持バックアップ |

**世代ローテーション:**

```
Day N:    backup_day_N.dump    → 第1世代
          backup_day_N-1.dump  → 第2世代
          backup_day_N-2.dump  → 第3世代
          backup_day_N-3.dump  → 削除
```

### 2.4 バックアップ保管場所

| 保管場所 | 種別 | 用途 | 暗号化 |
|---------|------|------|--------|
| /backup/local/ | ローカルディスク | 第1・第2世代保管 | AES-256 |
| s3://grc-backup/ | S3互換ストレージ | 第3世代・長期保管 | SSE-S3 + KMS |
| オフサイト | テープ/外部DC | 災害復旧用（月次） | AES-256 |

---

## 3. PostgreSQL バックアップ手順

### 3.1 日次フルバックアップ（pg_dump）

#### 3.1.1 自動実行スクリプト

```bash
#!/bin/bash
# /opt/grc-backup/scripts/pg_backup.sh
# PostgreSQL日次フルバックアップ

set -euo pipefail

# 設定
BACKUP_DIR="/backup/local/postgresql"
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/grc_db_${BACKUP_DATE}.dump"
DB_NAME="grc_db"
DB_USER="grc_backup"
DB_HOST="db-primary.grc-system.internal"
LOG_FILE="/var/log/grc-system/backup.log"
MAX_GENERATIONS=3
S3_BUCKET="s3://grc-backup/postgresql"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== PostgreSQL バックアップ開始 ==="

# バックアップディレクトリ確認
mkdir -p "$BACKUP_DIR"

# バックアップ実行
log "pg_dump実行開始: ${BACKUP_FILE}"
pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
    -Fc --compress=9 \
    --verbose \
    -f "$BACKUP_FILE" \
    2>> "$LOG_FILE"

# チェックサム生成
sha256sum "$BACKUP_FILE" > "${BACKUP_FILE}.sha256"
log "チェックサム生成完了"

# バックアップサイズ確認
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
log "バックアップサイズ: ${BACKUP_SIZE}"

# バックアップ検証
pg_restore --list "$BACKUP_FILE" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    log "バックアップ検証: OK"
else
    log "ERROR: バックアップ検証失敗"
    exit 1
fi

# 第3世代をリモートストレージに転送
THIRD_GEN=$(ls -t ${BACKUP_DIR}/grc_db_*.dump | sed -n '3p')
if [ -n "$THIRD_GEN" ]; then
    log "第3世代をS3に転送: $(basename $THIRD_GEN)"
    aws s3 cp "$THIRD_GEN" "$S3_BUCKET/" --sse aws:kms
    aws s3 cp "${THIRD_GEN}.sha256" "$S3_BUCKET/"
fi

# 世代管理（3世代を超えるものを削除）
ls -t ${BACKUP_DIR}/grc_db_*.dump | tail -n +$((MAX_GENERATIONS + 1)) | while read old_file; do
    log "古い世代を削除: $(basename $old_file)"
    rm -f "$old_file" "${old_file}.sha256"
done

log "=== PostgreSQL バックアップ完了 ==="
```

#### 3.1.2 cron設定

```cron
# /etc/cron.d/grc-backup
# PostgreSQL日次バックアップ（毎日04:00実行）
0 4 * * * grc-backup /opt/grc-backup/scripts/pg_backup.sh >> /var/log/grc-system/backup_cron.log 2>&1
```

### 3.2 WALアーカイブ（継続的バックアップ）

#### 3.2.1 PostgreSQL設定

```ini
# postgresql.conf
wal_level = replica
archive_mode = on
archive_command = 'test ! -f /backup/local/wal/%f && cp %p /backup/local/wal/%f'
archive_timeout = 300  # 5分間隔でWAL強制切り替え
```

#### 3.2.2 WALクリーンアップ

```bash
#!/bin/bash
# 7日以上古いWALファイルを削除
find /backup/local/wal/ -name "*.wal" -mtime +7 -delete
```

### 3.3 バックアップ確認手順

```bash
# バックアップファイル一覧確認
ls -lah /backup/local/postgresql/grc_db_*.dump

# チェックサム検証
sha256sum -c /backup/local/postgresql/grc_db_*.sha256

# バックアップ内容確認
pg_restore --list /backup/local/postgresql/grc_db_YYYYMMDD_HHMMSS.dump | head -30

# S3上のバックアップ確認
aws s3 ls s3://grc-backup/postgresql/
```

---

## 4. リストア手順

### 4.1 リストア判断基準

| 状況 | リストア方式 | 目安時間 |
|------|------------|---------|
| テーブル単位の誤削除 | 特定テーブルのリストア | 30分-1時間 |
| データ不整合 | ポイントインタイムリカバリ（PITR） | 1-2時間 |
| データベース全体の破損 | フルリストア | 2-4時間 |
| サーバー障害 | 新規サーバーでのフルリストア | 3-4時間 |

### 4.2 フルリストア手順

#### 4.2.1 事前準備

```bash
# 1. 現在のデータベースの状態確認
psql -U postgres -c "SELECT pg_database_size('grc_db');"
psql -U postgres -c "SELECT count(*) FROM pg_stat_activity WHERE datname='grc_db';"

# 2. アプリケーション停止
sudo systemctl stop grc-application
sudo systemctl stop celery-worker
sudo systemctl stop celery-beat

# 3. リストア対象バックアップの選択・検証
ls -lah /backup/local/postgresql/grc_db_*.dump
sha256sum -c /backup/local/postgresql/grc_db_YYYYMMDD_HHMMSS.sha256
```

#### 4.2.2 リストア実行

```bash
# 4. 既存データベースの削除と再作成
psql -U postgres -c "DROP DATABASE IF EXISTS grc_db;"
psql -U postgres -c "CREATE DATABASE grc_db OWNER grc_admin;"

# 5. リストア実行
pg_restore -h localhost -U postgres -d grc_db \
    --verbose --clean --if-exists \
    /backup/local/postgresql/grc_db_YYYYMMDD_HHMMSS.dump \
    2>&1 | tee /var/log/grc-system/restore.log

# 6. 権限の再設定
psql -U postgres -d grc_db -c "
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO grc_admin;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO grc_readonly;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO grc_admin;
"
```

#### 4.2.3 リストア後の確認

```bash
# 7. データ整合性確認
psql -U grc_admin -d grc_db -c "
SELECT schemaname, tablename, n_live_tup
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;"

# 8. アプリケーションマイグレーション確認
python manage.py showmigrations

# 9. アプリケーション起動
sudo systemctl start grc-application
sudo systemctl start celery-worker
sudo systemctl start celery-beat

# 10. ヘルスチェック
curl -s http://localhost:8000/health/deep/ | python -m json.tool

# 11. 主要機能の動作確認
python manage.py check --deploy
```

### 4.3 特定テーブルリストア

```bash
# 特定テーブルのみリストア（例: risk_assessments テーブル）
pg_restore -h localhost -U postgres -d grc_db \
    --table=risk_assessments \
    --verbose \
    /backup/local/postgresql/grc_db_YYYYMMDD_HHMMSS.dump
```

### 4.4 ポイントインタイムリカバリ（PITR）

```bash
# 1. アプリケーション停止
sudo systemctl stop grc-application

# 2. PostgreSQL停止
sudo systemctl stop postgresql

# 3. データディレクトリのバックアップ
mv /var/lib/postgresql/16/main /var/lib/postgresql/16/main_broken

# 4. ベースバックアップからのリストア
pg_basebackup -h db-primary -U replication -D /var/lib/postgresql/16/main -P

# 5. recovery.signal の作成
touch /var/lib/postgresql/16/main/recovery.signal

# 6. postgresql.conf にリカバリターゲットを設定
cat >> /var/lib/postgresql/16/main/postgresql.conf << EOF
restore_command = 'cp /backup/local/wal/%f %p'
recovery_target_time = '2026-03-26 10:00:00+09'
recovery_target_action = 'promote'
EOF

# 7. PostgreSQL起動（リカバリ自動実行）
sudo systemctl start postgresql

# 8. リカバリ完了確認
psql -U postgres -c "SELECT pg_is_in_recovery();"
# false が返ればリカバリ完了
```

---

## 5. その他のバックアップ・リストア

### 5.1 アップロードファイル

```bash
# バックアップ
rsync -avz --delete \
    /var/grc-system/uploads/ \
    /backup/local/uploads/$(date +%Y%m%d)/

# リストア
rsync -avz \
    /backup/local/uploads/YYYYMMDD/ \
    /var/grc-system/uploads/
```

### 5.2 Elasticsearch

```bash
# スナップショット作成
curl -X PUT "localhost:9200/_snapshot/grc_backup/snapshot_$(date +%Y%m%d)" \
    -H 'Content-Type: application/json' \
    -d '{"indices": "grc-*", "ignore_unavailable": true}'

# スナップショットからリストア
curl -X POST "localhost:9200/_snapshot/grc_backup/snapshot_YYYYMMDD/_restore" \
    -H 'Content-Type: application/json' \
    -d '{"indices": "grc-*"}'
```

### 5.3 Redis

```bash
# RDBスナップショット（自動: redis.conf で設定済み）
# 手動バックアップ
redis-cli BGSAVE
cp /var/lib/redis/dump.rdb /backup/local/redis/dump_$(date +%Y%m%d).rdb

# リストア
sudo systemctl stop redis
cp /backup/local/redis/dump_YYYYMMDD.rdb /var/lib/redis/dump.rdb
sudo chown redis:redis /var/lib/redis/dump.rdb
sudo systemctl start redis
```

---

## 6. バックアップ検証

### 6.1 自動検証

| 検証項目 | 実施タイミング | 方法 |
|---------|--------------|------|
| ファイルサイズ確認 | バックアップ直後 | 前日比較で異常値検知 |
| チェックサム検証 | バックアップ直後 | SHA-256照合 |
| pg_restore --list | バックアップ直後 | バックアップ構造の確認 |

### 6.2 定期リストアテスト

| テスト種別 | 頻度 | 環境 | 確認内容 |
|-----------|------|------|---------|
| フルリストアテスト | 月次 | テスト環境 | 全データの復元・アプリ動作確認 |
| PITRテスト | 四半期 | テスト環境 | 特定時点への復元精度 |
| DRテスト | 年次 | DR環境 | RTO/RPO目標の達成確認 |

### 6.3 リストアテストチェックリスト

- [ ] バックアップファイルのチェックサム一致
- [ ] pg_restore が正常完了
- [ ] テーブル数・レコード数が想定通り
- [ ] アプリケーションのマイグレーションが一致
- [ ] 主要機能（リスク管理・コンプライアンス・監査）が動作
- [ ] ユーザ認証が正常動作
- [ ] リストア所要時間がRTO内（4時間以内）
- [ ] データ損失がRPO内（24時間以内）

---

## 7. ISO27001 / NIST CSF 2.0 関連

### 7.1 ISO27001:2022 管理策対応

| 管理策ID | 管理策名 | 本文書での対応 |
|---------|---------|--------------|
| A.8.13 | 情報のバックアップ | バックアップ設計・手順 |
| A.8.14 | 情報処理施設の冗長性 | 3世代管理・リモート保管 |
| A.5.30 | 事業継続のためのICTの備え | RTO/RPO定義・DRテスト |
| A.8.10 | 情報の削除 | 世代管理による適切な削除 |
| A.8.24 | 暗号の利用 | バックアップデータの暗号化 |

### 7.2 NIST CSF 2.0 対応

| 機能 | カテゴリ | 本文書での対応 |
|------|---------|--------------|
| PROTECT (PR) | PR.DS | データセキュリティ（暗号化バックアップ） |
| PROTECT (PR) | PR.IP | 情報保護プロセス（バックアップ手順） |
| RECOVER (RC) | RC.RP | 復旧計画の実行（リストア手順） |
| RECOVER (RC) | RC.IM | 復旧の改善（定期テスト） |

---

## 8. 改訂履歴

| バージョン | 日付 | 変更者 | 変更内容 |
|-----------|------|--------|---------|
| 1.0.0 | 2026-03-26 | インフラチーム | 初版作成 |
