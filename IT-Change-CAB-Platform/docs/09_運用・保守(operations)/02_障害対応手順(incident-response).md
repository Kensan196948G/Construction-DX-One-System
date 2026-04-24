# 障害対応手順書
## IT変更管理・リリース自動化プラットフォーム（IT-Change-CAB-Platform）

| 項目 | 内容 |
|------|------|
| **文書番号** | OPS-CAB-002 |
| **バージョン** | 1.0.0 |
| **作成日** | 2026-03-26 |
| **作成者** | みらい建設工業 IT部門 |
| **対象リポジトリ** | Kensan196948G/IT-Change-CAB-Platform |

---

## 1. 障害対応方針

### 1.1 目的

本プラットフォームで発生する障害に対し、迅速かつ適切な対応を行うための手順を定める。障害の検知から復旧、事後対応までの一連のプロセスを標準化し、RTO 4時間以内の復旧を達成する。

### 1.2 適用範囲

- フロントエンド（React アプリケーション）
- バックエンドAPI（Node.js / Express）
- データベース（PostgreSQL）
- キャッシュ/キュー（Redis / BullMQ）
- インフラ（Docker / ネットワーク）
- 外部連携（Teams Webhook、メール、GitHub Actions）

---

## 2. 障害レベル分類

| レベル | 名称 | 定義 | 影響範囲 | RTO | 対応体制 |
|--------|------|------|---------|-----|---------|
| **P1** | 緊急（Critical） | サービス全停止、データ損失の恐れ | 全ユーザー利用不可 | 1時間 | 即時招集、運用責任者エスカレーション |
| **P2** | 重大（Major） | 主要機能停止、代替手段なし | 多数のユーザーに影響 | 2時間 | 即時対応、管理者報告 |
| **P3** | 警告（Minor） | 一部機能障害、代替手段あり | 一部ユーザーに影響 | 4時間 | 営業時間内対応 |
| **P4** | 軽微（Low） | 軽微な不具合、運用回避可能 | 影響限定的 | 次営業日 | 通常対応 |

### 2.1 障害レベル判定フロー

```
障害検知
  │
  ├── 全サービス停止？ ──── Yes ──→ P1（緊急）
  │
  ├── 主要機能（RFC起票/CAB承認）停止？ ──── Yes ──→ P2（重大）
  │
  ├── 一部機能障害（通知遅延/表示崩れ等）？ ──── Yes ──→ P3（警告）
  │
  └── 軽微な不具合？ ──── Yes ──→ P4（軽微）
```

### 2.2 障害レベル別事例

| レベル | 障害事例 |
|--------|---------|
| P1 | PostgreSQLサーバー停止、バックエンドAPI全停止、認証システム障害 |
| P2 | RFC起票APIエラー、CAB承認処理失敗、データ不整合 |
| P3 | 通知送信遅延、カレンダー表示遅延、レポート生成エラー |
| P4 | UI表示崩れ（特定ブラウザ）、文言誤り、非クリティカルなログエラー |

---

## 3. エスカレーションフロー

### 3.1 エスカレーション経路

```
障害検知
  │
  ▼
一次対応（システム管理者）
  │
  ├── 30分以内に解決 → 復旧完了報告
  │
  ▼ （解決不可 or P1/P2）
二次対応（アプリケーション管理者 + システム管理者）
  │
  ├── 1時間以内に解決 → 復旧完了報告
  │
  ▼ （解決不可 or P1）
三次対応（運用責任者 + 開発チーム）
  │
  ├── 外部ベンダーエスカレーション（必要時）
  │
  ▼
経営報告（P1の場合は即時）
```

### 3.2 エスカレーション連絡先

| エスカレーションレベル | 担当者 | 連絡手段 | 応答目標 |
|--------------------|--------|---------|---------|
| 一次 | システム管理者（当番） | Teams / 電話 | 15分以内 |
| 二次 | アプリケーション管理者 | Teams / 電話 | 30分以内 |
| 三次 | IT部門長（運用責任者） | 電話 | 15分以内 |
| 経営報告 | 経営層 | メール / 電話 | 1時間以内 |

