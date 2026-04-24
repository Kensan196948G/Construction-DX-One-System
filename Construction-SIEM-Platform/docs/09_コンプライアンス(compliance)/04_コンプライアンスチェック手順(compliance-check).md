# ✅ 自動コンプライアンスチェック手順

> Construction SIEM Platform のコンプライアンス自動検証ガイド

---

## 📋 目次

1. [概要](#概要)
2. [チェックエンドポイント](#チェックエンドポイント)
3. [ISO 27001 チェック項目](#iso-27001-チェック項目)
4. [NIST CSF チェック項目](#nist-csf-チェック項目)
5. [スコア計算方法](#スコア計算方法)
6. [定期実行ガイド](#定期実行ガイド)
7. [レポート活用](#レポート活用)

---

## 🎯 概要

### 自動コンプライアンスチェックとは

```
┌─────────────────────────────────────────┐
│       自動コンプライアンスチェック         │
│                                         │
│  API呼び出し                              │
│      │                                  │
│      ▼                                  │
│  ┌──────────────┐  ┌──────────────┐     │
│  │ ISO 27001    │  │ NIST CSF    │     │
│  │ 5項目チェック │  │ 6項目チェック │     │
│  └──────┬───────┘  └──────┬───────┘     │
│         │                 │             │
│         ▼                 ▼             │
│  ┌──────────────────────────────┐       │
│  │   スコア計算・判定            │       │
│  │   compliant / partial /      │       │
│  │   non_compliant              │       │
│  └──────────────────────────────┘       │
│         │                               │
│         ▼                               │
│  レポート出力                              │
└─────────────────────────────────────────┘
```

### チェック概要

| フレームワーク | チェック項目数 | 自動化率 |
|--------------|:----------:|:-------:|
| ISO 27001 | 5項目 | 100% |
| NIST CSF | 6項目 | 100% |
| **合計** | **11項目** | **100%** |

---

## 🔌 チェックエンドポイント

### 基本情報

| 項目 | 値 |
|------|-----|
| エンドポイント | `GET /api/v1/compliance/check` |
| 認証 | 必須（Bearer Token） |
| 必要ロール | 🔴 `admin` |
| レスポンス形式 | JSON |

### リクエスト

```bash
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:8000/api/v1/compliance/check
```

### レスポンス全体構造

```json
{
  "iso27001": {
    "A.8.5": { "status": "compliant", "details": "..." },
    "A.8.15": { "status": "compliant", "details": "..." },
    "A.8.16": { "status": "compliant", "details": "..." },
    "A.9.1": { "status": "compliant", "details": "..." },
    "A.5.25": { "status": "compliant", "details": "..." }
  },
  "iso27001_score": 100.0,
  "nist_csf": {
    "DE.CM-1": { "status": "compliant", "details": "..." },
    "DE.CM-3": { "status": "compliant", "details": "..." },
    "DE.CM-7": { "status": "compliant", "details": "..." },
    "PR.AC-1": { "status": "compliant", "details": "..." },
    "RS.RP-1": { "status": "compliant", "details": "..." },
    "DE.CM-4": { "status": "compliant", "details": "..." }
  },
  "nist_csf_score": 100.0,
  "overall_score": 100.0,
  "timestamp": "2026-03-24T10:00:00Z"
}
```

---

## 📜 ISO 27001 チェック項目

### 自動チェック一覧

| # | 制御項目 | チェック内容 | 判定基準 |
|:-:|---------|------------|---------|
| 1 | **A.8.5** セキュアな認証 | JWT認証が有効か | 認証ミドルウェアが稼働中 |
| 2 | **A.8.15** ログ取得 | 監査ログが記録されているか | 監査ログエントリ数 > 0 |
| 3 | **A.8.16** 監視活動 | 検知エンジンが稼働中か | Sigma/ML/IoCエンジン状態 |
| 4 | **A.9.1** アクセス制御方針 | RBACが有効か | ロール定義が存在 |
| 5 | **A.5.25** インシデント管理 | プレイブック機能が有効か | プレイブックエンジン稼働中 |

### チェック結果例

```json
{
  "iso27001": {
    "A.8.5": {
      "status": "compliant",
      "details": "JWT認証が有効。HS256アルゴリズム使用。トークン有効期限: 60分"
    },
    "A.8.15": {
      "status": "compliant",
      "details": "監査ログ記録中。現在のエントリ数: 5,432件"
    },
    "A.8.16": {
      "status": "compliant",
      "details": "Sigmaルール: 15件ロード済、MLモデル: 稼働中、IoC: 1,500件登録済"
    },
    "A.9.1": {
      "status": "compliant",
      "details": "RBAC有効。ロール: admin, analyst, viewer"
    },
    "A.5.25": {
      "status": "compliant",
      "details": "プレイブックエンジン稼働中。登録プレイブック: 5件"
    }
  },
  "iso27001_score": 100.0
}
```

---

## 🛡 NIST CSF チェック項目

### 自動チェック一覧

| # | サブカテゴリ | チェック内容 | 判定基準 |
|:-:|------------|------------|---------|
| 1 | **DE.CM-1** ネットワーク監視 | Kafkaストリーム監視が稼働中か | Kafka接続状態 |
| 2 | **DE.CM-3** 人的活動の監視 | 監査ログが有効か | 監査ログ稼働状態 |
| 3 | **DE.CM-4** 不正コード検知 | IoC照合が有効か | IoC登録数 > 0 |
| 4 | **DE.CM-7** 未認可接続の監視 | ML異常検知が稼働中か | モデル状態 |
| 5 | **PR.AC-1** 認証情報管理 | JWT認証が有効か | 認証機能状態 |
| 6 | **RS.RP-1** インシデント対応 | プレイブック実行可能か | エンジン状態 |

### チェック結果例

```json
{
  "nist_csf": {
    "DE.CM-1": {
      "status": "compliant",
      "details": "Kafkaストリーム監視が稼働中。接続ブローカー数: 1"
    },
    "DE.CM-3": {
      "status": "compliant",
      "details": "監査ログ記録中。除外: /health エンドポイント"
    },
    "DE.CM-4": {
      "status": "compliant",
      "details": "IoC照合エンジン稼働中。登録IoC数: 1,500件"
    },
    "DE.CM-7": {
      "status": "compliant",
      "details": "Isolation Forest MLモデル稼働中"
    },
    "PR.AC-1": {
      "status": "compliant",
      "details": "JWT認証有効。RBAC: 3ロール定義済"
    },
    "RS.RP-1": {
      "status": "compliant",
      "details": "プレイブックエンジン稼働中。自動実行可能"
    }
  },
  "nist_csf_score": 100.0
}
```

---

## 📊 スコア計算方法

### ステータス定義

| ステータス | スコア | 意味 | アイコン |
|-----------|:------:|------|:-------:|
| `compliant` | **100%** | 完全に準拠 | ✅ |
| `partial` | **50%** | 部分的に準拠 | 🔶 |
| `non_compliant` | **0%** | 未準拠 | ❌ |

### 計算式

```
フレームワークスコア = (各項目スコアの合計) / (項目数) × 100

ISO 27001 スコア例:
  A.8.5  = compliant   = 100%
  A.8.15 = compliant   = 100%
  A.8.16 = partial     =  50%
  A.9.1  = compliant   = 100%
  A.5.25 = compliant   = 100%
  ────────────────────────────
  スコア = (100+100+50+100+100) / 5 = 90.0%

全体スコア = (ISO27001スコア + NIST CSFスコア) / 2
```

### スコア判定基準

| スコア範囲 | 判定 | 推奨アクション |
|-----------|------|-------------|
| 🟢 90-100% | 優良 | 現状維持、定期チェック継続 |
| 🟡 70-89% | 要改善 | 非準拠項目の改善計画策定 |
| 🟠 50-69% | 要注意 | 即座に改善着手 |
| 🔴 0-49% | 危険 | 緊急対応必要 |

---

## 🔄 定期実行ガイド

### 推奨実行頻度

| 頻度 | 用途 | 方法 |
|------|------|------|
| **週次** | 定期コンプライアンスチェック | cron / 手動 |
| **月次** | 月次レポート作成 | cron + レポート出力 |
| **四半期** | 監査対応 | 手動 + 詳細レビュー |
| **変更時** | デプロイ後確認 | CI/CDパイプライン |

### cron設定例

```bash
# 毎週月曜 9:00 にコンプライアンスチェック実行
0 9 * * 1 /opt/scripts/compliance-check.sh

# スクリプト例
#!/bin/bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/token \
  -d "username=admin&password=admin" | jq -r '.access_token')

RESULT=$(curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/compliance/check)

SCORE=$(echo $RESULT | jq '.overall_score')

echo "[$(date)] Compliance Score: ${SCORE}%"

# スコアが90%未満の場合アラート
if (( $(echo "$SCORE < 90" | bc -l) )); then
  echo "⚠️ Compliance score below threshold: ${SCORE}%"
  # 通知処理を追加
fi
```

### CI/CDパイプラインへの組み込み

```yaml
# .github/workflows/compliance-check.yml
name: Compliance Check
on:
  schedule:
    - cron: '0 0 * * 1'  # 毎週月曜
  workflow_dispatch:       # 手動実行

jobs:
  compliance:
    runs-on: ubuntu-latest
    steps:
      - name: Run Compliance Check
        run: |
          TOKEN=$(curl -s -X POST $API_URL/auth/token \
            -d "username=$ADMIN_USER&password=$ADMIN_PASS" | jq -r '.access_token')

          RESULT=$(curl -s -H "Authorization: Bearer $TOKEN" \
            $API_URL/api/v1/compliance/check)

          echo "$RESULT" | jq .

          SCORE=$(echo "$RESULT" | jq '.overall_score')
          if (( $(echo "$SCORE < 90" | bc -l) )); then
            echo "::error::Compliance score below 90%: ${SCORE}%"
            exit 1
          fi
```

---

## 📈 レポート活用

### レポートテンプレート

```
══════════════════════════════════════════
  コンプライアンスチェック レポート
══════════════════════════════════════════

■ 実行日時: 2026-03-24 10:00:00 JST
■ 実行者: admin

■ 全体スコア: 95.0%  🟢

■ ISO 27001 スコア: 100.0%
  ✅ A.8.5  セキュアな認証        compliant
  ✅ A.8.15 ログ取得              compliant
  ✅ A.8.16 監視活動              compliant
  ✅ A.9.1  アクセス制御方針       compliant
  ✅ A.5.25 インシデント管理       compliant

■ NIST CSF スコア: 90.0%
  ✅ DE.CM-1 ネットワーク監視      compliant
  ✅ DE.CM-3 人的活動の監視        compliant
  🔶 DE.CM-4 不正コード検知        partial
  ✅ DE.CM-7 未認可接続の監視      compliant
  ✅ PR.AC-1 認証情報管理          compliant
  ✅ RS.RP-1 インシデント対応       compliant

■ 要改善項目:
  ・DE.CM-4: IoC登録数が推奨値(1000件)未満

■ 推奨アクション:
  ・脅威フィードの追加登録
══════════════════════════════════════════
```

### スコア推移のモニタリング

| 指標 | Q1 2026 | Q2 2026 (目標) | Q3 2026 (目標) | Q4 2026 (目標) |
|------|:-------:|:-----------:|:-----------:|:-----------:|
| ISO 27001 | 100% | 100% | 100% | 100% |
| NIST CSF | 90% | 95% | 98% | 100% |
| 全体 | 95% | 97.5% | 99% | 100% |

### Grafanaダッシュボード連携

コンプライアンスチェック結果をGrafanaダッシュボードで可視化できます。

```
┌─────────────────────────────────────┐
│  📊 Compliance Score Trend          │
│                                     │
│  100% ─────────────●────●────●      │
│   90% ──●────●────                  │
│   80%                               │
│   70%                               │
│        W1   W2   W3   W4   W5      │
│                                     │
│  ── ISO 27001  ── NIST CSF         │
└─────────────────────────────────────┘
```
