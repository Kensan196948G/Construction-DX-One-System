# パフォーマンステスト計画（Performance Test Plan）

| 項目 | 内容 |
|------|------|
| 文書番号 | TST-004 |
| バージョン | 1.0 |
| 作成日 | 2026-03-26 |
| 最終更新日 | 2026-03-26 |
| 作成者 | 品質管理チーム |
| 対象プロジェクト | 建設業 統合リスク＆コンプライアンス管理システム（Construction-GRC-System） |

---

## 1. 概要

### 1.1 目的

本文書は、Construction-GRC-Systemのパフォーマンステスト計画を定める。システムが要求される性能指標を満たすことを検証し、ボトルネックの特定と改善指針の策定を行う。

### 1.2 テスト範囲

| テスト種別 | 目的 |
|-----------|------|
| 負荷テスト（Load Test） | 想定されるピーク時の同時利用に耐えられるか検証 |
| ストレステスト（Stress Test） | 想定を超える負荷でのシステムの限界と回復性を検証 |
| 耐久テスト（Endurance Test） | 長時間の継続利用でのメモリリーク等の問題を検証 |
| スパイクテスト（Spike Test） | 急激な負荷増加に対する応答性を検証 |
| スケーラビリティテスト | 水平スケール時の性能向上を検証 |

---

## 2. 性能指標（SLA/SLO）

### 2.1 応答時間

| 操作カテゴリ | 目標応答時間 | 許容上限 | 測定条件 |
|------------|------------|---------|---------|
| 一覧画面表示 | 1秒以内 | 2秒 | 100件のデータ、同時50ユーザー |
| 詳細画面表示 | 500ms以内 | 1秒 | 関連データ含む |
| データ作成（POST） | 500ms以内 | 1秒 | 単一レコード |
| データ更新（PATCH） | 500ms以内 | 1秒 | 単一レコード |
| 検索実行 | 1秒以内 | 3秒 | 10万件からの全文検索 |
| ダッシュボード表示 | 2秒以内 | 3秒 | 全集計データ |
| レポート生成（小規模） | 3秒以内 | 5秒 | 100件以下 |
| レポート生成（大規模） | - | 60秒 | 非同期処理、10,000件以上 |
| ファイルアップロード | 3秒以内 | 5秒 | 10MBファイル |
| ログイン | 1秒以内 | 2秒 | JWT発行含む |

### 2.2 スループット

| 指標 | 目標値 | 備考 |
|------|--------|------|
| 同時接続ユーザー数 | 200 | アクティブセッション |
| リクエスト/秒（RPS） | 500 | 平均 |
| ピーク時RPS | 1,000 | 朝の業務開始時想定 |

### 2.3 リソース使用率

| リソース | 正常時目標 | 警告閾値 | 危険閾値 |
|---------|----------|---------|---------|
| CPU使用率 | 50%以下 | 70% | 85% |
| メモリ使用率 | 60%以下 | 75% | 90% |
| ディスクI/O | 50%以下 | 70% | 85% |
| データベース接続数 | 50%以下 | 70% | 85% |
| Redis メモリ | 60%以下 | 75% | 90% |

### 2.4 可用性

| 指標 | 目標値 |
|------|--------|
| 稼働率 | 99.5%以上 |
| 計画外ダウンタイム | 月間4時間以内 |
| エラーレート | 0.1%以下（5xx応答） |

---

## 3. テスト環境

### 3.1 環境構成

| コンポーネント | 本番環境 | テスト環境 |
|--------------|---------|----------|
| アプリサーバー | 2台（4vCPU, 8GB RAM） | 2台（同等スペック） |
| データベース | PostgreSQL 16（8vCPU, 32GB RAM） | 同等スペック |
| Redis | 2台（2vCPU, 8GB RAM） | 同等スペック |
| Celeryワーカー | 4台（2vCPU, 4GB RAM） | 同等スペック |
| ロードバランサー | Nginx | 同等構成 |

### 3.2 テストデータ

| データ種別 | 件数 | 備考 |
|-----------|------|------|
| ユーザー | 500 | 各ロール分布含む |
| リスク | 100,000 | 添付ファイル含む |
| コンプライアンス項目 | 50,000 | 法令・遵守状況含む |
| 統制項目 | 10,000 | 階層構造含む |
| 監査記録 | 20,000 | 指摘事項・エビデンス含む |
| 監査ログ | 1,000,000 | 過去1年分想定 |
| 通知 | 500,000 | 既読・未読含む |

### 3.3 テストデータ生成