### 3.3 エスカレーション判断基準

| 条件 | アクション |
|------|-----------|
| P1障害発生 | 即座に三次エスカレーション + 経営報告 |
| P2障害で30分以内に解決見込みなし | 二次エスカレーション |
| 同一障害が3回以上再発 | 運用責任者への報告 + 恒久対策検討 |
| データ損失の可能性 | 即座に三次エスカレーション |
| セキュリティインシデントの疑い | 即座にセキュリティ担当 + 三次エスカレーション |

---

## 4. 障害対応手順

### 4.1 共通手順

```
1. 障害検知・受付（5分）
   - 監視アラート / ユーザー報告の確認
   - 障害チケット起票
   - 障害レベル判定

2. 初期調査（15分）
   - 影響範囲の確認
   - ログ確認
   - 直近の変更確認

3. 応急処置（レベルに応じたRTO内）
   - サービス復旧
   - 必要に応じてロールバック

4. 原因調査（復旧後）
   - 根本原因分析（RCA）
   - 再発防止策策定

5. 事後対応
   - 障害報告書作成
   - 再発防止策実施
   - ナレッジベース更新
```

### 4.2 障害別復旧手順

#### 4.2.1 バックエンドAPI停止

**症状:** APIエンドポイントが応答しない（503/504エラー）

```bash
# 1. コンテナ状態確認
docker compose ps backend
docker compose logs --tail=50 backend

# 2. ヘルスチェック
curl -v http://localhost:8000/api/v1/health

# 3. コンテナ再起動
docker compose restart backend

# 4. 復旧確認
curl -f http://localhost:8000/api/v1/health

# 5. 再起動でも復旧しない場合 → コンテナ再作成
docker compose up -d --force-recreate backend

# 6. ログで原因確認
docker compose logs --tail=200 backend | grep -i "error\|fatal\|crash"
```

#### 4.2.2 PostgreSQL障害

**症状:** データベース接続エラー、クエリタイムアウト

```bash
# 1. PostgreSQLプロセス確認
docker compose ps db
docker compose exec db pg_isready

# 2. 接続数確認
docker compose exec db psql -U admin -d cab_platform \
  -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"

# 3. ロック状態確認
docker compose exec db psql -U admin -d cab_platform \
  -c "SELECT pid, wait_event_type, query FROM pg_stat_activity WHERE state='active' ORDER BY query_start;"

# 4. デッドロック解消
docker compose exec db psql -U admin -d cab_platform \
  -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state='idle in transaction' AND query_start < NOW() - INTERVAL '10 minutes';"

# 5. PostgreSQL再起動（最終手段）
docker compose restart db
# バックエンドも再起動（接続プールリセット）
docker compose restart backend worker

# 6. データ整合性確認
docker compose exec db psql -U admin -d cab_platform \
  -c "SELECT schemaname, relname, n_dead_tup FROM pg_stat_user_tables ORDER BY n_dead_tup DESC LIMIT 10;"
```

#### 4.2.3 Redis障害

**症状:** キャッシュ取得失敗、キュー処理停止

```bash
# 1. Redis状態確認
docker compose ps redis
docker compose exec redis redis-cli ping

# 2. メモリ使用量確認
docker compose exec redis redis-cli INFO memory

# 3. Redis再起動
docker compose restart redis

# 4. BullMQワーカー再起動
docker compose restart worker

# 5. 失敗ジョブの確認・リトライ
# BullMQダッシュボードまたはAPIで確認
curl http://localhost:8000/api/v1/admin/jobs/failed
```

#### 4.2.4 ディスク容量不足

**症状:** ディスク使用率85%超過アラート

```bash
# 1. ディスク使用量確認
df -h

# 2. 大容量ファイル特定
du -sh /var/lib/docker/volumes/*
du -sh /backup/*

# 3. Docker不要リソース削除
docker system prune -f
docker volume prune -f

# 4. 古いログ削除
find /backup/logs -name "*.gz" -mtime +90 -delete

# 5. 古いバックアップ削除
find /backup/db -name "*.dump" -mtime +30 -delete

# 6. PostgreSQLのVACUUM
docker compose exec db psql -U admin -d cab_platform -c "VACUUM FULL;"
```

