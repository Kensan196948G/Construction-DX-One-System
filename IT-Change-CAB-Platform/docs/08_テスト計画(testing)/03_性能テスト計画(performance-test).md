# 性能テスト計画書
## IT変更管理・リリース自動化プラットフォーム（IT-Change-CAB-Platform）

| 項目 | 内容 |
|------|------|
| **文書番号** | TST-CAB-003 |
| **バージョン** | 1.0.0 |
| **作成日** | 2026-03-26 |
| **作成者** | みらい建設工業 IT部門 |
| **対象リポジトリ** | Kensan196948G/IT-Change-CAB-Platform |

---

## 1. 性能テスト概要

### 1.1 目的

本プラットフォームが非機能要件で定義された性能目標を満たすことを検証する。通常運用時および高負荷時における応答時間・スループット・リソース使用率を計測し、ボトルネックを特定する。

### 1.2 性能目標値

| 指標 | 目標値 | 測定条件 |
|------|--------|---------|
| RFC起票API応答時間 | 2秒以内（95パーセンタイル） | 同時30ユーザー |
| RFC一覧API応答時間 | 2秒以内（95パーセンタイル） | 同時30ユーザー、RFC 1,000件 |
| 変更カレンダー表示 | 2秒以内（95パーセンタイル） | 同時30ユーザー、月間100変更 |
| CAB承認API応答時間 | 1秒以内（95パーセンタイル） | 同時10ユーザー |
| KPIダッシュボード表示 | 3秒以内（95パーセンタイル） | 同時10ユーザー、12ヶ月データ |
| 承認通知送信遅延 | 1分以内 | キュー負荷100件/分 |
| 同時利用ユーザー数 | 30名 | 全機能混合利用 |
| スループット | 100リクエスト/秒 | 混合シナリオ |
| エラー率 | 0.1%以下 | 同時30ユーザー |
| CPU使用率 | 70%以下 | 通常負荷時 |
| メモリ使用率 | 80%以下 | 通常負荷時 |

---

## 2. テスト種別

### 2.1 負荷テスト（Load Test）

| 項目 | 内容 |
|------|------|
| 目的 | 通常負荷下での性能目標達成を確認 |
| 同時ユーザー数 | 30名（目標値） |
| テスト時間 | 30分 |
| ランプアップ | 5分間で0→30ユーザー |
| ランプダウン | 5分間で30→0ユーザー |

### 2.2 ストレステスト（Stress Test）

| 項目 | 内容 |
|------|------|
| 目的 | 限界負荷の特定、システムの挙動確認 |
| 同時ユーザー数 | 30→60→90→120名（段階増加） |
| テスト時間 | 各段階10分 |
| 確認事項 | ブレークポイント特定、エラー率推移、回復挙動 |

### 2.3 耐久テスト（Endurance Test）

| 項目 | 内容 |
|------|------|
| 目的 | 長時間運用時のメモリリーク・性能劣化を検出 |
| 同時ユーザー数 | 15名（通常負荷の50%） |
| テスト時間 | 4時間 |
| 確認事項 | メモリ使用量推移、応答時間推移、DB接続プール |

### 2.4 スパイクテスト（Spike Test）

| 項目 | 内容 |
|------|------|
| 目的 | 急激な負荷増加時の挙動確認 |
| パターン | 5ユーザー → 60ユーザー（即座に増加） → 5ユーザー |
| テスト時間 | 15分 |
| 確認事項 | エラー率、復旧時間、レスポンスタイム |

---

## 3. テストシナリオ

### 3.1 シナリオ一覧

| シナリオID | シナリオ名 | 想定利用割合 | 概要 |
|-----------|----------|------------|------|
| PERF-001 | RFC起票フロー | 30% | RFC起票フォーム表示→入力→送信 |
| PERF-002 | RFC一覧参照 | 25% | RFC一覧表示→フィルタ→ページング |
| PERF-003 | CAB承認フロー | 15% | CABダッシュボード→RFC詳細→承認 |
| PERF-004 | 変更カレンダー参照 | 15% | カレンダー月表示→週表示→イベントクリック |
| PERF-005 | KPIダッシュボード参照 | 10% | KPI画面表示→期間フィルタ変更 |
| PERF-006 | RFC検索 | 5% | キーワード検索→結果表示 |

### 3.2 シナリオ詳細

#### PERF-001: RFC起票フロー

