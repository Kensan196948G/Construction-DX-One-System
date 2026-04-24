# ロールバック手順書（Rollback Guide）

| 項目 | 内容 |
|------|------|
| 文書番号 | GRC-RM-004 |
| バージョン | 1.0 |
| 作成日 | 2026-03-26 |
| 最終更新日 | 2026-03-26 |
| 作成者 | GRC開発チーム |
| 承認者 | インフラストラクチャリード |
| 分類 | リリース管理 |
| 準拠規格 | ISO27001:2022 / NIST CSF 2.0 / 建設業法 / 品確法 / 労安法 |

---

## 1. 目的

本文書は、Construction-GRC-Systemのリリース後に問題が発生した場合のロールバック（切り戻し）手順を定義する。迅速かつ安全にシステムを前のバージョンに復旧し、サービス影響を最小限に抑えることを目的とする。

---

## 2. ロールバック判断基準

### 2.1 ロールバック発動条件

以下のいずれかに該当する場合、ロールバックを発動する。

| レベル | 条件 | 判断者 | 対応時間 |
|-------|------|--------|---------|
| Critical | システム全体が停止している | インフラ担当（即時判断可） | 15分以内に開始 |
| Critical | データ破損の可能性がある | DBA + インフラ担当 | 15分以内に開始 |
| Critical | セキュリティインシデント発生 | セキュリティ責任者 | 30分以内に開始 |
| High | 主要機能が利用不能 | テックリード | 1時間以内に開始 |
| High | エラーレートが5%を超過 | インフラ担当 | 1時間以内に開始 |
| High | GRC管理策の重大な不適合が発見された | GRC管理者 | 2時間以内に開始 |
| Medium | パフォーマンスが著しく劣化（p95 > 10秒） | テックリード | 次回メンテナンスウィンドウ |
| Medium | 法令準拠性に影響する不具合 | コンプライアンス担当 | 2時間以内に開始 |

### 2.2 ロールバック判断フロー

```
問題検知
  │
  ├─► 障害レベル判定
  │    │
  │    ├── Critical ──► 即時ロールバック（承認は事後）
  │    │
  │    ├── High ──► テックリード/GRC管理者判断
  │    │              ├── ロールバック ──► 実行
  │    │              └── ホットフィックス ──► 修正対応
  │    │
  │    └── Medium以下 ──► 修正対応（次回パッチで対応）
  │
  └─► ロールバック実行
       │
       ├─► アプリケーション ロールバック
       ├─► データベース ロールバック（必要な場合）
       ├─► 検証
       └─► 事後報告
```

### 2.3 ロールバックしない場合の条件

| 条件 | 理由 |
|------|------|
| 影響が限定的で回避策がある | ホットフィックスで対応可能 |
| ロールバックによるデータ損失が大きい | データ復旧コストの方が高い |
| 新バージョンのデータ形式に依存するデータが大量に生成済み | ロールバック後のデータ整合性が保てない |

---

## 3. ロールバック前の準備

### 3.1 事前準備チェックリスト

| # | 項目 | 確認者 | 確認結果 |
|---|------|--------|---------|
| RB-01 | 現在のバージョン番号を記録 | インフラ担当 | v_______ |
| RB-02 | ロールバック先のバージョン番号を確認 | インフラ担当 | v_______ |
| RB-03 | 現在のデータベースの状態をバックアップ | DBA | [ ] 完了 |
| RB-04 | 影響を受けるユーザーへの通知準備 | PM | [ ] 完了 |
| RB-05 | ロールバック後のデータ整合性リスク確認 | DBA | [ ] 確認済み |
| RB-06 | メンテナンスモード切替準備 | インフラ担当 | [ ] 準備完了 |

### 3.2 ロールバック対象の確認

```bash
# 現在のバージョン確認
cat VERSION

# 前回のデプロイログ確認
cat DEPLOY_LOG | tail -5

# 利用可能なバージョン一覧
git tag -l "v*" --sort=-v:refname | head -10

# 前回のDockerイメージ確認
docker images | grep grc | sort -k2 -V
```