```python
# management command: generate_performance_test_data.py
python manage.py generate_test_data \
    --users 500 \
    --risks 100000 \
    --compliance 50000 \
    --controls 10000 \
    --audits 20000 \
    --audit-logs 1000000
```

---

## 4. テストツール

### 4.1 ツール構成

| ツール | 用途 | 選定理由 |
|--------|------|---------|
| **Locust** | 負荷テスト（主要ツール） | Pythonで記述可能、分散実行対応、リアルタイムダッシュボード |
| **k6** | 負荷テスト（補助） | JavaScriptで記述、CI統合容易、高精度な測定 |
| **pgbench** | データベース単体ベンチマーク | PostgreSQL標準ツール |
| **redis-benchmark** | Redis単体ベンチマーク | Redis標準ツール |
| **Grafana** | メトリクス可視化 | リアルタイム監視、ダッシュボード |
| **Prometheus** | メトリクス収集 | アプリケーション・インフラメトリクス |

### 4.2 Locust テストシナリオ例

```python
from locust import HttpUser, task, between, tag


class GRCUser(HttpUser):
    """GRCシステムの一般的な利用パターンを再現するユーザー。"""

    wait_time = between(1, 5)
    host = "https://staging.grc-system.example.com"

    def on_start(self):
        """ログイン処理。"""
        response = self.client.post("/api/v1/auth/login/", json={
            "email": f"testuser{self.environment.runner.user_count}@example.com",
            "password": "TestPassword123!",
        })
        self.token = response.json()["access"]
        self.client.headers.update({"Authorization": f"Bearer {self.token}"})

    @tag("dashboard")
    @task(5)
    def view_dashboard(self):
        """ダッシュボード表示（最も頻繁な操作）。"""
        self.client.get("/api/v1/dashboard/summary/")

    @tag("risk", "list")
    @task(3)
    def list_risks(self):
        """リスク一覧の取得。"""
        self.client.get("/api/v1/risks/?page=1&per_page=20")

    @tag("risk", "detail")
    @task(2)
    def view_risk_detail(self):
        """リスク詳細の取得。"""
        import random
        risk_id = random.randint(1, 10000)
        self.client.get(f"/api/v1/risks/{risk_id}/")

    @tag("risk", "search")
    @task(2)
    def search_risks(self):
        """リスクの検索。"""
        self.client.get("/api/v1/risks/?search=安全&risk_level=high")

    @tag("risk", "create")
    @task(1)
    def create_risk(self):
        """リスクの作成。"""
        self.client.post("/api/v1/risks/", json={
            "title": "パフォーマンステスト用リスク",
            "description": "負荷テストで自動作成されたリスク",
            "probability": 0.5,
            "impact": 5,
            "risk_level": "medium",
        })

    @tag("compliance")
    @task(2)
    def list_compliance(self):
        """コンプライアンス一覧の取得。"""
        self.client.get("/api/v1/compliance/?page=1&per_page=20")

    @tag("report")
    @task(1)
    def generate_report(self):
        """レポート生成（非同期）。"""
        self.client.post("/api/v1/reports/generate/", json={
            "type": "risk_summary",
            "format": "pdf",
        })
```

### 4.3 k6 テストシナリオ例

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const errorRate = new Rate('errors');
const dashboardDuration = new Trend('dashboard_duration');

export const options = {
  stages: [
    { duration: '2m', target: 50 },   // ランプアップ
    { duration: '5m', target: 100 },   // ピーク負荷
    { duration: '2m', target: 200 },   // ストレス負荷
    { duration: '5m', target: 200 },   // ストレス維持
    { duration: '2m', target: 0 },     // ランプダウン
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'],  // 95%タイルが2秒以内
    errors: ['rate<0.01'],              // エラーレート1%未満
    dashboard_duration: ['p(95)<3000'], // ダッシュボード95%タイルが3秒以内
  },
};

const BASE_URL = 'https://staging.grc-system.example.com/api/v1';

export function setup() {
  const res = http.post(`${BASE_URL}/auth/login/`, JSON.stringify({
    email: 'loadtest@example.com',
    password: 'TestPassword123!',
  }), { headers: { 'Content-Type': 'application/json' } });
  return { token: res.json('access') };
}

