# インフラ設計書
## IT変更管理・リリース自動化プラットフォーム（IT-Change-CAB-Platform）

| 項目 | 内容 |
|------|------|
| **文書番号** | INF-CAB-001 |
| **バージョン** | 1.0.0 |
| **作成日** | 2026-03-26 |
| **作成者** | みらい建設工業 IT部門 |
| **対象リポジトリ** | Kensan196948G/IT-Change-CAB-Platform |

---

## 1. インフラ概要

### 1.1 構成方針

| 方針 | 内容 |
|------|------|
| コンテナ基盤 | Docker Compose によるコンテナオーケストレーション |
| 構成管理 | IaC（Infrastructure as Code）による構成管理 |
| 可用性目標 | 稼働率 99.5%以上 |
| スケーラビリティ | 同時30ユーザー対応、将来的な水平スケーリング可能な設計 |
| セキュリティ | 最小権限の原則、ネットワーク分離 |

### 1.2 全体構成図

```
┌─────────────────────────────────────────────────────────────────┐
│                        ホストサーバー                              │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Docker Network                        │   │
│  │                                                          │   │
│  │  ┌─────────┐  ┌──────────┐  ┌──────────┐               │   │
│  │  │  Nginx   │  │ Frontend │  │ Backend  │               │   │
│  │  │ :80/:443 │──│  :3000   │  │  :8000   │               │   │
│  │  └────┬─────┘  └──────────┘  └────┬─────┘               │   │
│  │       │                           │                      │   │
│  │       │                      ┌────▼─────┐               │   │
│  │       │                      │  Worker   │               │   │
│  │       │                      │ (BullMQ)  │               │   │
│  │       │                      └────┬─────┘               │   │
│  │       │                           │                      │   │
│  │  ┌────▼──────────┐  ┌────────────▼──┐                   │   │
│  │  │  PostgreSQL   │  │    Redis      │                   │   │
│  │  │    :5432      │  │    :6379      │                   │   │
│  │  └───────────────┘  └──────────────┘                   │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              監視スタック（別Docker Network）               │   │
│  │  Prometheus / Grafana / Loki / AlertManager              │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────┐                                           │
│  │  バックアップ領域  │                                           │
│  │  /backup/        │                                           │
│  └─────────────────┘                                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. サービス一覧

### 2.1 アプリケーションサービス

| サービス名 | イメージ | ポート | 役割 | リソース制限 |
|-----------|---------|--------|------|------------|
| nginx | nginx:alpine | 80, 443 | リバースプロキシ、SSL終端 | CPU: 0.5, Mem: 256MB |
| frontend | cab-platform-frontend | 3000 (内部) | React SPAの配信 | CPU: 0.5, Mem: 512MB |
| backend | cab-platform-backend | 8000 | REST API サーバー | CPU: 2.0, Mem: 4GB |
| worker | cab-platform-backend | - | BullMQ ジョブワーカー | CPU: 1.0, Mem: 2GB |

### 2.2 データストアサービス

| サービス名 | イメージ | ポート | 役割 | リソース制限 |
|-----------|---------|--------|------|------------|
| db | postgres:16-alpine | 5432 (内部) | メインデータベース | CPU: 2.0, Mem: 4GB |
| redis | redis:7-alpine | 6379 (内部) | キャッシュ、ジョブキュー | CPU: 0.5, Mem: 512MB |

### 2.3 監視サービス

| サービス名 | イメージ | ポート | 役割 |
|-----------|---------|--------|------|
| prometheus | prom/prometheus | 9090 | メトリクス収集 |
| grafana | grafana/grafana | 3001 | ダッシュボード |
| loki | grafana/loki | 3100 | ログ集約 |
| promtail | grafana/promtail | 9080 | ログ収集エージェント |
| alertmanager | prom/alertmanager | 9093 | アラート管理 |
| node-exporter | prom/node-exporter | 9100 | ホストメトリクス |
| cadvisor | gcr.io/cadvisor/cadvisor | 8080 | コンテナメトリクス |
| postgres-exporter | prometheuscommunity/postgres-exporter | 9187 | DBメトリクス |
| redis-exporter | oliver006/redis_exporter | 9121 | Redisメトリクス |

---

## 3. ネットワーク設計

### 3.1 Docker ネットワーク

| ネットワーク名 | ドライバー | 用途 | 接続サービス |
|-------------|-----------|------|------------|
| cab-app-net | bridge | アプリケーション通信 | nginx, frontend, backend, worker, db, redis |
| cab-mon-net | bridge | 監視通信 | prometheus, grafana, loki, exporters |

### 3.2 ポート公開設計

| ポート | プロトコル | 公開範囲 | サービス | 用途 |
|--------|----------|---------|---------|------|
| 80 | TCP | 外部 | nginx | HTTP（HTTPSへリダイレクト） |
| 443 | TCP | 外部 | nginx | HTTPS |
| 3001 | TCP | 内部ネットワーク | grafana | 監視ダッシュボード |
| 9090 | TCP | 内部ネットワーク | prometheus | メトリクス |
| 5432 | TCP | localhost のみ | db | DB管理用（本番は公開しない） |
| 6379 | TCP | localhost のみ | redis | Redis管理用（本番は公開しない） |

### 3.3 Nginx リバースプロキシ設定

```nginx
# nginx/nginx.conf
upstream backend {
    server backend:8000;
}

