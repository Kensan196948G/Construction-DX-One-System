# 🛠 開発環境セットアップ（Setup）

> Construction SIEM Platform のローカル開発環境構築手順

---

## 📋 前提条件

| ツール | バージョン | 確認コマンド |
|--------|-----------|-------------|
| 🐳 Docker | 24.0 以上 | `docker --version` |
| 🐳 Docker Compose | v2.20 以上 | `docker compose version` |
| 🐍 Python | 3.12 以上 | `python3 --version` |
| 📦 pip | 最新推奨 | `pip --version` |
| 🔀 Git | 2.40 以上 | `git --version` |
| 📝 エディタ | VS Code 推奨 | - |

---

## 🚀 セットアップ手順

### Step 1: リポジトリクローン

```bash
git clone https://github.com/your-org/Construction-SIEM-Platform.git
cd Construction-SIEM-Platform
```

### Step 2: 環境変数設定

```bash
cp .env.example .env
```

`.env` ファイルを編集し、必要な値を設定してください（詳細は後述の環境変数一覧を参照）。

### Step 3: Python 仮想環境の作成

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# Windows: venv\Scripts\activate
```

### Step 4: 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### Step 5: Docker コンテナの起動

```bash
docker compose up -d
```

以下のサービスが起動します。

| サービス | ポート | 説明 |
|----------|:-----:|------|
| 🔍 Elasticsearch | 9200 | ログストレージ |
| 📊 Kibana | 5601 | ダッシュボード |
| 📨 Kafka | 9092 | メッセージブローカー |
| 🗄 Zookeeper | 2181 | Kafka 管理 |
| 📈 Prometheus | 9090 | メトリクス収集 |
| 📉 Grafana | 3000 | 可視化 |

### Step 6: テスト実行確認

```bash
pytest tests/ -v --tb=short
```

期待結果: **210テスト全て PASSED**

### Step 7: FastAPI サーバー起動

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

| URL | 説明 |
|-----|------|
| http://localhost:8000 | API ルート |
| http://localhost:8000/api/docs | Swagger UI |
| http://localhost:8000/api/redoc | ReDoc |
| http://localhost:8000/health | ヘルスチェック |

---

## ✅ 動作確認チェックリスト

| # | 確認項目 | コマンド/URL | 期待結果 |
|:-:|---------|-------------|---------|
| 1 | Docker起動 | `docker compose ps` | 全サービス running |
| 2 | Elasticsearch | `curl localhost:9200` | JSON レスポンス |
| 3 | テスト | `pytest tests/ -v` | 210 passed |
| 4 | FastAPI | `curl localhost:8000/health` | `{"status": "healthy"}` |
| 5 | Swagger UI | http://localhost:8000/api/docs | UI 表示 |

---

## 📝 環境変数一覧（.env.example）

### 🔐 認証・セキュリティ

| 変数名 | デフォルト値 | 説明 |
|--------|------------|------|
| `SECRET_KEY` | `change-me-in-production` | JWT署名キー（本番は必ず変更） |
| `JWT_ALGORITHM` | `HS256` | JWTアルゴリズム |
| `JWT_EXPIRATION` | `1800` | トークン有効期限（秒） |
| `ADMIN_USERNAME` | `admin` | 初期管理者ユーザー名 |
| `ADMIN_PASSWORD` | `admin` | 初期管理者パスワード（本番は必ず変更） |

### 🔍 Elasticsearch

| 変数名 | デフォルト値 | 説明 |
|--------|------------|------|
| `ELASTICSEARCH_URL` | `http://localhost:9200` | Elasticsearch 接続URL |
| `ELASTICSEARCH_INDEX_PREFIX` | `siem` | インデックスプレフィックス |
| `ELASTICSEARCH_USERNAME` | `` | ES認証ユーザー名（任意） |
| `ELASTICSEARCH_PASSWORD` | `` | ES認証パスワード（任意） |

### 📨 Kafka

| 変数名 | デフォルト値 | 説明 |
|--------|------------|------|
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Kafkaブローカーアドレス |
| `KAFKA_TOPIC_ALERTS` | `siem-alerts` | アラートトピック |
| `KAFKA_TOPIC_LOGS` | `siem-logs` | ログトピック |
| `KAFKA_CONSUMER_GROUP` | `siem-consumer` | コンシューマーグループ |

### 📈 モニタリング

| 変数名 | デフォルト値 | 説明 |
|--------|------------|------|
| `PROMETHEUS_PORT` | `9090` | Prometheusポート |
| `GRAFANA_PORT` | `3000` | Grafanaポート |
| `METRICS_ENABLED` | `true` | メトリクス収集の有効化 |

### 🔔 通知

| 変数名 | デフォルト値 | 説明 |
|--------|------------|------|
| `TEAMS_WEBHOOK_URL` | `` | Microsoft Teams Webhook URL |
| `SLACK_WEBHOOK_URL` | `` | Slack Webhook URL |
| `CUSTOM_WEBHOOK_URL` | `` | カスタム Webhook URL |
| `NOTIFICATION_ENABLED` | `true` | 通知送信の有効化 |

### ⚙ アプリケーション

| 変数名 | デフォルト値 | 説明 |
|--------|------------|------|
| `APP_ENV` | `development` | 環境（development/staging/production） |
| `APP_DEBUG` | `true` | デバッグモード |
| `APP_PORT` | `8000` | APIサーバーポート |
| `LOG_LEVEL` | `INFO` | ログレベル（DEBUG/INFO/WARNING/ERROR） |
| `RATE_LIMIT_PER_MINUTE` | `100` | レート制限（リクエスト/分） |

### 📊 KPI・SLA

| 変数名 | デフォルト値 | 説明 |
|--------|------------|------|
| `MTTD_TARGET_MINUTES` | `5` | MTTD目標（分） |
| `MTTR_TARGET_MINUTES` | `60` | MTTR目標（分） |
| `SLA_COMPLIANCE_TARGET` | `95` | SLA遵守率目標（%） |

---

## 🔧 トラブルシューティング

### Docker コンテナが起動しない

```bash
# ログ確認
docker compose logs -f

# コンテナ再作成
docker compose down
docker compose up -d --build
```

### Elasticsearch 接続エラー

```bash
# ヘルスチェック
curl -s localhost:9200/_cluster/health | python3 -m json.tool

# メモリ不足の場合
# docker-compose.yml の ES_JAVA_OPTS を調整
# ES_JAVA_OPTS: "-Xms512m -Xmx512m"
```

### テスト失敗

```bash
# 個別テスト実行
pytest tests/test_api.py -v --tb=long

# カバレッジ付き
pytest tests/ --cov=api --cov-report=html
```

### ポート競合

```bash
# 使用中のポート確認
lsof -i :8000
lsof -i :9200

# プロセス停止後に再起動
```

---

## 📂 プロジェクト構造

```
Construction-SIEM-Platform/
├── api/                    # FastAPI アプリケーション
│   ├── main.py            # エントリーポイント
│   ├── auth.py            # 認証・JWT
│   ├── models.py          # Pydantic モデル
│   └── routes/            # ルートハンドラ
├── tests/                  # テストスイート
│   ├── test_api.py
│   ├── test_auth.py
│   └── ...
├── docker-compose.yml      # Docker構成
├── Dockerfile             # コンテナイメージ
├── requirements.txt       # Python依存パッケージ
├── .env.example           # 環境変数テンプレート
├── .github/workflows/     # CI/CD設定
└── docs/                  # ドキュメント
```