export default function (data) {
  const headers = {
    Authorization: `Bearer ${data.token}`,
    'Content-Type': 'application/json',
  };

  // ダッシュボード表示
  const dashRes = http.get(`${BASE_URL}/dashboard/summary/`, { headers });
  dashboardDuration.add(dashRes.timings.duration);
  check(dashRes, { 'dashboard status 200': (r) => r.status === 200 });
  errorRate.add(dashRes.status !== 200);

  sleep(1);

  // リスク一覧
  const listRes = http.get(`${BASE_URL}/risks/?page=1&per_page=20`, { headers });
  check(listRes, { 'list status 200': (r) => r.status === 200 });
  errorRate.add(listRes.status !== 200);

  sleep(1);
}
```

---

## 5. テストシナリオ

### 5.1 負荷テスト（Load Test）

| シナリオID | シナリオ名 | ユーザー数 | 持続時間 | 合格基準 |
|-----------|----------|----------|---------|---------|
| LT-001 | 通常負荷 | 50同時ユーザー | 30分 | 応答時間P95 < 2秒、エラーレート < 0.1% |
| LT-002 | ピーク負荷 | 100同時ユーザー | 30分 | 応答時間P95 < 3秒、エラーレート < 0.5% |
| LT-003 | 設計上限 | 200同時ユーザー | 30分 | 応答時間P95 < 5秒、エラーレート < 1% |
| LT-004 | 段階的負荷増加 | 10→50→100→200 | 1時間 | 各段階で応答時間が線形に増加（指数的増加は不可） |

### 5.2 ストレステスト（Stress Test）

| シナリオID | シナリオ名 | ユーザー数 | 持続時間 | 合格基準 |
|-----------|----------|----------|---------|---------|
| ST-001 | 限界値テスト | 300同時ユーザー | 15分 | システムが安全にエラーを返す（クラッシュしない） |
| ST-002 | 回復テスト | 300→50 | 30分 | 負荷低減後5分以内に正常応答に復帰 |
| ST-003 | リソース枯渇テスト | 500同時ユーザー | 10分 | OOMやプロセスダウンが発生しない |

### 5.3 耐久テスト（Endurance Test）

| シナリオID | シナリオ名 | ユーザー数 | 持続時間 | 合格基準 |
|-----------|----------|----------|---------|---------|
| ET-001 | 8時間耐久 | 50同時ユーザー | 8時間 | メモリ使用量が安定（リーク無し）、応答時間の劣化無し |
| ET-002 | 24時間耐久 | 30同時ユーザー | 24時間 | 上記に加え、DB接続プール・Celeryタスクキューの安定性 |

### 5.4 スパイクテスト（Spike Test）

| シナリオID | シナリオ名 | ユーザー数 | 持続時間 | 合格基準 |
|-----------|----------|----------|---------|---------|
| SK-001 | 急激な負荷増加 | 10→200（1分以内） | 15分 | 200ユーザー到達後3分以内に応答時間安定 |
| SK-002 | 繰り返しスパイク | 10⇔200（5分間隔） | 30分 | 各スパイクから3分以内に回復 |

---

## 6. 重点テスト対象

### 6.1 データベースクエリ性能

| テスト対象 | SQL操作 | データ量 | 目標時間 |
|-----------|---------|---------|---------|
| リスク一覧（フィルタ付き） | SELECT + JOIN + WHERE | 10万件から20件取得 | 100ms以内 |
| リスク全文検索 | SELECT + tsvector検索 | 10万件から検索 | 500ms以内 |
| ダッシュボード集計 | SELECT + GROUP BY + COUNT | 10万件の集計 | 1秒以内 |
| 監査ログ検索 | SELECT + WHERE + ORDER | 100万件から100件取得 | 500ms以内 |
| 統制マトリクス取得 | SELECT + 複数JOIN | 1万統制 x リスク | 2秒以内 |

### 6.2 API エンドポイント性能

| エンドポイント | メソッド | 期待応答時間（P95） |
|--------------|---------|-------------------|
| `/api/v1/dashboard/summary/` | GET | 2秒 |
| `/api/v1/risks/` | GET | 1秒 |
| `/api/v1/risks/` | POST | 500ms |
| `/api/v1/risks/{id}/` | GET | 500ms |
| `/api/v1/risks/{id}/` | PATCH | 500ms |
| `/api/v1/compliance/` | GET | 1秒 |
| `/api/v1/audits/` | GET | 1秒 |
| `/api/v1/reports/generate/` | POST | 1秒（タスク投入） |
| `/api/v1/auth/login/` | POST | 1秒 |

### 6.3 非同期タスク性能

| タスク | データ量 | 目標完了時間 |
|--------|---------|------------|
| PDFレポート生成 | 100件 | 5秒 |
| PDFレポート生成 | 10,000件 | 60秒 |
| Excelエクスポート | 10,000件 | 30秒 |
| 期限チェックバッチ | 50,000件 | 5分 |
| 通知一括送信 | 1,000件 | 2分 |
| リスクスコア再計算 | 100,000件 | 10分 |

---

## 7. 実行計画

### 7.1 テストスケジュール

| フェーズ | 期間 | 実施内容 |
|---------|------|---------|
| 準備 | 1週間 | テスト環境構築、テストデータ生成、シナリオ作成 |
| ベースライン測定 | 2日 | 単一ユーザーでの基本性能測定 |
| 負荷テスト | 3日 | LT-001 ～ LT-004 実行 |
| ストレステスト | 2日 | ST-001 ～ ST-003 実行 |
| 耐久テスト | 2日 | ET-001, ET-002 実行 |
| スパイクテスト | 1日 | SK-001, SK-002 実行 |
| 分析・改善 | 3日 | ボトルネック分析、チューニング |
| 再テスト | 2日 | 改善後の検証 |
| 報告書作成 | 2日 | 結果サマリー、改善提案 |

### 7.2 実行手順

```bash
# 1. テスト環境の確認
curl -sf https://staging.grc-system.example.com/api/health/

