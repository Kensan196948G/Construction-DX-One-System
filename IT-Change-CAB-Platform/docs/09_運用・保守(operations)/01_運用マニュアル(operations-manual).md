# 運用マニュアル
## IT変更管理・リリース自動化プラットフォーム（IT-Change-CAB-Platform）

| 項目 | 内容 |
|------|------|
| **文書番号** | OPS-CAB-001 |
| **バージョン** | 1.0.0 |
| **作成日** | 2026-03-26 |
| **作成者** | みらい建設工業 IT部門 |
| **対象リポジトリ** | Kensan196948G/IT-Change-CAB-Platform |

---

## 1. 運用体制

### 1.1 運用担当者

| 役割 | 担当 | 責務 |
|------|------|------|
| システム管理者 | IT部門 インフラ担当 | サーバー管理、バックアップ、障害一次対応 |
| アプリケーション管理者 | IT部門 開発担当 | アプリケーション設定、ユーザー管理、不具合対応 |
| データベース管理者 | IT部門 インフラ担当 | DB運用、パフォーマンスチューニング |
| 運用責任者 | IT部門長 | エスカレーション先、最終判断 |

### 1.2 連絡先一覧

| 連絡先 | 用途 | 手段 |
|--------|------|------|
| IT部門 運用チーム | 通常運用問い合わせ | Teams チャネル「CAB-Platform-Ops」 |
| 運用責任者 | 重大障害エスカレーション | 電話 / Teams |
| 外部ベンダー | インフラ障害時 | メール / 電話 |

---

## 2. 日常運用手順

### 2.1 日次作業

| 時刻 | 作業内容 | 手順 | 確認者 |
|------|---------|------|--------|
| 09:00 | システムヘルスチェック | 1. 監視ダッシュボード確認 2. 各サービス稼働状況確認 3. 前日のエラーログ確認 | システム管理者 |
| 09:15 | バックアップ確認 | 1. 前日の自動バックアップ成功確認 2. バックアップサイズ確認 | システム管理者 |
| 09:30 | ジョブキュー確認 | 1. BullMQダッシュボード確認 2. 失敗ジョブの確認・リトライ | アプリ管理者 |
| 17:00 | 日次レポート確認 | 1. 当日のRFC起票/承認件数確認 2. 通知送信状況確認 | アプリ管理者 |

### 2.2 週次作業

| 曜日 | 作業内容 | 手順 | 確認者 |
|------|---------|------|--------|
| 月曜 | ディスク使用量確認 | 1. 各コンテナのディスク使用量確認 2. ログローテーション確認 | システム管理者 |
| 水曜 | セキュリティアップデート確認 | 1. npm audit 実行 2. Docker イメージ脆弱性スキャン | アプリ管理者 |
| 金曜 | 週次運用レポート作成 | 1. 稼働率計算 2. 障害件数集計 3. KPIサマリー | 運用責任者 |

### 2.3 月次作業

| 時期 | 作業内容 | 手順 | 確認者 |
|------|---------|------|--------|
| 月初 | 月次運用レポート作成 | 1. 前月の稼働率算出 2. SLA達成状況確認 3. 改善計画策定 | 運用責任者 |
| 月初 | 証明書有効期限確認 | 1. SSL証明書の有効期限確認 2. 30日以内期限切れのアラート確認 | システム管理者 |
| 月中 | パフォーマンス分析 | 1. 応答時間トレンド確認 2. リソース使用量トレンド確認 | システム管理者 |
| 月末 | バックアップリストアテスト | 1. バックアップからテスト環境へのリストア実行 2. データ整合性確認 | システム管理者 |

---

## 3. システム起動・停止手順

### 3.1 システム起動

```bash
# 1. Docker Compose で全サービス起動
cd /opt/cab-platform
docker compose up -d

# 2. サービス起動確認
docker compose ps

# 3. ヘルスチェック
curl -f http://localhost:8000/api/v1/health
curl -f http://localhost:3000

# 4. データベース接続確認
docker compose exec backend node -e "
  const { Pool } = require('pg');
  const pool = new Pool({ connectionString: process.env.DATABASE_URL });
  pool.query('SELECT 1').then(() => console.log('DB OK')).catch(console.error);
"

# 5. Redis接続確認
docker compose exec redis redis-cli ping
```

**起動順序:**
1. PostgreSQL（db） → 2. Redis（redis） → 3. バックエンドAPI（backend） → 4. BullMQワーカー（worker） → 5. フロントエンド（frontend）

### 3.2 システム停止

