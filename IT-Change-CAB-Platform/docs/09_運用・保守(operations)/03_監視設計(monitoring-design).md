# 監視設計書
## IT変更管理・リリース自動化プラットフォーム（IT-Change-CAB-Platform）

| 項目 | 内容 |
|------|------|
| **文書番号** | OPS-CAB-003 |
| **バージョン** | 1.0.0 |
| **作成日** | 2026-03-26 |
| **作成者** | みらい建設工業 IT部門 |
| **対象リポジトリ** | Kensan196948G/IT-Change-CAB-Platform |

---

## 1. 監視設計概要

### 1.1 目的

本プラットフォームの安定稼働（稼働率99.5%以上）を維持するため、ヘルスチェック・メトリクス収集・ログ管理・アラート通知の監視基盤を設計する。

### 1.2 監視アーキテクチャ

```
┌─────────────────────────────────────────────────────┐
│                   監視ダッシュボード                    │
│              Grafana (http://localhost:3001)          │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                  データソース                          │
│  ┌────────────┐  ┌──────────┐  ┌─────────────────┐  │
│  │ Prometheus │  │  Loki    │  │ PostgreSQL      │  │
│  │ メトリクス  │  │  ログ    │  │ アプリケーション  │  │
│  └──────┬─────┘  └────┬─────┘  └────────┬────────┘  │
└─────────┼─────────────┼────────────────┼───────────┘
          │             │                │
┌─────────▼─────────────▼────────────────▼───────────┐
│                 データ収集層                          │
│  ┌──────────────┐  ┌───────────┐  ┌────────────┐   │
│  │ Node Exporter│  │ Promtail  │  │ pg_exporter│   │
│  │ cAdvisor     │  │           │  │            │   │
│  └──────┬───────┘  └─────┬─────┘  └──────┬─────┘   │
└─────────┼────────────────┼───────────────┼─────────┘
          │                │               │
┌─────────▼────────────────▼───────────────▼─────────┐
│              監視対象システム                          │
│  Backend / Frontend / PostgreSQL / Redis / Worker   │
└─────────────────────────────────────────────────────┘
```

### 1.3 監視ツール一覧

| ツール | 用途 | バージョン |
|-------|------|-----------|
| Prometheus | メトリクス収集・保存・アラート | 2.x |
| Grafana | 可視化ダッシュボード | 10.x |
| Loki | ログ集約・検索 | 2.x |
| Promtail | ログ収集エージェント | 2.x |
| cAdvisor | コンテナリソース監視 | 0.47.x |
| Node Exporter | ホストマシンメトリクス | 1.x |
| postgres_exporter | PostgreSQLメトリクス | 0.15.x |
| redis_exporter | Redisメトリクス | 1.x |
| AlertManager | アラート管理・通知 | 0.27.x |

---

## 2. ヘルスチェック

### 2.1 ヘルスチェックエンドポイント

#### バックエンドAPI ヘルスチェック

**エンドポイント:** `GET /api/v1/health`

**レスポンス例:**
```json
{
  "status": "healthy",
  "timestamp": "2026-03-26T09:00:00.000Z",
  "version": "1.0.0",
  "uptime": 86400,
  "checks": {
    "database": {
      "status": "healthy",
      "responseTime": 5
    },
    "redis": {
      "status": "healthy",
      "responseTime": 2
    },
    "bullmq": {
      "status": "healthy",
      "activeJobs": 3,
      "waitingJobs": 12
    }
  }
}
```

#### 詳細ヘルスチェック

**エンドポイント:** `GET /api/v1/health/detailed`（管理者認証必要）

```json
{
  "status": "healthy",
  "checks": {
    "database": {
      "status": "healthy",
      "responseTime": 5,
      "activeConnections": 8,
      "maxConnections": 100,
      "version": "16.2"
    },
    "redis": {
      "status": "healthy",
      "responseTime": 2,
      "usedMemory": "15MB",
      "maxMemory": "256MB",
      "connectedClients": 5
    },
    "bullmq": {
      "status": "healthy",
      "queues": {
        "notification": { "active": 2, "waiting": 5, "failed": 0 },
        "cab-reminder": { "active": 0, "waiting": 1, "failed": 0 },
        "report-generation": { "active": 1, "waiting": 3, "failed": 0 }
      }
    },
    "disk": {
      "status": "healthy",
      "usedPercent": 45,
      "freeGB": 28.5
    }
  }
}
```

### 2.2 Docker ヘルスチェック設定

```yaml
# docker-compose.yml ヘルスチェック設定
services:
  backend:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  db:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U admin -d cab_platform"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 5s
      retries: 3

  frontend:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 60s
      timeout: 10s
      retries: 3
```

