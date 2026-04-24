# 💾 バックアップ・復旧

> Construction SIEM Platform のデータバックアップと復旧手順

---

## 📋 目次

1. [バックアップ戦略](#バックアップ戦略)
2. [Elasticsearchバックアップ](#elasticsearchバックアップ)
3. [ILMポリシー](#ilmポリシー)
4. [Kafkaログ保持](#kafkaログ保持)
5. [設定ファイル管理](#設定ファイル管理)
6. [復旧手順](#復旧手順)
7. [災害復旧計画](#災害復旧計画)

---

## 🎯 バックアップ戦略

### バックアップ対象と方針

| 対象 | 方式 | 頻度 | 保持期間 | 優先度 |
|------|------|:----:|:-------:|:------:|
| 🔍 Elasticsearch データ | スナップショットAPI | 日次 | 90日 | 🔴 高 |
| 📨 Kafka ログ | ログ保持設定 | 自動 | 7日 | 🟡 中 |
| ⚙️ 設定ファイル | Git管理 | 変更時 | 無期限 | 🔴 高 |
| 📊 Grafanaダッシュボード | JSON エクスポート | 週次 | 無期限 | 🟡 中 |
| 🔍 Kibanaダッシュボード | NDJSON エクスポート | 週次 | 無期限 | 🟡 中 |
| 🕵️ 脅威インテリジェンス | YAML/JSONエクスポート | 日次 | 30日 | 🔴 高 |

### バックアップ全体像

```
┌──────────────────────────────────────────┐
│          バックアップ対象                   │
├──────────┬──────────┬──────────┬─────────┤
│    ES    │  Kafka   │  設定    │ ダッシュ │
│  データ   │  ログ    │ ファイル │ ボード   │
├──────────┼──────────┼──────────┼─────────┤
│Snapshot  │ログ保持  │ Git     │JSON/    │
│  API     │  7日     │ 管理    │NDJSON   │
├──────────┼──────────┼──────────┼─────────┤
│  日次    │  自動    │ 変更時  │  週次   │
└──────────┴──────────┴──────────┴─────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│          バックアップ保存先                 │
│  ・ローカルストレージ（/backup/）           │
│  ・Azure Blob Storage（Phase 17で実装）   │
└──────────────────────────────────────────┘
```

---

## 🔍 Elasticsearchバックアップ

### スナップショットリポジトリ設定

```bash
# リポジトリ作成
curl -X PUT "localhost:9200/_snapshot/siem-backup" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "fs",
    "settings": {
      "location": "/backup/elasticsearch",
      "compress": true,
      "max_snapshot_bytes_per_sec": "50mb",
      "max_restore_bytes_per_sec": "50mb"
    }
  }'
```

### スナップショット作成

```bash
# 手動スナップショット
curl -X PUT "localhost:9200/_snapshot/siem-backup/snapshot-$(date +%Y%m%d)" \
  -H "Content-Type: application/json" \
  -d '{
    "indices": "siem-events-*,siem-alerts-*",
    "ignore_unavailable": true,
    "include_global_state": false
  }'
```

### スナップショット自動化（cron）

```bash
# /etc/cron.d/elasticsearch-backup
# 毎日午前2時にスナップショット作成
0 2 * * * root /opt/scripts/es-snapshot.sh

# 90日以上前のスナップショットを削除
0 3 * * * root /opt/scripts/es-snapshot-cleanup.sh 90
```

### バックアップスクリプト例

```bash
#!/bin/bash
# es-snapshot.sh
DATE=$(date +%Y%m%d-%H%M%S)
SNAPSHOT_NAME="snapshot-${DATE}"
ES_URL="http://localhost:9200"
REPO="siem-backup"

echo "[$(date)] Starting snapshot: ${SNAPSHOT_NAME}"

curl -s -X PUT "${ES_URL}/_snapshot/${REPO}/${SNAPSHOT_NAME}" \
  -H "Content-Type: application/json" \
  -d '{
    "indices": "siem-events-*,siem-alerts-*,siem-audit-*",
    "ignore_unavailable": true,
    "include_global_state": false
  }'

# 完了待ち
curl -s "${ES_URL}/_snapshot/${REPO}/${SNAPSHOT_NAME}/_status" | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['snapshots'][0]['state'])"

echo "[$(date)] Snapshot completed: ${SNAPSHOT_NAME}"
```

### スナップショット確認

```bash
# スナップショット一覧
curl -s "localhost:9200/_snapshot/siem-backup/_all" | python3 -m json.tool

# 特定スナップショットの詳細
curl -s "localhost:9200/_snapshot/siem-backup/snapshot-20260324" | python3 -m json.tool
```

---

## 📅 ILMポリシー

### ライフサイクル管理

```
Hot（7日間）→ Warm（30日間）→ Cold（90日間）→ Delete

┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐
│ Hot  │───►│ Warm │───►│ Cold │───►│Delete│
│ 7日  │    │ 30日 │    │ 90日 │    │      │
│      │    │      │    │      │    │      │
│高速  │    │中速  │    │低速  │    │削除  │
│SSD   │    │HDD   │    │圧縮  │    │      │
└──────┘    └──────┘    └──────┘    └──────┘
```

### ILMポリシー設定

```bash
curl -X PUT "localhost:9200/_ilm/policy/siem-lifecycle" \
  -H "Content-Type: application/json" \
  -d '{
    "policy": {
      "phases": {
        "hot": {
          "min_age": "0ms",
          "actions": {
            "rollover": {
              "max_age": "7d",
              "max_primary_shard_size": "50gb"
            },
            "set_priority": {
              "priority": 100
            }
          }
        },
        "warm": {
          "min_age": "7d",
          "actions": {
            "shrink": {
              "number_of_shards": 1
            },
            "forcemerge": {
              "max_num_segments": 1
            },
            "set_priority": {
              "priority": 50
            }
          }
        },
        "cold": {
          "min_age": "30d",
          "actions": {
            "set_priority": {
              "priority": 0
            },
            "freeze": {}
          }
        },
        "delete": {
          "min_age": "90d",
          "actions": {
            "delete": {}
          }
        }
      }
    }
  }'
```

### フェーズ別設定サマリー

| フェーズ | 期間 | アクション | ストレージ | 検索速度 |
|---------|:----:|-----------|:---------:|:--------:|
| 🔴 Hot | 0〜7日 | ロールオーバー | SSD（高速） | ⚡ 高速 |
| 🟠 Warm | 7〜30日 | シュリンク、マージ | HDD（標準） | 🔄 中速 |
| 🔵 Cold | 30〜90日 | フリーズ | HDD（圧縮） | 🐢 低速 |
| ⚫ Delete | 90日超 | 削除 | - | - |

---

## 📨 Kafkaログ保持

### 設定

| 項目 | 値 | 説明 |
|------|-----|------|
| `log.retention.hours` | `168`（7日） | ログ保持期間 |
| `log.retention.bytes` | `10737418240`（10GB） | トピック最大サイズ |
| `log.segment.bytes` | `1073741824`（1GB） | セグメントサイズ |
| `log.cleanup.policy` | `delete` | クリーンアップポリシー |

### トピック別保持設定

| トピック | 保持期間 | 用途 |
|---------|:-------:|------|
| `siem-events` | 7日 | 生イベント |
| `siem-alerts` | 30日 | アラート（長期保持） |
| `siem-audit` | 90日 | 監査ログ（コンプライアンス） |

```bash
# トピック別保持設定
kafka-configs --bootstrap-server kafka:9092 \
  --entity-type topics --entity-name siem-alerts \
  --alter --add-config retention.ms=2592000000  # 30日
```

---

## 📁 設定ファイル管理

### Git管理対象

| ファイル/ディレクトリ | 内容 |
|---------------------|------|
| `docker-compose.yml` | サービス定義 |
| `Dockerfile.*` | コンテナビルド定義 |
| `grafana/` | Grafana設定・ダッシュボード |
| `kibana/` | Kibana設定・ダッシュボード |
| `sigma_rules/` | Sigmaルール定義 |
| `threat_feeds/` | 脅威フィード定義 |
| `fluentd/` | Fluentd設定 |
| `.env.example` | 環境変数テンプレート |

### Git管理除外

| ファイル | 理由 |
|---------|------|
| `.env` | 機密情報を含む |
| `elasticsearch-data/` | 大容量データ |
| `*.log` | ログファイル |
| `__pycache__/` | キャッシュ |

---

## 🔄 復旧手順

### Elasticsearchデータ復旧

```bash
# 1. スナップショット一覧確認
curl -s "localhost:9200/_snapshot/siem-backup/_all" | python3 -m json.tool

# 2. 復元対象のスナップショット選択
SNAPSHOT="snapshot-20260324"

# 3. 既存インデックスのクローズ（必要時）
curl -X POST "localhost:9200/siem-events-*/_close"

# 4. スナップショットから復元
curl -X POST "localhost:9200/_snapshot/siem-backup/${SNAPSHOT}/_restore" \
  -H "Content-Type: application/json" \
  -d '{
    "indices": "siem-events-*,siem-alerts-*",
    "ignore_unavailable": true,
    "include_global_state": false
  }'

# 5. 復元状態確認
curl -s "localhost:9200/_recovery?active_only=true" | python3 -m json.tool

# 6. クラスター状態確認
curl -s "localhost:9200/_cluster/health" | python3 -m json.tool
```

### 全体復旧手順

```
1. インフラ復旧
   ├── Docker Compose 起動
   ├── Elasticsearch 起動確認
   └── Kafka 起動確認

2. データ復旧
   ├── ES スナップショット復元
   ├── TI フィード再ロード
   └── Sigmaルール確認

3. アプリケーション復旧
   ├── FastAPI 起動確認
   ├── /health/detailed で全コンポーネント確認
   └── テストイベント送信

4. 可視化復旧
   ├── Grafana ダッシュボード確認
   ├── Kibana インデックスパターン確認
   └── アラートルール確認

5. 復旧完了確認
   ├── 全ヘルスチェック OK
   ├── イベント収集再開確認
   └── アラート動作確認
```

---

## 🆘 災害復旧計画

### RPO/RTO目標

| 指標 | 目標 | 説明 |
|------|:----:|------|
| **RPO**（目標復旧時点） | 24時間 | 最大24時間分のデータ損失を許容 |
| **RTO**（目標復旧時間） | 4時間 | 4時間以内にサービス復旧 |

### 復旧優先順位

| 順位 | コンポーネント | RTO | 理由 |
|:----:|-------------|:---:|------|
| 1 | Elasticsearch | 1時間 | データストア（コア） |
| 2 | Kafka | 1時間 | メッセージング（コア） |
| 3 | FastAPI | 30分 | API機能 |
| 4 | Grafana | 2時間 | 監視・可視化 |
| 5 | Kibana | 2時間 | ログ検索 |

### 将来計画（Phase 17）

```
Phase 17: Azure Blob コールドストレージ
├── ESスナップショットをAzure Blobに自動転送
├── RPO を 1時間に短縮
├── 地理冗長性の確保
└── コスト最適化（Cold/Archive tier利用）
```