```bash
# 1. 新規リクエスト受付停止（メンテナンスモード有効化）
curl -X POST http://localhost:8000/api/v1/admin/maintenance \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"enabled": true, "message": "定期メンテナンス中です"}'

# 2. 進行中のジョブ完了待ち（最大5分）
docker compose exec backend node -e "
  const Queue = require('bullmq');
  // アクティブジョブ確認
"

# 3. サービス停止
docker compose down

# 4. 停止確認
docker compose ps
```

### 3.3 計画停止時の通知

| 通知タイミング | 対象 | 手段 |
|--------------|------|------|
| 停止3日前 | 全ユーザー | メール + Teams通知 |
| 停止1日前 | 全ユーザー | メール + Teams通知 |
| 停止直前 | 全ユーザー | アプリ内バナー |
| 復旧完了時 | 全ユーザー | メール + Teams通知 |

---

## 4. 監視項目

### 4.1 サービス監視

| 監視対象 | チェック方法 | 間隔 | アラート閾値 |
|---------|------------|------|------------|
| バックエンドAPI | GET /api/v1/health | 30秒 | 2回連続失敗 |
| フロントエンド | GET / (HTTP 200) | 60秒 | 2回連続失敗 |
| PostgreSQL | pg_isready | 30秒 | 1回失敗 |
| Redis | redis-cli ping | 30秒 | 1回失敗 |
| BullMQワーカー | ジョブ処理状況 | 60秒 | 失敗ジョブ10件以上 |

### 4.2 リソース監視

| 監視対象 | メトリクス | 警告閾値 | 危険閾値 |
|---------|----------|---------|---------|
| CPU | 使用率 | 70% | 90% |
| メモリ | 使用率 | 80% | 95% |
| ディスク | 使用率 | 70% | 85% |
| DB接続数 | アクティブ接続 | 80% of max | 95% of max |
| Redis メモリ | 使用量 | 70% of max | 90% of max |

### 4.3 アプリケーション監視

| 監視対象 | メトリクス | 閾値 |
|---------|----------|------|
| API応答時間 | p95 レスポンスタイム | > 2秒で警告 |
| エラー率 | 5xxエラー率 | > 1%で警告 |
| 通知送信遅延 | キュー滞留時間 | > 5分で警告 |
| 認証失敗 | 連続失敗数 | > 10回/分で警告 |

---

## 5. アラート対応手順

### 5.1 アラートレベル

| レベル | 条件 | 対応 | 通知先 |
|-------|------|------|--------|
| INFO | 軽微な警告 | ログ記録、次営業日確認 | 運用チームチャネル |
| WARNING | 閾値超過 | 1時間以内に確認・対応 | 運用チーム + 管理者 |
| CRITICAL | サービス障害 | 即時対応 | 運用チーム + 管理者 + 運用責任者 |

### 5.2 アラート別対応手順

#### CPU高負荷アラート

```
1. docker stats で各コンテナのCPU確認
2. 高負荷コンテナの特定
3. プロセス確認（docker compose exec <service> top）
4. 原因特定：
   - リクエスト急増 → ロードバランサー確認、レート制限確認
   - バッチ処理 → ジョブスケジュール確認
   - バグ（無限ループ等） → アプリケーションログ確認
5. 対策実施（コンテナ再起動 / スケールアウト / 原因修正）
```

#### メモリ高使用率アラート

```
1. docker stats でメモリ使用量確認
2. 高使用コンテナの特定
3. 原因特定：
   - メモリリーク → ヒープダンプ取得、Node.js --max-old-space-size 確認
   - キャッシュ肥大化 → Redis DBSIZE 確認、TTL設定確認
   - DB接続プールリーク → pg_stat_activity 確認
4. 対策実施（キャッシュクリア / コンテナ再起動 / 設定修正）
```

#### データベース接続アラート

```
1. docker compose exec db psql -c "SELECT count(*) FROM pg_stat_activity;"
2. アイドル接続の確認
3. 原因特定：
   - 接続リーク → アプリケーションログ確認
   - 接続プール設定不備 → pool.max 設定確認
4. 対策：
   - アイドル接続の強制切断
   - 接続プール設定調整
   - アプリケーション修正
```

---

## 6. バックアップ

### 6.1 バックアップ方針

| バックアップ対象 | 方式 | 頻度 | 保持期間 | 保存先 |
|---------------|------|------|---------|--------|
| PostgreSQLデータ | pg_dump（論理バックアップ） | 日次 02:00 | 30日 | /backup/db/ |
| PostgreSQL WAL | 継続的アーカイブ | リアルタイム | 7日 | /backup/wal/ |
| Redis データ | RDBスナップショット | 日次 03:00 | 7日 | /backup/redis/ |
| アプリケーション設定 | ファイルコピー | 変更時 | 永続 | Git リポジトリ |
| ログファイル | ローテーション + 圧縮 | 日次 | 90日 | /backup/logs/ |
| Docker ボリューム | tar 圧縮 | 週次 | 4世代 | /backup/volumes/ |