---

## 3. メトリクス設計

### 3.1 アプリケーションメトリクス

| メトリクス名 | 型 | 説明 | ラベル |
|-------------|---|------|--------|
| `http_requests_total` | Counter | HTTPリクエスト総数 | method, path, status |
| `http_request_duration_seconds` | Histogram | HTTPリクエスト応答時間 | method, path |
| `http_requests_in_flight` | Gauge | 処理中リクエスト数 | - |
| `rfc_created_total` | Counter | RFC作成数 | change_type |
| `rfc_approved_total` | Counter | RFC承認数 | change_type |
| `rfc_rejected_total` | Counter | RFC却下数 | change_type |
| `rfc_rollback_total` | Counter | ロールバック数 | change_type |
| `cab_decision_duration_seconds` | Histogram | CAB承認リードタイム | decision |
| `notification_sent_total` | Counter | 通知送信数 | type, channel |
| `notification_failed_total` | Counter | 通知送信失敗数 | type, channel |
| `conflict_detected_total` | Counter | 衝突検知数 | type |

### 3.2 インフラメトリクス

| メトリクス名 | 型 | 説明 | 収集元 |
|-------------|---|------|--------|
| `node_cpu_seconds_total` | Counter | CPU使用時間 | Node Exporter |
| `node_memory_MemAvailable_bytes` | Gauge | 利用可能メモリ | Node Exporter |
| `node_filesystem_avail_bytes` | Gauge | 利用可能ディスク容量 | Node Exporter |
| `container_cpu_usage_seconds_total` | Counter | コンテナCPU使用時間 | cAdvisor |
| `container_memory_usage_bytes` | Gauge | コンテナメモリ使用量 | cAdvisor |
| `container_network_receive_bytes_total` | Counter | コンテナネットワーク受信量 | cAdvisor |

### 3.3 データベースメトリクス

| メトリクス名 | 説明 | 収集元 |
|-------------|------|--------|
| `pg_stat_activity_count` | アクティブ接続数 | postgres_exporter |
| `pg_stat_database_blks_hit` | キャッシュヒット数 | postgres_exporter |
| `pg_stat_database_tup_returned` | 返却行数 | postgres_exporter |
| `pg_stat_database_deadlocks` | デッドロック数 | postgres_exporter |
| `pg_stat_user_tables_seq_scan` | シーケンシャルスキャン数 | postgres_exporter |
| `pg_database_size_bytes` | データベースサイズ | postgres_exporter |
| `pg_stat_replication_lag` | レプリケーション遅延 | postgres_exporter |

### 3.4 Redisメトリクス

| メトリクス名 | 説明 | 収集元 |
|-------------|------|--------|
| `redis_connected_clients` | 接続クライアント数 | redis_exporter |
| `redis_used_memory_bytes` | メモリ使用量 | redis_exporter |
| `redis_keyspace_hits_total` | キャッシュヒット数 | redis_exporter |
| `redis_keyspace_misses_total` | キャッシュミス数 | redis_exporter |
| `redis_commands_processed_total` | 処理コマンド数 | redis_exporter |

### 3.5 Prometheusメトリクス収集設定

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/api/v1/metrics'

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