upstream frontend {
    server frontend:80;
}

server {
    listen 80;
    server_name cab.mirai-kensetsu.co.jp;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name cab.mirai-kensetsu.co.jp;

    ssl_certificate     /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;

    # セキュリティヘッダー
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';";

    # API
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # レート制限
        limit_req zone=api burst=20 nodelay;
    }

    # フロントエンド
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;

        # SPA対応
        try_files $uri $uri/ /index.html;
    }

    # ヘルスチェック
    location /health {
        proxy_pass http://backend/api/v1/health;
        access_log off;
    }

    # リクエストサイズ制限
    client_max_body_size 10M;

    # タイムアウト設定
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
}
```

---

## 4. ストレージ設計

### 4.1 Docker ボリューム

| ボリューム名 | マウント先 | サービス | 用途 | サイズ見積 |
|-------------|-----------|---------|------|----------|
| pgdata | /var/lib/postgresql/data | db | PostgreSQLデータ | 10-50GB |
| redisdata | /data | redis | Redis永続化データ | 1-5GB |
| prometheus_data | /prometheus | prometheus | メトリクスデータ | 5-20GB |
| grafana_data | /var/lib/grafana | grafana | ダッシュボード設定 | 1GB |
| loki_data | /loki | loki | ログデータ | 10-30GB |

### 4.2 バインドマウント

| ホスト側パス | コンテナ側パス | サービス | 用途 |
|------------|-------------|---------|------|
| ./nginx/nginx.conf | /etc/nginx/nginx.conf | nginx | Nginx設定 |
| ./nginx/ssl/ | /etc/nginx/ssl/ | nginx | SSL証明書 |
| ./backup/db/ | /backup | db | DBバックアップ |
| ./monitoring/ | /etc/prometheus/ | prometheus | Prometheus設定 |

### 4.3 バックアップストレージ

| パス | 用途 | 保持期間 | ローテーション |
|------|------|---------|-------------|
| /backup/db/ | PostgreSQLバックアップ | 30日 | 日次 02:00 |
| /backup/redis/ | Redisスナップショット | 7日 | 日次 03:00 |
| /backup/logs/ | アーカイブログ | 90日 | 日次 |
| /backup/volumes/ | ボリュームバックアップ | 4世代 | 週次 |

---

## 5. セキュリティ設計

### 5.1 ネットワークセキュリティ

| 対策 | 実装方法 |
|------|---------|
| HTTPS強制 | Nginx でHTTP→HTTPSリダイレクト |
| TLS 1.2/1.3 | Nginx SSL設定でTLS 1.0/1.1を無効化 |
| ファイアウォール | ホストOS の iptables/ufw で必要ポートのみ開放 |
| 内部通信 | DBとRedisはDocker内部ネットワークのみ、外部公開しない |
| レート制限 | Nginx の `limit_req` でAPI呼び出し制限 |

### 5.2 コンテナセキュリティ

| 対策 | 実装方法 |
|------|---------|
| 最小イメージ | Alpine ベースイメージを使用 |
| 非rootユーザー | アプリコンテナは非root で実行 |
| リソース制限 | `deploy.resources.limits` でCPU/メモリ制限 |
| 読取専用FS | 設定ファイルは `:ro` でマウント |
| イメージスキャン | Trivy で脆弱性スキャン |
| シークレット管理 | 環境変数ファイルはGit管理外、chmod 600 |

### 5.3 データベースセキュリティ

| 対策 | 実装方法 |
|------|---------|
| 外部アクセス禁止 | ポートは `127.0.0.1:5432` にバインド |
| 強力なパスワード | 32文字以上のランダムパスワード |
| 接続制限 | `pg_hba.conf` でアクセス元を制限 |
| 暗号化 | PostgreSQL の `scram-sha-256` 認証 |
| 監査ログ | DDL文のログ記録有効化 |

---

## 6. 可用性設計

### 6.1 ヘルスチェック

全サービスにDockerヘルスチェックを設定し、異常検知時に自動再起動する。

| サービス | チェック方法 | 間隔 | リトライ |
|---------|------------|------|--------|
| backend | HTTP GET /api/v1/health | 30秒 | 3回 |
| frontend | HTTP GET / | 60秒 | 3回 |
| db | pg_isready | 30秒 | 3回 |
| redis | redis-cli ping | 30秒 | 3回 |

### 6.2 自動復旧

| 機能 | 設定 |
|------|------|
| コンテナ自動再起動 | `restart: always` |
| 依存関係制御 | `depends_on` + `condition: service_healthy` |
| ヘルスチェック再起動 | Docker Engine が unhealthy コンテナを自動再起動 |

### 6.3 バックアップとリストア

| 項目 | 設定 |
|------|------|
| RPO（目標復旧時点） | 24時間（日次バックアップ） |
| RTO（目標復旧時間） | 4時間 |
| バックアップ方式 | pg_dump（論理バックアップ）+ WALアーカイブ |
| リストアテスト | 月次でテスト環境へのリストア検証 |

---

## 7. PostgreSQL チューニング

### 7.1 主要パラメータ

| パラメータ | 値 | 説明 |
|-----------|---|------|
| max_connections | 100 | 最大接続数 |
| shared_buffers | 1GB | 共有バッファ（メモリの25%） |
| effective_cache_size | 3GB | OSキャッシュ含む有効キャッシュ（メモリの75%） |
| maintenance_work_mem | 256MB | メンテナンス作業用メモリ |
| checkpoint_completion_target | 0.9 | チェックポイント完了目標 |
| wal_buffers | 16MB | WALバッファ |
| default_statistics_target | 100 | 統計情報精度 |
| random_page_cost | 1.1 | SSD環境向け設定 |
| effective_io_concurrency | 200 | SSD環境向け並行I/O |
| log_min_duration_statement | 1000 | 1秒以上のスロークエリをログ |

---

## 8. ホストサーバー要件

### 8.1 本番環境サーバースペック

| 項目 | 最小要件 | 推奨 |
|------|---------|------|
| CPU | 4 vCPU | 8 vCPU |
| メモリ | 8GB | 16GB |
| ディスク | 100GB SSD | 200GB SSD |
| ネットワーク | 1Gbps | 1Gbps |
| OS | Ubuntu 22.04 LTS | Ubuntu 24.04 LTS |

### 8.2 ホストOSの設定

```bash
# カーネルパラメータ
sysctl -w vm.overcommit_memory=1
sysctl -w net.core.somaxconn=65535
sysctl -w fs.file-max=65535

# Docker デーモン設定（/etc/docker/daemon.json）
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "5"
  },
  "storage-driver": "overlay2",
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 65535,
      "Soft": 65535
    }
  }
}
```

---

*文書管理：本文書はバージョン管理対象。変更時はバージョン番号を更新すること。*