### 6.2 バックアップスクリプト

```bash
#!/bin/bash
# /opt/cab-platform/scripts/backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/db"

# PostgreSQL バックアップ
docker compose exec -T db pg_dump \
  -U admin \
  -d cab_platform \
  --format=custom \
  --compress=9 \
  > "${BACKUP_DIR}/cab_platform_${DATE}.dump"

# バックアップ検証
pg_restore --list "${BACKUP_DIR}/cab_platform_${DATE}.dump" > /dev/null 2>&1
if [ $? -eq 0 ]; then
  echo "[$(date)] バックアップ成功: cab_platform_${DATE}.dump"
else
  echo "[$(date)] バックアップ検証失敗!" | mail -s "バックアップ失敗アラート" it-ops@mirai-kensetsu.co.jp
fi

# 古いバックアップ削除（30日以上）
find "${BACKUP_DIR}" -name "*.dump" -mtime +30 -delete
```

### 6.3 リストア手順

```bash
# 1. 対象バックアップファイル確認
ls -la /backup/db/

# 2. リストア実行（テスト環境で先行確認推奨）
docker compose exec -T db pg_restore \
  -U admin \
  -d cab_platform \
  --clean \
  --if-exists \
  < /backup/db/cab_platform_YYYYMMDD_HHMMSS.dump

# 3. データ整合性確認
docker compose exec db psql -U admin -d cab_platform \
  -c "SELECT COUNT(*) FROM change_requests;"
docker compose exec db psql -U admin -d cab_platform \
  -c "SELECT COUNT(*) FROM cab_decisions;"

# 4. アプリケーション動作確認
curl -f http://localhost:8000/api/v1/health
```

---

## 7. ログ管理

### 7.1 ログ種別

| ログ種別 | 出力先 | ローテーション | 保持期間 |
|---------|--------|-------------|---------|
| アプリケーションログ | stdout → Docker logs | 日次、100MB | 90日 |
| アクセスログ | stdout → Docker logs | 日次、100MB | 90日 |
| エラーログ | stderr → Docker logs | 日次、50MB | 180日 |
| DBスロークエリログ | PostgreSQL log | 日次 | 30日 |
| 監査ログ | 専用テーブル + ファイル | 月次 | 1年 |

### 7.2 ログ確認コマンド

```bash
# 各サービスのログ確認
docker compose logs -f backend --tail=100
docker compose logs -f worker --tail=100
docker compose logs -f db --tail=50

# エラーログのみ抽出
docker compose logs backend 2>&1 | grep -i "error"

# 特定期間のログ
docker compose logs --since="2026-03-26T09:00:00" --until="2026-03-26T10:00:00" backend
```

---

## 8. 定期メンテナンス

### 8.1 メンテナンススケジュール

| 作業 | 頻度 | 所要時間 | サービス影響 |
|------|------|---------|------------|
| セキュリティパッチ適用 | 月次（第2日曜） | 1-2時間 | 短時間停止あり |
| データベースVACUUM | 週次（日曜 03:00） | 自動実行 | なし |
| ログクリーンアップ | 日次（自動） | 自動実行 | なし |
| Docker イメージ更新 | 四半期 | 2-3時間 | 計画停止 |
| SSL証明書更新 | 年次（有効期限30日前） | 30分 | 短時間停止あり |

### 8.2 メンテナンスモード

```bash
# メンテナンスモード有効化
curl -X POST http://localhost:8000/api/v1/admin/maintenance \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "message": "システムメンテナンス中です。終了予定: 06:00",
    "estimated_end": "2026-04-01T06:00:00+09:00"
  }'

# メンテナンスモード解除
curl -X POST http://localhost:8000/api/v1/admin/maintenance \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'
```

---

## 9. 災害復旧（DR）

### 9.1 RPO / RTO

| 項目 | 目標値 |
|------|--------|
| RPO（目標復旧時点） | 24時間（日次バックアップ） |
| RTO（目標復旧時間） | 4時間 |

### 9.2 復旧手順概要

```
1. 障害状況の把握（30分）
2. 復旧環境の準備（60分）
3. バックアップからのデータリストア（60分）
4. アプリケーションデプロイ（30分）
5. 動作確認・データ整合性検証（30分）
6. DNS切り替え・ユーザーアクセス復旧（30分）
合計: 約4時間
```

---

*文書管理：本文書はバージョン管理対象。変更時はバージョン番号を更新すること。*