rule_files:
  - 'alerts/*.yml'

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']
```

---

## 4. アラートルール

### 4.1 アプリケーションアラート

```yaml
# alerts/application.yml
groups:
  - name: application
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.01
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "高エラー率検知 ({{ $value | humanizePercentage }})"
          description: "5xxエラー率が1%を超過しています"

      - alert: SlowAPIResponse
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API応答遅延 (p95: {{ $value }}s)"
          description: "API応答時間のp95が2秒を超過しています"

      - alert: HighNotificationFailRate
        expr: rate(notification_failed_total[10m]) > 0
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "通知送信失敗発生"

      - alert: ServiceDown
        expr: up{job="backend"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "バックエンドサービス停止"
```

### 4.2 インフラアラート

```yaml
# alerts/infrastructure.yml
groups:
  - name: infrastructure
    rules:
      - alert: HighCPUUsage
        expr: 100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 70
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "CPU使用率高 ({{ $value }}%)"

      - alert: CriticalCPUUsage
        expr: 100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 90
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "CPU使用率危険 ({{ $value }}%)"

      - alert: HighMemoryUsage
        expr: (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100 > 80
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "メモリ使用率高 ({{ $value }}%)"

      - alert: DiskSpaceLow
        expr: (1 - node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100 > 85
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "ディスク容量不足 (使用率: {{ $value }}%)"
```

### 4.3 データベースアラート

```yaml
# alerts/database.yml
groups:
  - name: database
    rules:
      - alert: PostgreSQLDown
        expr: pg_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "PostgreSQL停止"

      - alert: HighDBConnections
        expr: pg_stat_activity_count / pg_settings_max_connections * 100 > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "DB接続数高 ({{ $value }}%)"

      - alert: DeadlockDetected
        expr: increase(pg_stat_database_deadlocks[5m]) > 0
        labels:
          severity: warning
        annotations:
          summary: "デッドロック検知"

      - alert: LowCacheHitRate
        expr: pg_stat_database_blks_hit / (pg_stat_database_blks_hit + pg_stat_database_blks_read) < 0.95
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "DBキャッシュヒット率低下 ({{ $value | humanizePercentage }})"
```

### 4.4 Redisアラート

```yaml
# alerts/redis.yml
groups:
  - name: redis
    rules:
      - alert: RedisDown
        expr: redis_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Redis停止"

      - alert: HighRedisMemory
        expr: redis_used_memory_bytes / redis_config_maxmemory * 100 > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Redisメモリ使用率高 ({{ $value }}%)"
```

---

## 5. ログ管理

### 5.1 ログレベル定義

| レベル | 用途 | 例 |
|-------|------|-----|
| ERROR | アプリケーションエラー、例外 | DB接続失敗、API処理エラー |
| WARN | 警告、潜在的な問題 | 遅いクエリ、リトライ発生 |
| INFO | 通常の処理記録 | RFC作成、CAB承認、ログイン |
| DEBUG | デバッグ情報（開発環境のみ） | クエリ内容、変数値 |

### 5.2 ログフォーマット

```json
{
  "timestamp": "2026-03-26T09:15:30.123Z",
  "level": "INFO",
  "service": "backend",
  "traceId": "abc123def456",
  "userId": "user-uuid-001",
  "action": "rfc.create",
  "message": "RFC作成完了",
  "metadata": {
    "rfcNumber": "RFC-2026-042",
    "changeType": "normal",
    "targetSystems": ["ActiveDirectory"]
  },
  "duration": 145
}
```

### 5.3 監査ログ

| イベント | 記録内容 | 保持期間 |
|---------|---------|---------|
| ログイン/ログアウト | ユーザーID、IP、日時、成功/失敗 | 1年 |
| RFC操作（作成/編集/削除） | 操作者、RFC番号、変更内容 | 3年 |
| CAB承認/却下 | 承認者、RFC番号、判定、理由 | 3年 |
| ユーザー管理操作 | 操作者、対象ユーザー、操作内容 | 1年 |
| システム設定変更 | 操作者、変更項目、変更前後の値 | 1年 |
| フリーズ期間設定 | 操作者、期間、対象変更種別 | 1年 |

### 5.4 Loki ログ収集設定

```yaml
# promtail-config.yml
server:
  http_listen_port: 9080

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        target_label: 'container'
      - source_labels: ['__meta_docker_container_log_stream']
        target_label: 'stream'
    pipeline_stages:
      - json:
          expressions:
            level: level
            service: service
            traceId: traceId
      - labels:
          level:
          service:
```

---

## 6. ダッシュボード設計

### 6.1 ダッシュボード一覧

| ダッシュボード名 | 対象 | 主要パネル |
|---------------|------|-----------|
| システム概要 | 運用チーム全員 | サービス稼働状況、エラー率、応答時間 |
| インフラ詳細 | システム管理者 | CPU/メモリ/ディスク、コンテナリソース |
| アプリケーション詳細 | アプリ管理者 | API応答時間、RFC処理数、通知状況 |
| データベース | DB管理者 | 接続数、クエリ性能、キャッシュヒット率 |
| ビジネスKPI | 運用責任者 | 変更成功率、承認リードタイム、変更件数推移 |

### 6.2 システム概要ダッシュボード

| パネル名 | 表示内容 | 可視化タイプ |
|---------|---------|------------|
| サービス稼働状況 | 各サービスのUp/Down | ステータスマップ |
| エラー率推移 | 5xxエラー率（5分間隔） | 折れ線グラフ |
| 応答時間推移 | p50/p90/p95/p99 | 折れ線グラフ |
| リクエスト数 | RPS推移 | 折れ線グラフ |
| アクティブユーザー数 | 同時接続ユーザー | 数値ゲージ |
| 直近のアラート | アクティブアラート一覧 | テーブル |
| CPU/メモリ概要 | 各コンテナのリソース使用率 | 棒グラフ |
| ディスク使用率 | 全マウントポイント | ゲージ |

### 6.3 アプリケーション詳細ダッシュボード

| パネル名 | 表示内容 | 可視化タイプ |
|---------|---------|------------|
| RFC作成数推移 | 日別RFC作成数（種別別） | 積み上げ棒グラフ |
| RFC承認/却下推移 | 日別承認・却下数 | 積み上げ棒グラフ |
| 承認リードタイム | 提出～承認の所要時間分布 | ヒストグラム |
| 通知送信状況 | 送信成功/失敗数 | 折れ線グラフ |
| キュー処理状況 | BullMQキュー長推移 | 折れ線グラフ |
| API別応答時間 | エンドポイント別p95 | テーブル（ヒートマップ） |
| エラーログ | 直近のエラーログ一覧 | テーブル |

---

## 7. アラート通知設定

### 7.1 通知チャネル

| チャネル | 対象アラート | 設定 |
|---------|------------|------|
| Teams（CAB-Platform-Ops） | 全アラート | Webhook URL |
| メール | Critical アラート | SMTP設定 |
| 電話（PagerDuty等） | P1 障害 | インテグレーション設定 |

### 7.2 AlertManager設定

```yaml
# alertmanager.yml
global:
  resolve_timeout: 5m

route:
  receiver: 'teams-ops'
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  routes:
    - match:
        severity: critical
      receiver: 'teams-critical'
      repeat_interval: 1h
    - match:
        severity: warning
      receiver: 'teams-ops'

receivers:
  - name: 'teams-ops'
    webhook_configs:
      - url: 'http://teams-webhook-proxy:8089/webhook'
        send_resolved: true

  - name: 'teams-critical'
    webhook_configs:
      - url: 'http://teams-webhook-proxy:8089/webhook'
        send_resolved: true
    email_configs:
      - to: 'it-ops@mirai-kensetsu.co.jp'
        from: 'cab-platform-alert@mirai-kensetsu.co.jp'
        smarthost: 'smtp.office365.com:587'
        auth_username: '{{ .ExternalURL }}'
        require_tls: true
```

---

## 8. 監視基盤 Docker Compose

```yaml
# docker-compose.monitoring.yml
version: '3.9'

services:
  prometheus:
    image: prom/prometheus:v2.50.0
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./monitoring/alerts:/etc/prometheus/alerts
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=30d'

  grafana:
    image: grafana/grafana:10.3.0
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    ports:
      - "3001:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_ADMIN_PASSWORD}

  loki:
    image: grafana/loki:2.9.0
    volumes:
      - loki_data:/loki
    ports:
      - "3100:3100"

  promtail:
    image: grafana/promtail:2.9.0
    volumes:
      - ./monitoring/promtail-config.yml:/etc/promtail/config.yml
      - /var/run/docker.sock:/var/run/docker.sock
      - /var/lib/docker/containers:/var/lib/docker/containers:ro

  alertmanager:
    image: prom/alertmanager:v0.27.0
    volumes:
      - ./monitoring/alertmanager.yml:/etc/alertmanager/alertmanager.yml
    ports:
      - "9093:9093"

  node-exporter:
    image: prom/node-exporter:v1.7.0
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro

  cadvisor:
    image: gcr.io/cadvisor/cadvisor:v0.47.0
    ports:
      - "8080:8080"
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro

  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:v0.15.0
    environment:
      DATA_SOURCE_NAME: "postgresql://admin:${DB_PASSWORD}@db:5432/cab_platform?sslmode=disable"
    ports:
      - "9187:9187"

  redis-exporter:
    image: oliver006/redis_exporter:v1.55.0
    environment:
      REDIS_ADDR: "redis://redis:6379"
    ports:
      - "9121:9121"

volumes:
  prometheus_data:
  grafana_data:
  loki_data:
```

---

## 9. SLA監視

### 9.1 SLA指標

| SLA指標 | 目標値 | 測定方法 | 報告頻度 |
|---------|--------|---------|---------|
| 稼働率 | 99.5%以上 | ヘルスチェック成功率から算出 | 月次 |
| API応答時間 | p95 < 2秒 | Prometheusメトリクス | 日次 |
| 計画外停止時間 | 月間3.6時間以下 | 障害チケットから集計 | 月次 |
| 通知送信成功率 | 99%以上 | 通知送信メトリクス | 週次 |

### 9.2 稼働率計算

```
月間稼働率 = (月間総時間 - 計画外停止時間) / 月間総時間 * 100

例: 月間720時間 - 計画外停止1時間 = 719 / 720 * 100 = 99.86%

目標: 99.5% → 月間許容停止時間: 720 * 0.005 = 3.6時間
```

---

*文書管理：本文書はバージョン管理対象。変更時はバージョン番号を更新すること。*
