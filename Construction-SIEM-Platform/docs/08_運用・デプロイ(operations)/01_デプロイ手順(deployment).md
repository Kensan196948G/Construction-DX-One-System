# 🚀 デプロイ手順

> Construction SIEM Platform のデプロイメントガイド

---

## 📋 目次

1. [前提条件](#前提条件)
2. [Docker Composeデプロイ](#docker-composeデプロイ)
3. [サービス一覧](#サービス一覧)
4. [環境変数設定](#環境変数設定)
5. [ヘルスチェック](#ヘルスチェック)
6. [ボリューム管理](#ボリューム管理)
7. [起動・停止手順](#起動停止手順)

---

## 📌 前提条件

| 項目 | 最低要件 | 推奨 |
|------|---------|------|
| Docker | 24.0+ | 最新安定版 |
| Docker Compose | v2.20+ | 最新安定版 |
| メモリ | 8GB | 16GB+ |
| ディスク | 20GB | 100GB+（ログ保存量による） |
| CPU | 4コア | 8コア+ |
| OS | Linux / macOS / WSL2 | Ubuntu 22.04+ |

---

## 🐳 Docker Composeデプロイ

### 基本デプロイコマンド

```bash
# 1. リポジトリクローン
git clone https://github.com/your-org/Construction-SIEM-Platform.git
cd Construction-SIEM-Platform

# 2. 環境変数設定
cp .env.example .env
# .env ファイルを編集して適切な値を設定

# 3. サービス起動
docker compose up -d

# 4. ログ確認
docker compose logs -f

# 5. ヘルスチェック
curl http://localhost:8000/health
```

### 段階的起動（推奨）

```bash
# Step 1: インフラ基盤
docker compose up -d zookeeper kafka elasticsearch

# Step 2: インフラ安定待ち（約30秒）
sleep 30

# Step 3: データパイプライン
docker compose up -d fluentd iot-edge

# Step 4: 分析エンジン
docker compose up -d rule-engine ml-detector

# Step 5: アプリケーション
docker compose up -d fastapi

# Step 6: 可視化ツール
docker compose up -d kibana grafana
```

---

## 📦 サービス一覧

| サービス名 | イメージ | ポート | 役割 | 依存関係 |
|-----------|---------|:------:|------|---------|
| 🦓 Zookeeper | `confluentinc/cp-zookeeper` | 2181 | Kafka管理 | なし |
| 📨 Kafka | `confluentinc/cp-kafka` | 9092 | メッセージブローカー | Zookeeper |
| 📝 Fluentd | カスタムビルド | 24224 | ログ収集 | Kafka |
| 📡 IoT Edge | カスタムビルド | - | IoTデータ取得 | Kafka |
| 🎯 Rule Engine | カスタムビルド | - | Sigmaルール照合 | Kafka, ES |
| 🤖 ML Detector | カスタムビルド | - | 異常検知 | Kafka, ES |
| 🔍 Elasticsearch | `elasticsearch:8.x` | 9200 | データストア・検索 | なし |
| 🌐 FastAPI | カスタムビルド | **8000** | APIサーバー | ES, Kafka |
| 📊 Kibana | `kibana:8.x` | 5601 | ログ可視化 | ES |
| 📈 Grafana | `grafana/grafana` | 3000 | メトリクス可視化 | ES |

### サービス間通信図

```
                    ┌──────────┐
                    │ Grafana  │:3000
                    └────┬─────┘
                         │
┌──────────┐        ┌────┴─────┐        ┌──────────┐
│  Kibana  │:5601 ──│ FastAPI  │:8000 ──│    ES    │:9200
└──────────┘        └────┬─────┘        └──────────┘
                         │                    ▲
                    ┌────┴─────┐              │
                    │  Kafka   │:9092 ────────┤
                    └────┬─────┘              │
                         │               ┌────┴─────┐
              ┌──────────┼──────────┐    │Rule Eng. │
              │          │          │    └──────────┘
         ┌────┴───┐ ┌───┴────┐ ┌───┴────┐
         │Fluentd │ │IoT Edge│ │ML Det. │
         └────────┘ └────────┘ └────────┘
              │
         ┌────┴─────┐
         │Zookeeper │:2181
         └──────────┘
```

---

## ⚙️ 環境変数設定

### `.env` ファイル設定項目

| 変数名 | デフォルト | 必須 | 説明 |
|--------|----------|:----:|------|
| `JWT_SECRET_KEY` | - | ✅ | JWT署名用秘密鍵 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | - | トークン有効期限 |
| `RATE_LIMIT_PER_MINUTE` | `100` | - | レート制限値 |
| `ELASTICSEARCH_URL` | `http://elasticsearch:9200` | - | ES接続先 |
| `KAFKA_BOOTSTRAP_SERVERS` | `kafka:9092` | - | Kafka接続先 |
| `ENVIRONMENT` | `development` | - | 実行環境 |
| `LOG_LEVEL` | `INFO` | - | ログレベル |
| `CORS_ORIGINS` | `*` | - | CORS許可オリジン |

### `.env.example`

```env
# === Security ===
JWT_SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=60
RATE_LIMIT_PER_MINUTE=100

# === Infrastructure ===
ELASTICSEARCH_URL=http://elasticsearch:9200
KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# === Application ===
ENVIRONMENT=development
LOG_LEVEL=INFO
CORS_ORIGINS=*

# === Elasticsearch ===
ES_JAVA_OPTS=-Xms512m -Xmx512m
discovery.type=single-node
xpack.security.enabled=false

# === Grafana ===
GF_SECURITY_ADMIN_PASSWORD=admin
```

> ⚠️ **重要**: 本番環境では必ず `JWT_SECRET_KEY` を強力なランダム文字列に変更してください。

---

## 🏥 ヘルスチェック

### 基本ヘルスチェック

```bash
# シンプルチェック
curl http://localhost:8000/health
```

レスポンス:

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-03-24T10:00:00Z"
}
```

### 詳細ヘルスチェック

```bash
# 全コンポーネントチェック
curl http://localhost:8000/health/detailed
```

レスポンス:

```json
{
  "status": "healthy",
  "components": {
    "elasticsearch": {
      "status": "healthy",
      "cluster_name": "construction-siem",
      "number_of_nodes": 1
    },
    "kafka": {
      "status": "healthy",
      "brokers": 1
    },
    "threat_intelligence": {
      "status": "healthy",
      "total_indicators": 1500
    }
  },
  "timestamp": "2026-03-24T10:00:00Z"
}
```

### 各サービスの個別チェック

| サービス | チェック方法 | 正常応答 |
|---------|-----------|---------|
| FastAPI | `curl localhost:8000/health` | `{"status": "healthy"}` |
| Elasticsearch | `curl localhost:9200/_cluster/health` | `{"status": "green"}` |
| Kafka | `docker compose exec kafka kafka-topics --list --bootstrap-server localhost:9092` | トピック一覧表示 |
| Kibana | `curl localhost:5601/api/status` | ステータスJSON |
| Grafana | `curl localhost:3000/api/health` | `{"database": "ok"}` |

---

## 💾 ボリューム管理

### 永続ボリューム

| ボリューム名 | マウント先 | 用途 | 推奨サイズ |
|-------------|----------|------|-----------|
| `elasticsearch-data` | `/usr/share/elasticsearch/data` | ESデータ永続化 | 50GB+ |
| `grafana-data` | `/var/lib/grafana` | Grafana設定永続化 | 1GB |
| `kafka-data` | `/var/lib/kafka/data` | Kafkaログ永続化 | 20GB |

### ボリューム操作

```bash
# ボリューム一覧
docker volume ls | grep construction-siem

# ボリューム使用量
docker system df -v

# ボリューム削除（⚠️ データ消失）
docker compose down -v
```

---

## 🔄 起動・停止手順

### 起動

```bash
# 全サービス起動
docker compose up -d

# 特定サービスのみ起動
docker compose up -d fastapi elasticsearch

# ビルド後起動（コード変更時）
docker compose up -d --build
```

### 停止

```bash
# 全サービス停止（データ保持）
docker compose down

# 全サービス停止 + ボリューム削除（⚠️ データ消失）
docker compose down -v

# 特定サービスのみ再起動
docker compose restart fastapi
```

### ログ確認

```bash
# 全サービスのログ（リアルタイム）
docker compose logs -f

# 特定サービスのログ
docker compose logs -f fastapi

# 最新100行のみ
docker compose logs --tail 100 fastapi
```

### スケーリング

```bash
# ワーカー数の増加（対応サービスのみ）
docker compose up -d --scale rule-engine=3

# 現在のサービス状態確認
docker compose ps
```