---

## 4. アプリケーション ロールバック手順

### 4.1 Docker Composeによるロールバック

```bash
# ===== STEP 1: メンテナンスモード有効化 =====
cd /opt/grc-system

COMPOSE_CMD="docker compose -f docker/docker-compose.yml -f docker/docker-compose.prod.yml"

$COMPOSE_CMD exec -T backend python manage.py maintenance_mode --enable

echo "メンテナンスモード有効化完了: $(date)"

# ===== STEP 2: 現在の状態を記録 =====
CURRENT_VERSION=$(cat VERSION)
ROLLBACK_VERSION="${1:-}"  # ロールバック先バージョンを引数で指定

echo "現在のバージョン: $CURRENT_VERSION"
echo "ロールバック先: $ROLLBACK_VERSION"

# 現在のコンテナ状態を記録
$COMPOSE_CMD ps > /tmp/rollback_pre_state_$(date +%Y%m%d_%H%M%S).txt

# ===== STEP 3: ロールバック先のコードに切替 =====

# Gitタグを使用してロールバック
git fetch origin
git checkout "v${ROLLBACK_VERSION}"

# ===== STEP 4: Dockerイメージの切替 =====

# レジストリからロールバック先イメージをプル
docker pull ${REGISTRY}/grc-backend:v${ROLLBACK_VERSION}
docker pull ${REGISTRY}/grc-frontend:v${ROLLBACK_VERSION}

# または、ローカルにキャッシュされたイメージを使用
# docker tag grc-backend:v${ROLLBACK_VERSION} grc-backend:latest
# docker tag grc-frontend:v${ROLLBACK_VERSION} grc-frontend:latest

# ===== STEP 5: 環境変数の復元（必要な場合）=====
# バックアップされた環境変数ファイルを復元
if [ -f ".env.production.bak.${ROLLBACK_VERSION}" ]; then
  cp ".env.production.bak.${ROLLBACK_VERSION}" .env.production
fi

# ===== STEP 6: コンテナの再起動 =====
export VERSION=$ROLLBACK_VERSION
$COMPOSE_CMD up -d --remove-orphans

echo "コンテナ再起動完了: $(date)"

# ===== STEP 7: ヘルスチェック =====
./scripts/health-check.sh production

# ===== STEP 8: メンテナンスモード解除 =====
$COMPOSE_CMD exec -T backend python manage.py maintenance_mode --disable

# ===== STEP 9: 検証 =====
./scripts/smoke-test.sh production

# ===== STEP 10: バージョン記録 =====
echo "v${ROLLBACK_VERSION}" > VERSION
echo "Rolled back from v${CURRENT_VERSION} to v${ROLLBACK_VERSION} at $(date)" >> DEPLOY_LOG

echo "===== ロールバック完了 ====="
```

### 4.2 ロールバックスクリプト（scripts/rollback.sh）

