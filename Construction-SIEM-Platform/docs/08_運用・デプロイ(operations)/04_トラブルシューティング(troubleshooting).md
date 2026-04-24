# 🔧 トラブルシューティング

> Construction SIEM Platform のよくある問題と対処法

---

## 📋 目次

1. [Elasticsearch接続問題](#elasticsearch接続問題)
2. [Kafka接続問題](#kafka接続問題)
3. [認証・認可問題](#認証認可問題)
4. [レート制限問題](#レート制限問題)
5. [CI/CD問題](#cicd問題)
6. [パフォーマンス問題](#パフォーマンス問題)
7. [一般的な問題](#一般的な問題)

---

## 🔍 Elasticsearch接続問題

### 症状: Elasticsearch接続失敗

| 項目 | 内容 |
|------|------|
| 🔴 症状 | API起動時にES接続エラーが表示される |
| 💡 原因 | ESが未起動、ネットワーク到達不可、メモリ不足 |
| ✅ 影響 | **インメモリフォールバック**が自動的に動作する |

```
⚠️ Construction SIEM Platformは、Elasticsearch未接続時でも
   インメモリストレージにフォールバックして動作します。
   本番環境では必ずESを稼働させてください。
```

### 対処手順

```bash
# 1. ESコンテナの状態確認
docker compose ps elasticsearch

# 2. ESログ確認
docker compose logs elasticsearch | tail -50

# 3. ES接続テスト
curl -s http://localhost:9200/_cluster/health | python3 -m json.tool

# 4. メモリ確認（ESはメモリを大量に使用）
docker stats elasticsearch --no-stream

# 5. ES再起動
docker compose restart elasticsearch

# 6. それでも復旧しない場合 → データボリュームの確認
docker volume inspect construction-siem-platform_elasticsearch-data
```

### よくある原因と対策

| 原因 | 対策 |
|------|------|
| メモリ不足 | `ES_JAVA_OPTS=-Xms512m -Xmx512m` を環境変数で調整 |
| ディスク容量不足 | ILMポリシーの確認、古いインデックス削除 |
| ポート競合 | `netstat -tlnp | grep 9200` で確認 |
| 設定エラー | `docker compose logs elasticsearch` でエラー確認 |

---

## 📨 Kafka接続問題

### 症状: Kafka未接続

| 項目 | 内容 |
|------|------|
| 🔴 症状 | イベント送信時にKafka接続エラー |
| 💡 原因 | Kafka/Zookeeper未起動、ネットワーク問題 |
| ✅ 影響 | **スタンバイモード**で動作（イベント受信を一時停止） |

### 対処手順

```bash
# 1. Kafka + Zookeeperの状態確認
docker compose ps kafka zookeeper

# 2. Zookeeperが先に起動しているか確認
docker compose logs zookeeper | tail -20

# 3. Kafkaログ確認
docker compose logs kafka | tail -50

# 4. トピック一覧確認
docker compose exec kafka kafka-topics \
  --list --bootstrap-server localhost:9092

# 5. コンシューマーラグ確認
docker compose exec kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe --all-groups

# 6. 段階的再起動
docker compose restart zookeeper
sleep 10
docker compose restart kafka
```

### よくある原因と対策

| 原因 | 対策 |
|------|------|
| Zookeeper未起動 | Zookeeperを先に起動 |
| ブローカーID重複 | Kafkaデータボリュームを削除して再起動 |
| ネットワーク設定 | `KAFKA_ADVERTISED_LISTENERS` 確認 |
| メモリ不足 | `KAFKA_HEAP_OPTS` を調整 |

---

## 🔑 認証・認可問題

### 症状: JWT期限切れ（401 Unauthorized）

| 項目 | 内容 |
|------|------|
| 🔴 症状 | `401 Unauthorized - Token has expired` |
| 💡 原因 | JWTトークンの有効期限（デフォルト60分）超過 |
| ✅ 対処 | 再認証してトークンを再取得 |

```bash
# トークン再取得
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin"

# レスポンスからaccess_tokenを取得して使用
export TOKEN="取得したトークン"
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/events
```

### 症状: 権限不足（403 Forbidden）

| 項目 | 内容 |
|------|------|
| 🔴 症状 | `403 Forbidden - Insufficient permissions` |
| 💡 原因 | ユーザーのロールに操作権限がない |
| ✅ 対処 | 適切なロールのユーザーで再認証 |

| 操作 | 必要ロール |
|------|----------|
| 監査ログ閲覧 | `admin` |
| コンプライアンスチェック | `admin` |
| IoC削除 | `admin` |
| イベント作成 | `admin` / `analyst` |
| イベント閲覧 | `admin` / `analyst` / `viewer` |

### 症状: JWT秘密鍵エラー

```bash
# 環境変数確認
echo $JWT_SECRET_KEY

# .envファイル確認
grep JWT_SECRET_KEY .env

# 秘密鍵の再設定（強力なランダム文字列を使用）
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## ⏱ レート制限問題

### 症状: レート制限超過（429 Too Many Requests）

| 項目 | 内容 |
|------|------|
| 🔴 症状 | `429 Too Many Requests` |
| 💡 原因 | 同一IPから100リクエスト/分を超過 |
| ✅ 対処 | `Retry-After` ヘッダーの値（秒）を待ってから再試行 |

```bash
# レスポンスヘッダー確認
curl -v http://localhost:8000/api/v1/events 2>&1 | grep -i retry-after

# レート制限設定の確認
grep RATE_LIMIT_PER_MINUTE .env

# レート制限値の変更（開発環境のみ）
# .envファイルを編集
RATE_LIMIT_PER_MINUTE=500
# FastAPI再起動
docker compose restart fastapi
```

### クライアント側の対策

```python
import time
import requests

def api_request_with_retry(url, headers, max_retries=3):
    for attempt in range(max_retries):
        response = requests.get(url, headers=headers)
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            print(f"Rate limited. Waiting {retry_after}s...")
            time.sleep(retry_after)
            continue
        return response
    raise Exception("Max retries exceeded")
```

---

## 🔄 CI/CD問題

### 症状: CI失敗

| チェック | ローカル実行コマンド | 説明 |
|---------|-------------------|------|
| ⬛ black | `black --check .` | コードフォーマット |
| 📑 isort | `isort --check-only .` | import順序 |
| 🔍 flake8 | `flake8 .` | Lintチェック |
| 🧪 pytest | `pytest -v` | テスト実行 |
| 🔒 bandit | `bandit -r src/` | セキュリティチェック |

### 対処手順

```bash
# 1. フォーマット自動修正
black .
isort .

# 2. Lint確認
flake8 .

# 3. テスト実行
pytest -v --tb=short

# 4. セキュリティチェック
bandit -r src/ -f json

# 5. 複雑度チェック（C901）
flake8 --select=C901 --max-complexity=10 .
```

### よくあるCI失敗パターン

| パターン | 原因 | 対処 |
|---------|------|------|
| `black` 失敗 | フォーマット不一致 | `black .` で自動修正 |
| `isort` 失敗 | import順序不正 | `isort .` で自動修正 |
| `flake8 E501` | 行が長すぎる（88文字超） | 行を分割 |
| `flake8 C901` | 関数の複雑度が高い | 関数を分割 |
| `bandit` 警告 | セキュリティリスク | コードを修正、または`# nosec`で除外 |
| `pytest` 失敗 | テスト不合格 | テストコードまたは実装を修正 |

---

## ⚡ パフォーマンス問題

### 症状: API応答が遅い

```bash
# 1. FastAPIコンテナのリソース使用状況
docker stats fastapi --no-stream

# 2. Elasticsearch応答速度
curl -s -w "Time: %{time_total}s\n" http://localhost:9200/_cluster/health

# 3. 詳細ヘルスチェックで遅いコンポーネント特定
curl -s http://localhost:8000/health/detailed | python3 -m json.tool

# 4. FastAPIログでスロークエリ確認
docker compose logs fastapi | grep -i "slow\|timeout"
```

### パフォーマンスチューニング

| 項目 | 推奨設定 | 効果 |
|------|---------|------|
| ESヒープ | `-Xms2g -Xmx2g` | 検索速度向上 |
| ESシャード数 | インデックスごとに1-5 | 書き込み速度向上 |
| Kafkaパーティション | トピックごとに3-6 | スループット向上 |
| FastAPIワーカー | CPU数 × 2 + 1 | 同時処理能力向上 |

---

## 🛠 一般的な問題

### Docker Compose起動失敗

```bash
# ポート使用状況確認
sudo lsof -i :8000  # FastAPI
sudo lsof -i :9200  # Elasticsearch
sudo lsof -i :9092  # Kafka
sudo lsof -i :5601  # Kibana
sudo lsof -i :3000  # Grafana

# 全コンテナ停止
docker compose down

# ボリュームの状態確認
docker volume ls

# Docker自体のログ確認
journalctl -u docker.service --since "1 hour ago"
```

### ディスク容量不足

```bash
# Docker使用量確認
docker system df

# 不要なイメージ・コンテナ削除
docker system prune -f

# 不要なボリューム削除（⚠️ 注意）
docker volume prune -f

# ESインデックスサイズ確認
curl -s "localhost:9200/_cat/indices?v&s=store.size:desc" | head -20
```

### ネットワーク問題

```bash
# Dockerネットワーク確認
docker network ls
docker network inspect construction-siem-platform_default

# コンテナ間通信テスト
docker compose exec fastapi ping elasticsearch
docker compose exec fastapi curl http://elasticsearch:9200
```

---

## 📞 サポートマトリクス

| 問題レベル | 対応方法 | 対応時間 |
|-----------|---------|---------|
| 🟢 軽微 | このドキュメントで自己解決 | - |
| 🟡 中程度 | GitHub Issues で報告 | 24時間以内 |
| 🔴 重大 | エスカレーション（インシデント対応手順参照） | SLAに従う |