# 2. テストデータの生成
docker compose exec backend python manage.py generate_test_data --risks 100000

# 3. Locust による負荷テスト実行
locust -f tests/performance/locustfile.py \
  --host=https://staging.grc-system.example.com \
  --users=100 \
  --spawn-rate=10 \
  --run-time=30m \
  --csv=results/load_test \
  --html=results/load_test_report.html

# 4. k6 によるテスト実行
k6 run tests/performance/k6_scenarios.js \
  --out json=results/k6_results.json

# 5. 結果の確認
# Grafana ダッシュボード: http://monitoring.example.com:3000
```

---

## 8. 監視・計測項目

### 8.1 アプリケーションメトリクス

| メトリクス | 収集方法 | 閾値 |
|-----------|---------|------|
| リクエスト応答時間（P50/P95/P99） | Django Middleware + Prometheus | P95 < 2秒 |
| リクエスト/秒（RPS） | Nginx access log + Prometheus | - |
| エラーレート（4xx/5xx） | Django Middleware | < 1% |
| アクティブDB接続数 | PostgreSQL pg_stat_activity | < プール上限の80% |
| Celeryキュー長 | Celery + Flower | < 1,000 |
| Celeryタスク実行時間 | Celery + Prometheus | タスク別に設定 |

### 8.2 インフラメトリクス

| メトリクス | 収集方法 | 閾値 |
|-----------|---------|------|
| CPU使用率 | Node Exporter | < 85% |
| メモリ使用率 | Node Exporter | < 90% |
| ディスクI/O | Node Exporter | < 85% |
| ネットワーク帯域 | Node Exporter | < 80% |
| PostgreSQL クエリ実行時間 | pg_stat_statements | スロークエリ < 1秒 |
| Redis メモリ使用量 | Redis Exporter | < 設定上限の90% |

---

## 9. ボトルネック対応ガイドライン

| 症状 | 想定原因 | 対応方法 |
|------|---------|---------|
| API応答時間が遅い | N+1クエリ | `select_related`/`prefetch_related` の追加 |
| DB接続数が上限に到達 | 接続プール不足 | pgbouncer導入、プールサイズ調整 |
| メモリ使用量が増加し続ける | メモリリーク | `tracemalloc` で調査、オブジェクト参照の解放 |
| Celeryタスクが溜まる | ワーカー不足 | ワーカー数増加、タスクの優先度調整 |
| ダッシュボード表示が遅い | 集計クエリが重い | マテリアライズドビュー導入、キャッシュ適用 |
| 検索が遅い | インデックス不足 | GINインデックス追加、`pg_trgm` 最適化 |
| レポート生成が遅い | 大量データの直列処理 | バッチ分割、ストリーミング出力 |

---

## 10. 成果物

| 成果物 | 説明 |
|--------|------|
| パフォーマンステスト結果レポート | 各シナリオの実行結果サマリー |
| Locust/k6 レポート（HTML） | 詳細な測定データとグラフ |
| ボトルネック分析レポート | 特定されたボトルネックと改善提案 |
| チューニング実施報告 | 実施した最適化と効果測定 |
| Grafana ダッシュボードキャプチャ | テスト中のリソース使用状況 |

---

## 改訂履歴

| バージョン | 日付 | 変更内容 | 変更者 |
|-----------|------|---------|--------|
| 1.0 | 2026-03-26 | 初版作成 | 品質管理チーム |