```bash
#!/bin/bash
set -euo pipefail

# =============================================================================
# Construction-GRC-System ロールバックスクリプト
# 使用方法: ./scripts/rollback.sh <environment> <target_version>
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="${1:-}"
TARGET_VERSION="${2:-}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/var/log/grc-deploy/rollback_${ENVIRONMENT}_${TIMESTAMP}.log"

# 引数検証
if [[ -z "$ENVIRONMENT" ]] || [[ -z "$TARGET_VERSION" ]]; then
  echo "ERROR: 使用方法: ./scripts/rollback.sh <environment> <target_version>"
  echo "  例: ./scripts/rollback.sh production 1.0.0"
  exit 1
fi

# ログ関数
log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ROLLBACK] [$ENVIRONMENT] $1" | tee -a "$LOG_FILE"
}

trap 'log "ERROR: ロールバック中にエラーが発生しました（行: $LINENO）"; exit 1' ERR

CURRENT_VERSION=$(cat "${PROJECT_DIR}/VERSION" 2>/dev/null || echo "unknown")

log "===== ロールバック開始 ====="
log "環境: $ENVIRONMENT"
log "現在のバージョン: $CURRENT_VERSION"
log "ロールバック先: $TARGET_VERSION"

# 確認プロンプト（本番環境のみ）
if [[ "$ENVIRONMENT" == "production" ]]; then
  read -p "本番環境をv${TARGET_VERSION}にロールバックします。続行しますか？ (yes/no): " CONFIRM
  if [[ "$CONFIRM" != "yes" ]]; then
    log "ロールバックがキャンセルされました"
    exit 0
  fi
fi

# Compose ファイル指定
COMPOSE_CMD="docker compose -f ${PROJECT_DIR}/docker/docker-compose.yml"
case $ENVIRONMENT in
  development)  COMPOSE_CMD="$COMPOSE_CMD -f ${PROJECT_DIR}/docker/docker-compose.dev.yml" ;;
  staging)      COMPOSE_CMD="$COMPOSE_CMD -f ${PROJECT_DIR}/docker/docker-compose.staging.yml" ;;
  production)   COMPOSE_CMD="$COMPOSE_CMD -f ${PROJECT_DIR}/docker/docker-compose.prod.yml" ;;
esac

# STEP 1: バックアップ
log "現在の状態をバックアップ中..."
${SCRIPT_DIR}/backup.sh "$ENVIRONMENT" --pre-rollback
log "バックアップ完了"

# STEP 2: メンテナンスモード
if [[ "$ENVIRONMENT" != "development" ]]; then
  log "メンテナンスモード有効化..."
  $COMPOSE_CMD exec -T backend python manage.py maintenance_mode --enable 2>/dev/null || true
fi

# STEP 3: コード切替
log "コードをv${TARGET_VERSION}に切替中..."
cd "$PROJECT_DIR"
git fetch origin
git checkout "v${TARGET_VERSION}"

# STEP 4: コンテナ更新
log "コンテナを更新中..."
export VERSION=$TARGET_VERSION
$COMPOSE_CMD up -d --remove-orphans

# STEP 5: ヘルスチェック
log "ヘルスチェック実行中..."
${SCRIPT_DIR}/health-check.sh "$ENVIRONMENT"

# STEP 6: メンテナンスモード解除
if [[ "$ENVIRONMENT" != "development" ]]; then
  log "メンテナンスモード解除..."
  $COMPOSE_CMD exec -T backend python manage.py maintenance_mode --disable 2>/dev/null || true
fi

# STEP 7: 記録
echo "v${TARGET_VERSION}" > "${PROJECT_DIR}/VERSION"
echo "Rolled back from v${CURRENT_VERSION} to v${TARGET_VERSION} at $(date)" >> "${PROJECT_DIR}/DEPLOY_LOG"

log "===== ロールバック完了 ====="
log "ロールバック元: v${CURRENT_VERSION} → ロールバック先: v${TARGET_VERSION}"
```

---

## 5. データベース ロールバック手順

### 5.1 データベースロールバックの判断

| 条件 | ロールバック方法 |
|------|---------------|
| マイグレーションが後方互換 | アプリケーションロールバックのみ（DBロールバック不要） |
| マイグレーションにリバースが用意されている | Djangoマイグレーションのリバース実行 |
| マイグレーションが破壊的（カラム削除等） | データベースバックアップからの復元 |
| データ移行を伴う大規模変更 | ポイントインタイムリカバリ（PITR） |

### 5.2 Djangoマイグレーション リバース

```bash
# 現在のマイグレーション状態確認
$COMPOSE_CMD exec -T backend python manage.py showmigrations

# 特定のマイグレーションにロールバック
# 例: risk_management アプリの 0005 まで戻す
$COMPOSE_CMD exec -T backend python manage.py migrate risk_management 0005

# 全アプリのマイグレーション状態を指定バージョンに戻す
# ロールバック対象マイグレーションリスト（リリースノートに記載）に従い実行
$COMPOSE_CMD exec -T backend python manage.py migrate compliance_management 0012
$COMPOSE_CMD exec -T backend python manage.py migrate audit_management 0008

# マイグレーション状態の確認
$COMPOSE_CMD exec -T backend python manage.py showmigrations
```