```javascript
// k6 テストスクリプト
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const rfcCreateDuration = new Trend('rfc_create_duration');
const rfcCreateErrors = new Rate('rfc_create_errors');

export const options = {
  stages: [
    { duration: '5m', target: 30 },   // ランプアップ
    { duration: '20m', target: 30 },   // 定常負荷
    { duration: '5m', target: 0 },     // ランプダウン
  ],
  thresholds: {
    'rfc_create_duration': ['p(95)<2000'],  // 95%ile < 2秒
    'rfc_create_errors': ['rate<0.001'],     // エラー率 < 0.1%
    'http_req_duration': ['p(95)<2000'],
  },
};

export default function () {
  const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
  const TOKEN = __ENV.AUTH_TOKEN;

  // 1. RFC起票フォーム画面取得
  const formRes = http.get(`${BASE_URL}/api/v1/rfcs/form-data`, {
    headers: { Authorization: `Bearer ${TOKEN}` },
  });
  check(formRes, { 'フォームデータ取得成功': (r) => r.status === 200 });

  sleep(2); // ユーザー入力時間

  // 2. 衝突チェック
  const conflictRes = http.post(
    `${BASE_URL}/api/v1/rfcs/check-conflict`,
    JSON.stringify({
      target_systems: ['ActiveDirectory'],
      planned_start: '2026-04-15T09:00:00Z',
      planned_end: '2026-04-15T11:00:00Z',
    }),
    { headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${TOKEN}` } }
  );
  check(conflictRes, { '衝突チェック成功': (r) => r.status === 200 });

  sleep(1);

  // 3. RFC送信
  const startTime = Date.now();
  const createRes = http.post(
    `${BASE_URL}/api/v1/rfcs`,
    JSON.stringify({
      title: `テスト変更申請 ${Date.now()}`,
      description: 'k6負荷テスト用RFC',
      change_type: 'normal',
      target_systems: ['ActiveDirectory'],
      planned_start: '2026-04-15T09:00:00Z',
      planned_end: '2026-04-15T11:00:00Z',
      business_impact: '一時的なAD認証遅延の可能性',
      risk_assessment: 'リスク低：定期メンテナンス作業',
      rollback_plan: 'AD設定の前回バックアップからの復元',
    }),
    { headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${TOKEN}` } }
  );
  rfcCreateDuration.add(Date.now() - startTime);
  rfcCreateErrors.add(createRes.status !== 201);

  check(createRes, {
    'RFC作成成功': (r) => r.status === 201,
    'RFC番号返却': (r) => JSON.parse(r.body).rfc_number !== undefined,
  });

  sleep(3); // ページ閲覧時間
}
```

#### PERF-002: RFC一覧参照フロー

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export default function () {
  const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
  const TOKEN = __ENV.AUTH_TOKEN;
  const headers = { Authorization: `Bearer ${TOKEN}` };

  // 1. RFC一覧取得（1ページ目）
  const listRes = http.get(`${BASE_URL}/api/v1/rfcs?page=1&limit=20`, { headers });
  check(listRes, {
    'RFC一覧取得成功': (r) => r.status === 200,
    '応答時間2秒以内': (r) => r.timings.duration < 2000,
  });

  sleep(2);

  // 2. フィルタ付き一覧取得
  const filteredRes = http.get(
    `${BASE_URL}/api/v1/rfcs?page=1&limit=20&status=cab_review&change_type=normal`,
    { headers }
  );
  check(filteredRes, { 'フィルタ一覧取得成功': (r) => r.status === 200 });

  sleep(2);

  // 3. 2ページ目取得
  const page2Res = http.get(`${BASE_URL}/api/v1/rfcs?page=2&limit=20`, { headers });
  check(page2Res, { '2ページ目取得成功': (r) => r.status === 200 });

  sleep(3);
}
```

#### PERF-003: CAB承認フロー

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export default function () {
  const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
  const TOKEN = __ENV.CAB_AUTH_TOKEN;
  const headers = { Authorization: `Bearer ${TOKEN}` };

  // 1. CABダッシュボード取得
  const dashRes = http.get(`${BASE_URL}/api/v1/cab/dashboard`, { headers });
  check(dashRes, { 'ダッシュボード取得成功': (r) => r.status === 200 });

  sleep(2);

  // 2. 審議対象RFC詳細取得
  const rfcId = JSON.parse(dashRes.body).pending_rfcs?.[0]?.id;
  if (rfcId) {
    const detailRes = http.get(`${BASE_URL}/api/v1/rfcs/${rfcId}`, { headers });
    check(detailRes, { 'RFC詳細取得成功': (r) => r.status === 200 });

    sleep(3);

    // 3. 承認投票
    const voteRes = http.post(
      `${BASE_URL}/api/v1/cab/decisions`,
      JSON.stringify({
        rfc_id: rfcId,
        decision: 'approved',
        comment: 'k6テスト承認',
      }),
      { headers: { ...headers, 'Content-Type': 'application/json' } }
    );
    check(voteRes, {
      '承認成功': (r) => r.status === 200 || r.status === 201,
      '応答時間1秒以内': (r) => r.timings.duration < 1000,
    });
  }

  sleep(3);
}
```

#### PERF-004: 変更カレンダー参照

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export default function () {
  const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
  const TOKEN = __ENV.AUTH_TOKEN;
  const headers = { Authorization: `Bearer ${TOKEN}` };

  // 1. 月間カレンダーデータ取得
  const calRes = http.get(
    `${BASE_URL}/api/v1/calendar?start=2026-04-01&end=2026-04-30`,
    { headers }
  );
  check(calRes, {
    'カレンダーデータ取得成功': (r) => r.status === 200,
    '応答時間2秒以内': (r) => r.timings.duration < 2000,
  });

  sleep(3);

  // 2. 週間カレンダーデータ取得
  const weekRes = http.get(
    `${BASE_URL}/api/v1/calendar?start=2026-04-06&end=2026-04-12`,
    { headers }
  );
  check(weekRes, { '週間データ取得成功': (r) => r.status === 200 });

  sleep(2);
}
```

---

## 4. テスト環境

### 4.1 環境構成

| コンポーネント | スペック | 備考 |
|--------------|--------|------|
| テスト実行マシン | 4 vCPU / 8GB RAM | k6実行環境 |
| アプリケーションサーバー | 2 vCPU / 4GB RAM | 本番同等構成 |
| PostgreSQL | 2 vCPU / 4GB RAM / SSD 50GB | 本番同等構成 |
| Redis | 1 vCPU / 2GB RAM | 本番同等構成 |
| BullMQワーカー | 1 vCPU / 2GB RAM | ジョブ処理 |

### 4.2 テストデータ

| データ種別 | 件数 | 備考 |
|-----------|------|------|
| ユーザーアカウント | 50件 | CABメンバー10名、一般ユーザー40名 |
| RFC（変更申請） | 1,000件 | 各ステータス分布：draft 10%, submitted 5%, cab_review 5%, approved 10%, in_progress 5%, completed 55%, rolled_back 5%, cancelled 5% |
| CABセッション | 100件 | 過去12ヶ月分 |
| フリーズ期間 | 10件 | 年4回の繁忙期 |
| 通知履歴 | 5,000件 | 各種通知 |

### 4.3 テストデータ生成スクリプト

```bash
# テストデータ生成
cd backend
npm run seed:performance -- --users=50 --rfcs=1000 --sessions=100

# データ確認
psql $DATABASE_URL -c "SELECT change_type, status, COUNT(*) FROM change_requests GROUP BY change_type, status;"
```

---

## 5. 監視・計測項目

### 5.1 アプリケーションメトリクス

| メトリクス | 計測方法 | 閾値 |
|-----------|---------|------|
| HTTP応答時間（p50/p90/p95/p99） | k6 | p95 < 2秒 |
| スループット（RPS） | k6 | > 100 RPS |
| エラー率 | k6 | < 0.1% |
| アクティブ接続数 | k6 | < 100 |

### 5.2 サーバーリソースメトリクス

| メトリクス | 計測方法 | 閾値 |
|-----------|---------|------|
| CPU使用率 | docker stats / Prometheus | < 70% |
| メモリ使用量 | docker stats / Prometheus | < 80% |
| ディスクI/O | iostat | IOPS < 上限の80% |
| ネットワークI/O | iftop | 帯域 < 上限の70% |

### 5.3 データベースメトリクス

| メトリクス | 計測方法 | 閾値 |
|-----------|---------|------|
| クエリ実行時間 | pg_stat_statements | p95 < 500ms |
| アクティブ接続数 | pg_stat_activity | < max_connections の 80% |
| キャッシュヒット率 | pg_stat_database | > 95% |
| デッドロック数 | pg_stat_database | 0 |
| テーブルスキャン数 | pg_stat_user_tables | seq_scan の急増なし |

### 5.4 Redisメトリクス

| メトリクス | 計測方法 | 閾値 |
|-----------|---------|------|
| メモリ使用量 | redis-cli INFO | < maxmemory の 80% |
| 接続数 | redis-cli INFO | < 100 |
| キャッシュヒット率 | redis-cli INFO | > 90% |
| キュー長 | BullMQ UI | < 1,000 |

---

## 6. テスト実行手順

### 6.1 事前準備

```bash
# 1. k6インストール
brew install k6  # macOS
# または
sudo apt install k6  # Ubuntu

# 2. テスト環境起動
docker compose -f docker-compose.test.yml up -d

# 3. テストデータ投入
npm run seed:performance

# 4. テスト用認証トークン取得
export AUTH_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"perf_user","password":"test_password"}' | jq -r '.token')

export CAB_AUTH_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"cab_member","password":"test_password"}' | jq -r '.token')
```

### 6.2 テスト実行

```bash
# 負荷テスト
k6 run --env BASE_URL=http://localhost:8000 \
       --env AUTH_TOKEN=$AUTH_TOKEN \
       tests/performance/load-test.js \
       --out json=results/load-test-$(date +%Y%m%d).json

