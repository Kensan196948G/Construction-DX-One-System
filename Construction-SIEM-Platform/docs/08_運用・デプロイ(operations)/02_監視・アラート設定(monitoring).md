# 📊 監視・アラート設定

> Construction SIEM Platform の監視体制とアラート設定ガイド

---

## 📋 目次

1. [監視アーキテクチャ](#監視アーキテクチャ)
2. [Prometheusメトリクス](#prometheusメトリクス)
3. [Grafanaダッシュボード](#grafanaダッシュボード)
4. [Kibana可視化](#kibana可視化)
5. [詳細ヘルスチェック](#詳細ヘルスチェック)
6. [アラートルール](#アラートルール)

---

## 🏗 監視アーキテクチャ

```
┌─────────────────────────────────────────────────┐
│                  監視レイヤー                      │
│                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ Grafana  │  │  Kibana  │  │Prometheus│      │
│  │ (メトリ  │  │ (ログ    │  │ (収集)   │      │
│  │  クス)   │  │  検索)   │  │          │      │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘      │
│       │              │              │            │
│       └──────────────┼──────────────┘            │
│                      │                           │
├──────────────────────┼───────────────────────────┤
│                      │                           │
│  ┌──────────┐  ┌─────┴────┐  ┌──────────┐      │
│  │ FastAPI  │  │   ES     │  │  Kafka   │      │
│  │ /metrics │  │          │  │          │      │
│  │ /health  │  │          │  │          │      │
│  └──────────┘  └──────────┘  └──────────┘      │
│                                                 │
│                アプリケーションレイヤー              │
└─────────────────────────────────────────────────┘
```

---

## 📈 Prometheusメトリクス

### エンドポイント

| パス | 説明 | 認証 |
|------|------|:----:|
| `/metrics` | Prometheusメトリクス | 不要 |

### 公開メトリクス

| メトリクス名 | タイプ | 説明 |
|-------------|--------|------|
| `http_requests_total` | Counter | HTTPリクエスト総数（method, path, status別） |
| `http_request_duration_seconds` | Histogram | リクエスト処理時間 |
| `http_requests_in_progress` | Gauge | 処理中リクエスト数 |
| `siem_events_total` | Counter | 受信イベント総数 |
| `siem_alerts_total` | Counter | 生成アラート総数（severity別） |
| `siem_sigma_matches_total` | Counter | Sigmaルールマッチ数 |
| `siem_ml_anomalies_total` | Counter | ML異常検知数 |
| `siem_ioc_matches_total` | Counter | IoC照合マッチ数 |
| `siem_playbook_executions_total` | Counter | プレイブック実行数 |
| `elasticsearch_health` | Gauge | ESクラスター状態（1=green, 0.5=yellow, 0=red） |
| `kafka_consumer_lag` | Gauge | Kafkaコンシューマーラグ |

### Prometheus設定例

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'construction-siem'
    static_configs:
      - targets: ['fastapi:8000']
    metrics_path: /metrics
    scrape_interval: 10s
```

---

## 📊 Grafanaダッシュボード

### ダッシュボード一覧

| ダッシュボード | ファイル | 内容 |
|--------------|---------|------|
| 🏠 SIEM概要 | `grafana/dashboards/siem-overview.json` | 全体KPI、イベント数、アラート数 |
| 🎯 検知ダッシュボード | `grafana/dashboards/detection.json` | Sigma/ML/IoC検知状況 |
| 🏗 建設現場モニター | `grafana/dashboards/construction-site.json` | 現場別セキュリティ状況 |
| ⚙️ インフラ監視 | `grafana/dashboards/infrastructure.json` | ES/Kafka/APIパフォーマンス |
| 📋 コンプライアンス | `grafana/dashboards/compliance.json` | コンプライアンススコア推移 |

### SIEM概要ダッシュボードのパネル

```
┌─────────────────────────────────────────────────┐
│  📊 Construction SIEM - 概要ダッシュボード        │
├────────┬────────┬────────┬────────┬──────────────┤
│イベント │アラート │ MTTD  │ MTTR  │コンプライアンス│
│ 15,234 │   42   │ 12min │ 1.5h  │    92%       │
├────────┴────────┴────────┴────────┴──────────────┤
│                                                 │
│  📈 イベント数推移（24時間）                       │
│  ▃▄▆█▇▅▃▂▃▄▅▆▇█▇▆▅▄▃▃▄▅▆                      │
│                                                 │
├─────────────────────┬───────────────────────────┤
│  🎯 Severity分布    │  🏗 現場別アラート          │
│  ■ Critical: 3     │  現場A: ████░░ 12         │
│  ■ High: 12        │  現場B: ██░░░░  6         │
│  ■ Medium: 18      │  現場C: █░░░░░  3         │
│  ■ Low: 9          │  本社:  ████████ 21       │
├─────────────────────┴───────────────────────────┤
│  📋 最新アラート一覧                               │
│  10:30 [P2] IoTデバイス不正アクセス - 現場A        │
│  10:15 [P3] 大量ログイン失敗 - 本社               │
│  09:45 [P4] ポートスキャン検知 - 現場B             │
└─────────────────────────────────────────────────┘
```

### Grafanaプロビジョニング

```
grafana/
├── provisioning/
│   ├── datasources/
│   │   └── datasource.yml      # Elasticsearch, Prometheus
│   ├── dashboards/
│   │   └── dashboard.yml       # ダッシュボード自動読み込み
│   └── alerting/
│       └── alert-rules.yml     # アラートルール
└── dashboards/
    ├── siem-overview.json
    ├── detection.json
    ├── construction-site.json
    ├── infrastructure.json
    └── compliance.json
```

### データソース設定

```yaml
# grafana/provisioning/datasources/datasource.yml
apiVersion: 1
datasources:
  - name: Elasticsearch
    type: elasticsearch
    url: http://elasticsearch:9200
    database: "siem-events-*"
    jsonData:
      timeField: "@timestamp"
      esVersion: "8.0.0"

  - name: Prometheus
    type: prometheus
    url: http://prometheus:9090
    isDefault: true
```

---

## 🔍 Kibana可視化

### アクセス

| 項目 | 値 |
|------|-----|
| URL | `http://localhost:5601` |
| インデックスパターン | `siem-events-*` |
| タイムフィールド | `@timestamp` |

### ダッシュボード一覧

| ダッシュボード | ファイル | 用途 |
|--------------|---------|------|
| 🔍 イベント検索 | `kibana/dashboards/event-search.ndjson` | ログの全文検索・フィルタリング |
| 📊 イベント分析 | `kibana/dashboards/event-analysis.ndjson` | イベントの統計分析 |
| 🎯 アラート管理 | `kibana/dashboards/alert-management.ndjson` | アラートの一覧・管理 |
| 🕵️ 脅威ハンティング | `kibana/dashboards/threat-hunting.ndjson` | 手動脅威調査 |

### Kibanaダッシュボードインポート

```bash
# ダッシュボードのインポート
curl -X POST "http://localhost:5601/api/saved_objects/_import" \
  -H "kbn-xsrf: true" \
  --form file=@kibana/dashboards/event-search.ndjson
```

---

## 🏥 詳細ヘルスチェック

### エンドポイント: `/health/detailed`

各コンポーネントの詳細な状態を返します。

| コンポーネント | チェック内容 | 正常条件 |
|--------------|------------|---------|
| 🔍 Elasticsearch | クラスター接続 | `status: green/yellow` |
| 📨 Kafka | ブローカー接続 | ブローカー数 > 0 |
| 🕵️ Threat Intelligence | IoC数確認 | `total_indicators > 0` |
| 🎯 Rule Engine | ルール数確認 | `loaded_rules > 0` |
| 🤖 ML Detector | モデル状態 | `model_loaded: true` |

### 監視スクリプト例

```bash
#!/bin/bash
# health-monitor.sh - 定期ヘルスチェックスクリプト

ENDPOINT="http://localhost:8000/health/detailed"
INTERVAL=60  # 60秒間隔

while true; do
  RESPONSE=$(curl -s -w "%{http_code}" "$ENDPOINT")
  HTTP_CODE="${RESPONSE: -3}"

  if [ "$HTTP_CODE" != "200" ]; then
    echo "[ALERT] Health check failed: HTTP $HTTP_CODE"
    # 通知処理を追加
  fi

  sleep $INTERVAL
done
```

---

## 🔔 アラートルール

### Grafanaアラートルール

| ルール名 | 条件 | 重要度 | 通知先 |
|---------|------|:------:|--------|
| 🔴 ES接続断 | ES health = red | Critical | Webhook + Email |
| 🔴 API応答なし | /health 5分連続失敗 | Critical | Webhook + Email |
| 🟠 高severityアラート | severity >= 8 が5分間に3件以上 | High | Webhook |
| 🟠 Kafkaラグ増大 | consumer_lag > 10000 | High | Webhook |
| 🟡 レート制限超過 | 429エラー率 > 10% | Medium | Webhook |
| 🟡 ディスク使用率 | > 80% | Medium | Email |
| 🟢 ML異常検知数増加 | 通常の3倍以上 | Low | ログのみ |

### アラートルール設定例

```yaml
# grafana/provisioning/alerting/alert-rules.yml
apiVersion: 1
groups:
  - orgId: 1
    name: SIEM Critical Alerts
    folder: SIEM
    interval: 1m
    rules:
      - uid: es-connection-alert
        title: "Elasticsearch接続断"
        condition: C
        data:
          - refId: A
            queryType: prometheus
            model:
              expr: elasticsearch_health == 0
        for: 2m
        annotations:
          summary: "Elasticsearchとの接続が切断されました"
        labels:
          severity: critical

      - uid: high-severity-alert
        title: "高Severityアラート多発"
        condition: C
        data:
          - refId: A
            queryType: prometheus
            model:
              expr: rate(siem_alerts_total{severity="critical"}[5m]) > 0.01
        for: 5m
        annotations:
          summary: "高Severityアラートが短期間に多発しています"
        labels:
          severity: high
```

### 通知チャネル設定

| チャネル | 用途 | 設定 |
|---------|------|------|
| 📧 Email | P1/P2通知 | SMTP設定 |
| 💬 Webhook | 全アラート | Teams/Slack URL |
| 📱 PagerDuty | P1のみ | Integration Key |
| 📝 ログ | 全イベント | ファイル出力 |