### 5.3 データベースバックアップからの復元

```bash
# ===== 方法A: pg_dumpからの復元 =====

# 1. 現在のデータベースを退避
$COMPOSE_CMD exec -T postgres pg_dump -U grc_user grc_production > /tmp/pre_rollback_$(date +%Y%m%d_%H%M%S).sql

# 2. アプリケーションコンテナを停止（DB接続を切断）
$COMPOSE_CMD stop backend celery-worker celery-beat

# 3. データベースの削除と再作成
$COMPOSE_CMD exec -T postgres psql -U postgres -c "DROP DATABASE IF EXISTS grc_production;"
$COMPOSE_CMD exec -T postgres psql -U postgres -c "CREATE DATABASE grc_production OWNER grc_user;"

# 4. バックアップからリストア
$COMPOSE_CMD exec -T postgres psql -U grc_user grc_production < /backup/grc_production_YYYYMMDD_HHMMSS.sql

# 5. アプリケーションコンテナを起動
$COMPOSE_CMD start backend celery-worker celery-beat

# 6. データ整合性確認
$COMPOSE_CMD exec -T backend python manage.py check_data_integrity


# ===== 方法B: AWS RDS ポイントインタイムリカバリ（本番環境）=====

# 1. 復旧ポイントの確認
aws rds describe-db-instances --db-instance-identifier grc-production \
  --query 'DBInstances[0].LatestRestorableTime'

# 2. ポイントインタイムリカバリでインスタンス作成
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier grc-production \
  --target-db-instance-identifier grc-production-rollback \
  --restore-time "2026-03-25T21:00:00Z" \
  --db-instance-class db.r6g.xlarge

# 3. 復旧インスタンスの起動完了を待機
aws rds wait db-instance-available \
  --db-instance-identifier grc-production-rollback

# 4. エンドポイントの切替
# .env.production の DATABASE_URL を復旧インスタンスのエンドポイントに変更

# 5. アプリケーション再起動
$COMPOSE_CMD up -d --remove-orphans

# 6. 旧インスタンスの保持（問題がなければ7日後に削除）
```

### 5.4 データ整合性確認

```bash
# ロールバック後のデータ整合性チェック
$COMPOSE_CMD exec -T backend python manage.py check_data_integrity

# 主要テーブルのレコード数確認
$COMPOSE_CMD exec -T postgres psql -U grc_user grc_production -c "
SELECT
  'risks' as table_name, COUNT(*) as count FROM risks
UNION ALL
SELECT 'compliance_items', COUNT(*) FROM compliance_items
UNION ALL
SELECT 'audit_records', COUNT(*) FROM audit_records
UNION ALL
SELECT 'users', COUNT(*) FROM auth_user
UNION ALL
SELECT 'audit_logs', COUNT(*) FROM audit_logs;
"

# 外部キー整合性チェック
$COMPOSE_CMD exec -T backend python manage.py validate_foreign_keys

# 監査ログの連続性チェック
$COMPOSE_CMD exec -T backend python manage.py check_audit_log_continuity
```

---

## 6. データ復旧手順

### 6.1 バックアップ戦略

| バックアップ種別 | 頻度 | 保持期間 | 保存先 | 暗号化 |
|---------------|------|---------|--------|--------|
| フルバックアップ | 日次（深夜2:00） | 30日 | S3 + 別リージョン | AES-256 |
| 差分バックアップ | 6時間ごと | 7日 | S3 | AES-256 |
| トランザクションログ（WAL） | 継続的 | 7日 | S3 | AES-256 |
| ファイルストレージ（MinIO） | 日次 | 30日 | S3 | AES-256 |
| 設定ファイル | 変更時 | 90日 | S3 + Git | AES-256 |