#### 4.2.5 通知送信障害

**症状:** 承認通知・アラート通知が送信されない

```bash
# 1. BullMQキュー状態確認
docker compose logs --tail=50 worker

# 2. Teams Webhook接続確認
curl -X POST "$TEAMS_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"text": "接続テスト"}'

# 3. メールサーバー接続確認
docker compose exec backend node -e "
  const nodemailer = require('nodemailer');
  const transport = nodemailer.createTransport({...});
  transport.verify().then(console.log).catch(console.error);
"

# 4. 失敗ジョブのリトライ
curl -X POST http://localhost:8000/api/v1/admin/jobs/retry-failed \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

#### 4.2.6 認証障害

**症状:** ログインできない、JWT検証エラー

```bash
# 1. 認証サービスログ確認
docker compose logs --tail=50 backend | grep -i "auth\|jwt\|token"

# 2. JWTシークレット確認
docker compose exec backend printenv JWT_SECRET | head -c 5

# 3. 外部認証サービス（Entra ID等）の接続確認
curl -v https://login.microsoftonline.com/<tenant-id>/.well-known/openid-configuration

# 4. 応急処置：ローカル認証への切り替え（設定ファイルで制御）
# 5. バックエンド再起動
docker compose restart backend
```

---

## 5. 障害記録

### 5.1 障害チケット記載項目

| 項目 | 内容 |
|------|------|
| 障害ID | INC-YYYY-NNN（自動採番） |
| 検知日時 | 障害発生/検知日時 |
| 障害レベル | P1 / P2 / P3 / P4 |
| 影響範囲 | 影響サービス、影響ユーザー数 |
| 症状 | 障害の症状・エラー内容 |
| 原因 | 根本原因 |
| 応急処置 | 実施した応急処置 |
| 恒久対策 | 再発防止策 |
| 対応者 | 対応した担当者 |
| 復旧日時 | 復旧完了日時 |
| ダウンタイム | 障害時間（分） |

### 5.2 障害報告書テンプレート

```
━━━━━━━━━━━━━━━━━━━━━━
障害報告書
━━━━━━━━━━━━━━━━━━━━━━

障害ID:     INC-2026-XXX
報告日:     2026-XX-XX
報告者:     XXXXX

■ 障害概要
- 発生日時:   2026-XX-XX XX:XX
- 復旧日時:   2026-XX-XX XX:XX
- 障害時間:   XX分
- 障害レベル: PX

■ 影響範囲
- 影響サービス: XXXXX
- 影響ユーザー数: XX名

■ 原因
- 直接原因: XXXXX
- 根本原因: XXXXX

■ 対応経緯
  XX:XX 障害検知
  XX:XX 一次対応開始
  XX:XX 原因特定
  XX:XX 復旧完了

■ 再発防止策
  1. XXXXX
  2. XXXXX

■ 教訓
  XXXXX
```

---

## 6. 定期訓練

### 6.1 障害対応訓練スケジュール

| 訓練種別 | 頻度 | 内容 |
|---------|------|------|
| 机上訓練 | 四半期 | 障害シナリオに基づく対応手順確認 |
| 実機訓練 | 半年 | テスト環境での障害発生・復旧訓練 |
| バックアップリストア訓練 | 四半期 | バックアップからのデータ復旧訓練 |
| エスカレーション訓練 | 半年 | 連絡体制・エスカレーション手順の確認 |

### 6.2 訓練シナリオ例

| シナリオ | 障害レベル | 概要 |
|---------|-----------|------|
| DBサーバー障害 | P1 | PostgreSQLコンテナ停止からの復旧 |
| API応答遅延 | P2 | バックエンドの性能劣化対応 |
| 通知システム障害 | P3 | Teams Webhook接続障害からの復旧 |
| データ復旧 | P1 | バックアップからのデータリストア |

---

*文書管理：本文書はバージョン管理対象。変更時はバージョン番号を更新すること。*