# ストレステスト
k6 run --env BASE_URL=http://localhost:8000 \
       --env AUTH_TOKEN=$AUTH_TOKEN \
       tests/performance/stress-test.js \
       --out json=results/stress-test-$(date +%Y%m%d).json

# 耐久テスト
k6 run --env BASE_URL=http://localhost:8000 \
       --env AUTH_TOKEN=$AUTH_TOKEN \
       tests/performance/endurance-test.js \
       --out json=results/endurance-test-$(date +%Y%m%d).json

# スパイクテスト
k6 run --env BASE_URL=http://localhost:8000 \
       --env AUTH_TOKEN=$AUTH_TOKEN \
       tests/performance/spike-test.js \
       --out json=results/spike-test-$(date +%Y%m%d).json
```

### 6.3 結果確認

```bash
# k6サマリー出力
k6 run --summary-export=results/summary.json tests/performance/load-test.js

# Grafanaダッシュボードで可視化（k6 + InfluxDB + Grafana）
# http://localhost:3001/d/k6-dashboard
```

---

## 7. 合格基準

| テスト種別 | 合格基準 |
|-----------|---------|
| 負荷テスト | 全API応答時間がp95 < 2秒、エラー率 < 0.1%、同時30ユーザー処理可能 |
| ストレステスト | 60ユーザーまでエラー率 < 1%、システムクラッシュなし |
| 耐久テスト | 4時間連続稼働でメモリリークなし（使用量増加 < 10%）、応答時間劣化なし |
| スパイクテスト | スパイク後5分以内に正常応答に復旧 |

---

## 8. 性能改善対策（ボトルネック対応計画）

| 想定ボトルネック | 検知指標 | 対策 |
|---------------|---------|------|
| DB クエリ遅延 | クエリ実行時間 > 500ms | インデックス追加、クエリ最適化 |
| DB 接続プール枯渇 | アクティブ接続数 > 80% | プールサイズ拡張、接続リーク修正 |
| API 応答遅延 | p95 > 2秒 | Redis キャッシュ導入、N+1クエリ修正 |
| メモリリーク | メモリ使用量の継続増加 | ヒープダンプ解析、リーク箇所修正 |
| キュー滞留 | キュー長 > 1,000 | ワーカー数増加、処理バッチ化 |
| CPU高負荷 | CPU > 70% | 処理の非同期化、水平スケーリング |

---

## 9. テストスケジュール

| フェーズ | 期間 | テスト内容 | 備考 |
|---------|------|-----------|------|
| 準備 | 1日 | 環境構築、データ投入、スクリプト検証 | |
| 負荷テスト | 1日 | 各シナリオの負荷テスト実行 | |
| ストレステスト | 1日 | 限界負荷特定 | |
| 耐久テスト | 1日 | 4時間連続テスト | 夜間実行推奨 |
| スパイクテスト | 半日 | スパイクテスト実行 | |
| 分析・改善 | 2日 | 結果分析、ボトルネック改善 | |
| 再テスト | 1日 | 改善後の再テスト | |

---

*文書管理：本文書はバージョン管理対象。変更時はバージョン番号を更新すること。*
