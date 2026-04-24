# 🕵️ 脅威インテリジェンス運用

> IoC（Indicator of Compromise）管理と脅威フィード運用手順

---

## 📋 目次

1. [IoC管理概要](#ioc管理概要)
2. [フィードローダー](#フィードローダー)
3. [照合エンジン](#照合エンジン)
4. [API仕様](#api仕様)
5. [運用手順](#運用手順)

---

## 🗂 IoC管理概要

### IoC（Indicator of Compromise）タイプ

| タイプ | 説明 | 例 | 用途 |
|--------|------|-----|------|
| 🌐 `ip` | 不正IPアドレス | `203.0.113.50` | C2サーバー、スキャナー検知 |
| 🔗 `domain` | 不正ドメイン | `malware.example.com` | フィッシング、マルウェア配布 |
| 🔑 `hash` | ファイルハッシュ | `d41d8cd98f00b204e9800998ecf8427e` | マルウェア検体照合 |
| 🌍 `url` | 不正URL | `https://evil.example.com/payload` | 不正ダウンロード先 |

### データモデル

```
IoC
├── id: UUID
├── type: ip | domain | hash | url
├── value: string（IoC値）
├── source: string（フィードソース名）
├── severity: 1-10
├── description: string
├── tags: list[string]
├── created_at: datetime
├── updated_at: datetime
└── is_active: bool
```

### 保存方式

| 環境 | ストレージ | 特徴 |
|------|-----------|------|
| 開発 | インメモリ（dict） | 高速、再起動で消失 |
| 本番 | Elasticsearch | 永続化、全文検索対応 |

---

## 📥 フィードローダー

### 対応フォーマット

| フォーマット | 拡張子 | 説明 |
|-------------|--------|------|
| YAML | `.yaml` / `.yml` | 人間が読みやすい形式 |
| JSON | `.json` | API連携向け |

### YAMLフィード例

```yaml
feed_name: "construction-threat-feed"
feed_version: "1.0"
last_updated: "2026-03-24T00:00:00Z"
indicators:
  - type: ip
    value: "203.0.113.50"
    severity: 8
    description: "C2 Server - Construction sector targeting"
    tags: ["apt", "construction", "c2"]
  - type: domain
    value: "malware-cdn.example.com"
    severity: 9
    description: "Malware distribution domain"
    tags: ["malware", "distribution"]
  - type: hash
    value: "e99a18c428cb38d5f260853678922e03"
    severity: 7
    description: "Known ransomware variant"
    tags: ["ransomware", "filelocker"]
```

### JSONフィード例

```json
{
  "feed_name": "external-threat-feed",
  "indicators": [
    {
      "type": "url",
      "value": "https://evil.example.com/exploit",
      "severity": 9,
      "description": "Exploit kit landing page"
    }
  ]
}
```

### フィードロード手順

```
1. フィードファイルを配置
   └── threat_feeds/
       ├── construction-feed.yaml
       ├── external-feed.json
       └── custom-feed.yaml

2. API経由でロード
   POST /api/v1/threat-intel/feeds/load
   {
     "file_path": "threat_feeds/construction-feed.yaml"
   }

3. 結果確認
   GET /api/v1/threat-intel/indicators?source=construction-threat-feed
```

---

## ⚡ 照合エンジン

### アルゴリズム

```
照合方式: O(1) ハッシュルックアップ

内部構造:
┌──────────────────────────┐
│  IoC インデックス          │
│                          │
│  ip_index: {             │
│    "203.0.113.50": IoC,  │
│    "198.51.100.1": IoC   │
│  }                       │
│                          │
│  domain_index: {         │
│    "evil.com": IoC       │
│  }                       │
│                          │
│  hash_index: { ... }     │
│  url_index:  { ... }     │
└──────────────────────────┘

検索時間計算量: O(1) 平均
```

### 照合フロー

```
セキュリティイベント
    │
    ▼
┌─────────────┐
│ source_ip   │──► ip_index で照合
├─────────────┤
│ dest_ip     │──► ip_index で照合
├─────────────┤
│ domain      │──► domain_index で照合
├─────────────┤
│ file_hash   │──► hash_index で照合
├─────────────┤
│ url         │──► url_index で照合
└─────────────┘
    │
    ▼
マッチ → アラート生成 + severity付与
不一致 → 通常処理続行
```

### パフォーマンス

| 指標 | 値 |
|------|-----|
| 単一照合 | < 1ms |
| イベント全体照合 | < 5ms（5フィールド照合時） |
| 最大IoC数 | 100万件（インメモリ時） |
| メモリ使用量 | 約100MB / 100万IoC |

---

## 🔌 API仕様

### エンドポイント一覧

| メソッド | パス | 説明 | 権限 |
|---------|------|------|------|
| `GET` | `/api/v1/threat-intel/indicators` | IoC一覧取得 | analyst+ |
| `POST` | `/api/v1/threat-intel/indicators` | IoC追加 | analyst+ |
| `GET` | `/api/v1/threat-intel/indicators/{id}` | IoC詳細取得 | analyst+ |
| `PUT` | `/api/v1/threat-intel/indicators/{id}` | IoC更新 | analyst+ |
| `DELETE` | `/api/v1/threat-intel/indicators/{id}` | IoC削除 | admin |
| `POST` | `/api/v1/threat-intel/match` | 単一値照合 | analyst+ |
| `POST` | `/api/v1/threat-intel/match/event` | イベント全体照合 | analyst+ |
| `POST` | `/api/v1/threat-intel/feeds/load` | フィードロード | admin |
| `GET` | `/api/v1/threat-intel/stats` | 統計情報 | analyst+ |

### リクエスト/レスポンス例

#### IoC追加

```bash
POST /api/v1/threat-intel/indicators
Authorization: Bearer <token>

{
  "type": "ip",
  "value": "203.0.113.50",
  "severity": 8,
  "description": "C2サーバー",
  "tags": ["apt", "construction"]
}
```

#### 単一値照合

```bash
POST /api/v1/threat-intel/match
Authorization: Bearer <token>

{
  "type": "ip",
  "value": "203.0.113.50"
}
```

レスポンス:

```json
{
  "matched": true,
  "indicator": {
    "type": "ip",
    "value": "203.0.113.50",
    "severity": 8,
    "description": "C2サーバー"
  }
}
```

#### イベント全体照合

```bash
POST /api/v1/threat-intel/match/event
Authorization: Bearer <token>

{
  "source_ip": "203.0.113.50",
  "dest_ip": "10.0.0.1",
  "domain": "safe.example.com",
  "file_hash": null,
  "url": null
}
```

レスポンス:

```json
{
  "matches": [
    {
      "field": "source_ip",
      "indicator": {
        "type": "ip",
        "value": "203.0.113.50",
        "severity": 8
      }
    }
  ],
  "total_matches": 1,
  "max_severity": 8
}
```

---

## 📘 運用手順

### フィード更新サイクル

| フィードタイプ | 更新頻度 | 担当 | 方法 |
|--------------|---------|------|------|
| 商用脅威フィード | 毎日（自動） | システム | API連携 |
| OSINT フィード | 週次 | アナリスト | YAML/JSONロード |
| 業界固有フィード | 月次 | SOCリーダー | 手動レビュー後ロード |
| 自社検出IoC | 随時 | アナリスト | API経由で個別追加 |

### IoC追加手順

```
1. 脅威情報の入手
   └── 商用フィード / OSINT / 自社検出

2. IoC の検証
   ├── 誤検知チェック（自社IP範囲との照合）
   ├── 信頼度評価（ソースの信頼性）
   └── 重複チェック

3. IoC の登録
   ├── API: POST /api/v1/threat-intel/indicators
   └── バッチ: POST /api/v1/threat-intel/feeds/load

4. 有効性確認
   └── テストイベントで照合テスト

5. 監視開始
   └── 照合ヒット時のアラート確認
```

### IoC削除・無効化手順

```
1. 削除理由の確認
   ├── 期限切れ（90日以上経過）
   ├── 誤検知と判明
   └── 攻撃者のインフラ変更

2. 無効化（推奨）
   └── PUT /api/v1/threat-intel/indicators/{id}
       { "is_active": false }

3. 完全削除（必要時のみ）
   └── DELETE /api/v1/threat-intel/indicators/{id}
       ※ admin権限が必要

4. 監査ログ確認
   └── 削除操作が記録されていることを確認
```

### IoC品質管理

| 指標 | 目標値 | 測定方法 |
|------|--------|---------|
| 誤検知率 | < 5% | マッチ件数 vs 実インシデント |
| カバレッジ | > 80% | 検知インシデント / 全インシデント |
| 鮮度 | < 24時間 | フィード更新からロードまでの時間 |
| IoC総数 | 10,000+ | `/api/v1/threat-intel/stats` |
