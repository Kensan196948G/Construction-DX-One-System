# 🧪 テスト方針（Testing Policy）

> Construction SIEM Platform のテスト戦略と品質基準

---

## 📋 テスト概要

| 項目 | 値 |
|------|------|
| テストフレームワーク | pytest |
| 総テスト数 | **210件** |
| 目標カバレッジ | **85%以上** |
| 現在のカバレッジ | **83%**（改善中） |
| 非同期テスト | pytest-asyncio |
| HTTPクライアント | httpx（AsyncClient） |
| カバレッジツール | pytest-cov |

---

## 🎯 カバレッジ目標

### 現状と目標

```
目標  ████████████████████░░ 85%
現在  ███████████████████░░░ 83%
                               ▲
                          あと2%改善が必要
```

| レベル | 基準 | 現状 |
|--------|:----:|:----:|
| 🔴 不合格 | < 80% | - |
| 🟡 要改善 | 80-84% | ← 現在 83% |
| 🟢 合格 | 85%以上 | 目標 |
| 🏆 優秀 | 90%以上 | 将来目標 |

---

## 📊 テストレベル

### テストピラミッド

```
         ╱╲
        ╱  ╲
       ╱ E2E╲        ← 少数（統合シナリオ）
      ╱──────╲
     ╱ 統合    ╲      ← 中程度（API統合テスト）
    ╱──────────╲
   ╱ ユニット    ╲    ← 多数（関数・メソッド単体）
  ╱──────────────╲
```

### 各レベルの詳細

| レベル | テスト数 | 割合 | 対象 | 実行速度 |
|--------|:-------:|:----:|------|:-------:|
| ⚡ ユニットテスト | ~160件 | 76% | 関数・メソッド単体 | 高速 |
| 🔗 統合テスト | ~35件 | 17% | API エンドポイント連携 | 中速 |
| 🌐 E2Eテスト | ~15件 | 7% | シナリオ全体 | 低速 |

---

## 🛠 テストツール

| ツール | バージョン | 用途 |
|--------|-----------|------|
| 🧪 pytest | 最新 | テストランナー |
| ⚡ pytest-asyncio | 最新 | 非同期テストサポート |
| 📊 pytest-cov | 最新 | カバレッジ計測 |
| 🌐 httpx | 最新 | 非同期HTTPクライアント |
| 🎭 unittest.mock | 標準 | モック・パッチ |
| 📝 pytest-html | 最新 | HTMLレポート生成 |

---

## 📂 テストファイル構成

```
tests/
├── conftest.py              # 共通フィクスチャ
├── test_api.py              # API基本+統合テスト (22件)
├── test_auth.py             # JWT認証・RBAC (15件)
├── test_kpi.py              # KPI計算・監査・Kafka (18件)
├── test_threat_intel.py     # 脅威インテリジェンス (16件)
├── test_notifications.py    # 通知・ヘルスチェック (11件)
├── test_rate_limit.py       # レート制限 (6件)
├── test_data_validation.py  # データ検証 (11件)
├── test_metrics.py          # メトリクス (9件)
├── test_compliance.py       # コンプライアンス (9件)
├── test_correlation.py      # 相関分析 (9件)
├── test_es_client.py        # ESクライアント (7件)
├── test_elasticsearch.py    # ES統合テスト
├── test_integration.py      # E2E統合テスト
└── test_sigma_rules.py      # Sigma/MLルール
```

---

## ✅ テスト実行方法

### 基本実行

```bash
# 全テスト実行
pytest tests/ -v

# カバレッジ付き実行
pytest tests/ --cov=api --cov-report=term-missing --cov-fail-under=85

# HTML レポート生成
pytest tests/ --cov=api --cov-report=html
# → htmlcov/index.html をブラウザで確認

# 特定ファイルのみ
pytest tests/test_auth.py -v

# 特定テスト関数のみ
pytest tests/test_auth.py -v -k "test_token_generation"

# マーカー指定
pytest tests/ -v -m "asyncio"
```

### CI での実行

```bash
pytest tests/ -v \
  --cov=api \
  --cov-report=xml \
  --cov-report=term-missing \
  --cov-fail-under=85 \
  --tb=short \
  --asyncio-mode=auto
```

---

## 📏 テスト記述規約

### ファイル命名

| パターン | 例 |
|---------|------|
| `test_<module>.py` | `test_api.py`, `test_auth.py` |

### クラス命名

| パターン | 例 |
|---------|------|
| `Test<Feature>` | `TestAlertIngest`, `TestAuthentication` |

### 関数命名

| パターン | 例 |
|---------|------|
| `test_<action>_<expected>` | `test_create_alert_success` |
| `test_<action>_<condition>_<expected>` | `test_create_alert_invalid_severity_returns_422` |

### テスト構造（AAA パターン）

```python
async def test_acknowledge_alert_success(client, auth_headers):
    """正常なアラート承認が成功すること"""
    # Arrange（準備）
    alert_id = "alert-001"

    # Act（実行）
    response = await client.patch(
        f"/api/v1/alerts/{alert_id}/acknowledge",
        headers=auth_headers,
    )

    # Assert（検証）
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["acknowledged"] is True
```

---

## 🔄 テスト改善計画

### カバレッジ改善ロードマップ

| フェーズ | 目標 | 追加テスト |
|---------|:----:|-----------|
| 現在 | 83% | - |
| Phase 1 | 85% | エッジケース追加（認証・バリデーション） |
| Phase 2 | 88% | エラーハンドリングテスト追加 |
| Phase 3 | 90% | E2Eシナリオ拡充 |

### 優先度の高いテスト追加項目

| # | 対象 | テスト内容 | 優先度 |
|:-:|------|-----------|:------:|
| 1 | 認証 | トークンリフレッシュのエッジケース | 🔴 高 |
| 2 | インシデント | SLAタイマー境界値テスト | 🔴 高 |
| 3 | 相関分析 | キルチェーン完全一致シナリオ | 🟡 中 |
| 4 | 通知 | Webhook失敗時のリトライ | 🟡 中 |
| 5 | 監査 | 大量ログの性能テスト | 🔵 低 |