### 6.2 バックアップスクリプト（scripts/backup.sh）

```bash
#!/bin/bash
set -euo pipefail

# =============================================================================
# Construction-GRC-System バックアップスクリプト
# 使用方法: ./scripts/backup.sh <environment> [--full|--pre-rollback|--verify]
# =============================================================================

ENVIRONMENT="${1:-}"
BACKUP_TYPE="${2:---full}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/grc-system/${ENVIRONMENT}"
S3_BUCKET="s3://grc-backup-${ENVIRONMENT}"

mkdir -p "$BACKUP_DIR"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] [BACKUP] $1"
}

case $BACKUP_TYPE in
  --full|--pre-rollback)
    log "フルバックアップ開始: $ENVIRONMENT"

    # データベースバックアップ
    COMPOSE_CMD="docker compose -f docker/docker-compose.yml -f docker/docker-compose.${ENVIRONMENT}.yml"

    DB_BACKUP_FILE="${BACKUP_DIR}/db_${TIMESTAMP}.sql.gz"
    $COMPOSE_CMD exec -T postgres pg_dump -U grc_user grc_${ENVIRONMENT} | gzip > "$DB_BACKUP_FILE"
    log "データベースバックアップ完了: $DB_BACKUP_FILE"

    # ファイルストレージバックアップ
    FILE_BACKUP="${BACKUP_DIR}/files_${TIMESTAMP}.tar.gz"
    tar -czf "$FILE_BACKUP" -C /opt/grc-system media/ 2>/dev/null || true
    log "ファイルバックアップ完了: $FILE_BACKUP"

    # 設定ファイルバックアップ
    CONFIG_BACKUP="${BACKUP_DIR}/config_${TIMESTAMP}.tar.gz"
    tar -czf "$CONFIG_BACKUP" -C /opt/grc-system .env.${ENVIRONMENT} docker/ nginx/ 2>/dev/null || true
    log "設定バックアップ完了: $CONFIG_BACKUP"

    # S3アップロード（本番環境のみ）
    if [[ "$ENVIRONMENT" == "production" ]]; then
      aws s3 cp "$DB_BACKUP_FILE" "${S3_BUCKET}/db/" --sse AES256
      aws s3 cp "$FILE_BACKUP" "${S3_BUCKET}/files/" --sse AES256
      aws s3 cp "$CONFIG_BACKUP" "${S3_BUCKET}/config/" --sse AES256
      log "S3アップロード完了"
    fi

    log "フルバックアップ完了"
    ;;

  --verify)
    log "バックアップ検証開始: $ENVIRONMENT"

    # 最新のバックアップファイル確認
    LATEST_DB=$(ls -t ${BACKUP_DIR}/db_*.sql.gz 2>/dev/null | head -1)
    if [[ -z "$LATEST_DB" ]]; then
      log "ERROR: データベースバックアップが見つかりません"
      exit 1
    fi

    # バックアップファイルの整合性確認
    gzip -t "$LATEST_DB"
    log "バックアップファイル整合性: OK"

    # バックアップサイズ確認
    BACKUP_SIZE=$(du -sh "$LATEST_DB" | cut -f1)
    log "最新バックアップサイズ: $BACKUP_SIZE"

    log "バックアップ検証完了"
    ;;
esac
```

### 6.3 リストア手順

```bash
# ===== 手順1: バックアップファイルの特定 =====

# ローカルバックアップ一覧
ls -la /backup/grc-system/production/db_*.sql.gz

# S3バックアップ一覧
aws s3 ls s3://grc-backup-production/db/ --recursive | sort -k1,2

# ===== 手順2: バックアップファイルのダウンロード（S3の場合）=====
aws s3 cp s3://grc-backup-production/db/db_20260325_020000.sql.gz /tmp/restore/

# ===== 手順3: リストア実行 =====
# 上記「5.3 データベースバックアップからの復元」を参照

# ===== 手順4: リストア後検証 =====
# 上記「5.4 データ整合性確認」を参照
```

---

## 7. 部分ロールバック

### 7.1 特定機能のみのロールバック

特定の機能モジュールのみに問題がある場合、フィーチャーフラグを使用して機能を無効化する。

```bash
# フィーチャーフラグによる機能無効化
$COMPOSE_CMD exec -T backend python manage.py feature_flag --disable risk_assessment_v2
$COMPOSE_CMD exec -T backend python manage.py feature_flag --disable compliance_dashboard_new

# フィーチャーフラグ状態確認
$COMPOSE_CMD exec -T backend python manage.py feature_flag --list
```

### 7.2 フィーチャーフラグ一覧

| フラグ名 | 対応機能 | デフォルト |
|---------|---------|----------|
| `risk_assessment_v2` | リスク評価v2エンジン | ON |
| `compliance_dashboard_new` | 新コンプライアンスダッシュボード | ON |
| `ai_risk_analysis` | AI支援リスク分析 | OFF |
| `nist_csf_mapping` | NIST CSFマッピング表示 | ON |
| `construction_law_check` | 建設業法自動チェック | ON |

---

## 8. ロールバック後の対応

### 8.1 ロールバック後チェックリスト

| # | 項目 | 担当 | 完了 |
|---|------|------|------|
| 1 | 全機能のスモークテスト合格 | QAリード | [ ] |
| 2 | 監査ログの記録確認 | GRC管理者 | [ ] |
| 3 | データ整合性確認 | DBA | [ ] |
| 4 | ユーザーへの通知 | PM | [ ] |
| 5 | 障害報告書の作成 | PM | [ ] |
| 6 | 根本原因分析（RCA）の実施 | テックリード | [ ] |
| 7 | 再リリース計画の策定 | PM | [ ] |
| 8 | GitHub Projectsのステータス更新 | PM | [ ] |

### 8.2 障害報告書テンプレート

```markdown
# 障害報告書

## 基本情報
- 障害発生日時: YYYY-MM-DD HH:MM
- 障害検知日時: YYYY-MM-DD HH:MM
- ロールバック完了日時: YYYY-MM-DD HH:MM
- 影響時間: X時間X分
- 障害レベル: Critical / High / Medium

## 障害概要
（障害の概要を記載）

## 影響範囲
- 影響を受けたユーザー数: XXX名
- 影響を受けた機能: （機能名）
- データへの影響: あり / なし

## 根本原因
（根本原因を記載）

## 対応履歴
| 日時 | 対応内容 | 担当者 |
|------|---------|--------|
| HH:MM | 障害検知 | ○○ |
| HH:MM | ロールバック判断 | ○○ |
| HH:MM | ロールバック完了 | ○○ |

## 再発防止策
1. （再発防止策を記載）
2. （再発防止策を記載）

## 再リリース計画
- 修正予定日: YYYY-MM-DD
- 再リリース予定日: YYYY-MM-DD
```

---

## 9. 定期ロールバック訓練

### 9.1 訓練計画

| 項目 | 内容 |
|------|------|
| 実施頻度 | 四半期に1回 |
| 実施環境 | ステージング環境 |
| 参加者 | インフラ担当、テックリード、DBA、QAリード |
| 所要時間 | 2〜3時間 |
| 目的 | ロールバック手順の実効性確認、対応時間の測定 |

### 9.2 訓練シナリオ

| シナリオ | 内容 | 目標時間 |
|---------|------|---------|
| シナリオ1 | アプリケーションのみのロールバック | 15分以内 |
| シナリオ2 | データベースマイグレーションリバース | 30分以内 |
| シナリオ3 | データベースバックアップからの復元 | 60分以内 |
| シナリオ4 | 全体ロールバック（アプリ+DB+ファイル） | 90分以内 |

---

## 10. 改訂履歴

| バージョン | 日付 | 変更内容 | 変更者 |
|-----------|------|---------|--------|
| 1.0 | 2026-03-26 | 初版作成 | GRC開発チーム |
