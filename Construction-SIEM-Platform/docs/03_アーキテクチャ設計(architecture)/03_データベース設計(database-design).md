# 💾 データベース設計書

> Elasticsearch インデックス設計および ILM ポリシーを定義する

---

## 📊 設計概要

本システムでは **Elasticsearch 8.x** をプライマリストレージとして使用し、セキュリティイベントおよびアラートデータを格納する。

| インデックス | 用途 | パターン | ILM 適用 |
|-------------|------|---------|:--------:|
| 📥 siem-events | CLF 正規化イベント | `siem-events-YYYY.MM.DD` | ✅ |
| 🚨 siem-alerts | アラートデータ | `siem-alerts` | ✅ |

---

## 📥 siem-events インデックス

### インデックスパターン

```
siem-events-YYYY.MM.DD
```

日付ベースのローリングインデックス。1日1インデックスを自動生成する。

### マッピング定義

| フィールド | 型 | 説明 | 例 |
|-----------|-----|------|-----|
| `@timestamp` | `date` | イベント発生タイムスタンプ (ISO 8601) | `2026-03-24T10:30:00.000Z` |
| `event_id` | `keyword` | イベント一意識別子 (UUID) | `a1b2c3d4-e5f6-...` |
| `source_ip` | `ip` | イベント発生元 IP アドレス | `192.168.1.100` |
| `dest_ip` | `ip` | 宛先 IP アドレス | `10.0.0.50` |
| `event_type` | `keyword` | イベント種別 | `authentication_failure` |
| `severity` | `keyword` | セベリティ (critical/high/medium/low/info) | `high` |
| `device_id` | `keyword` | デバイス識別子 | `iot-sensor-042` |
| `user_id` | `keyword` | ユーザー識別子 | `user@example.com` |
| `action` | `keyword` | 実行アクション | `login_attempt` |
| `outcome` | `keyword` | 結果 (success/failure) | `failure` |
| `hostname` | `keyword` | ホスト名 | `web-server-01` |
| `port` | `integer` | ポート番号 | `443` |
| `protocol` | `keyword` | プロトコル | `tcp` |
| `file_hash` | `keyword` | ファイルハッシュ (SHA256) | `a1b2c3...` |
| `file_name` | `keyword` | ファイル名 | `design.dwg` |
| `url` | `text` | URL | `https://example.com/api` |
| `geo_location` | `geo_point` | 地理情報 | `{"lat": 35.68, "lon": 139.69}` |
| `raw_log` | `text` | 元のログメッセージ | 正規化前の生ログ |
| `tags` | `keyword` (配列) | タグ | `["iot", "construction-site-a"]` |
| `details` | `object` | 追加詳細情報 (JSON) | `{"attempts": 5}` |
| `normalized_by` | `keyword` | 正規化モジュール名 | `normalizer-v2` |
| `ingested_at` | `date` | Elasticsearch 格納タイムスタンプ | `2026-03-24T10:30:05.000Z` |

### インデックス設定

```json
{
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 1,
    "index.lifecycle.name": "siem-events-policy",
    "index.lifecycle.rollover_alias": "siem-events",
    "refresh_interval": "5s"
  }
}
```

| 設定項目 | 値 | 説明 |
|---------|-----|------|
| 🔹 シャード数 | 3 | データ分散・並列検索用 |
| 🔹 レプリカ数 | 1 | 冗長化（各シャード1レプリカ） |
| 🔹 リフレッシュ間隔 | 5秒 | 検索可能になるまでの遅延 |
| 🔹 ILM ポリシー | `siem-events-policy` | ライフサイクル管理 |

---

## 🚨 siem-alerts インデックス

### マッピング定義

| フィールド | 型 | 説明 | 例 |
|-----------|-----|------|-----|
| `@timestamp` | `date` | アラート生成タイムスタンプ | `2026-03-24T10:32:00.000Z` |
| `alert_id` | `keyword` | アラート一意識別子 (UUID) | `b2c3d4e5-f6a7-...` |
| `title` | `text` | アラートタイトル | `ブルートフォース攻撃検知` |
| `description` | `text` | アラート詳細説明 | `同一IPから10回の認証失敗を検知` |
| `severity` | `keyword` | セベリティ | `high` |
| `status` | `keyword` | ステータス (open/acknowledged/resolved) | `open` |
| `rule_id` | `keyword` | トリガーしたルール ID | `DET-002` |
| `rule_name` | `keyword` | ルール名 | `brute_force_detection` |
| `source_ip` | `ip` | 攻撃元 IP | `203.0.113.50` |
| `dest_ip` | `ip` | 攻撃先 IP | `192.168.1.10` |
| `event_ids` | `keyword` (配列) | 関連イベント ID リスト | `["a1b2...", "c3d4..."]` |
| `event_count` | `integer` | 関連イベント数 | `10` |
| `mitre_tactic` | `keyword` | MITRE ATT&CK 戦術 | `Credential Access` |
| `mitre_technique` | `keyword` | MITRE ATT&CK 技術 | `T1110 Brute Force` |
| `kill_chain_stage` | `keyword` | キルチェーンステージ | `exploitation` |
| `ioc_matches` | `object` (配列) | マッチした IoC 情報 | `[{"type": "ip", "value": "..."}]` |
| `ml_score` | `float` | ML 異常スコア (0.0-1.0) | `0.95` |
| `assigned_to` | `keyword` | 担当者 | `analyst@example.com` |
| `incident_id` | `keyword` | 紐付けインシデント ID | `INC-2026-001` |
| `playbook_executed` | `keyword` (配列) | 実行済みプレイブック | `["ransomware_response"]` |
| `resolved_at` | `date` | 解決タイムスタンプ | `2026-03-24T11:00:00.000Z` |
| `resolution_note` | `text` | 解決メモ | `IP ブロック実施済み` |
| `tags` | `keyword` (配列) | タグ | `["brute-force", "external"]` |

### インデックス設定

```json
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 1,
    "index.lifecycle.name": "siem-alerts-policy",
    "refresh_interval": "1s"
  }
}
```

| 設定項目 | 値 | 説明 |
|---------|-----|------|
| 🔹 シャード数 | 1 | アラートはイベントより少量 |
| 🔹 レプリカ数 | 1 | 冗長化 |
| 🔹 リフレッシュ間隔 | 1秒 | リアルタイム性重視 |
| 🔹 ILM ポリシー | `siem-alerts-policy` | ライフサイクル管理 |

---

## 🔄 ILM（Index Lifecycle Management）ポリシー

### siem-events-policy

セキュリティイベントのライフサイクル管理。

```mermaid
graph LR
    HOT[🔥 Hot<br/>7日間] --> WARM[🟡 Warm<br/>30日間]
    WARM --> COLD[❄️ Cold<br/>90日間]
    COLD --> DEL[🗑 Delete]
```

| フェーズ | 期間 | ストレージ | 設定 |
|:--------:|:----:|-----------|------|
| 🔥 **Hot** | 0〜7日 | 高速 SSD | フルインデックス、リアルタイム検索 |
| 🟡 **Warm** | 8〜37日 | 標準 SSD | レプリカ数削減(0)、フォースマージ |
| ❄️ **Cold** | 38〜127日 | HDD | 読取専用、シュリンク |
| 🗑 **Delete** | 128日〜 | — | インデックス削除 |

### ILM ポリシー定義（siem-events-policy）

```json
{
  "policy": {
    "phases": {
      "hot": {
        "min_age": "0ms",
        "actions": {
          "rollover": {
            "max_age": "1d",
            "max_size": "50gb"
          },
          "set_priority": {
            "priority": 100
          }
        }
      },
      "warm": {
        "min_age": "7d",
        "actions": {
          "shrink": {
            "number_of_shards": 1
          },
          "forcemerge": {
            "max_num_segments": 1
          },
          "allocate": {
            "number_of_replicas": 0
          },
          "set_priority": {
            "priority": 50
          }
        }
      },
      "cold": {
        "min_age": "30d",
        "actions": {
          "readonly": {},
          "set_priority": {
            "priority": 0
          }
        }
      },
      "delete": {
        "min_age": "90d",
        "actions": {
          "delete": {}
        }
      }
    }
  }
}
```

### siem-alerts-policy

アラートデータは長期保持が必要なため、削除フェーズの期間が長い。

| フェーズ | 期間 | 設定 |
|:--------:|:----:|------|
| 🔥 **Hot** | 0〜30日 | フルインデックス |
| 🟡 **Warm** | 31〜180日 | レプリカ削減 |
| ❄️ **Cold** | 181〜365日 | 読取専用 |
| 🗑 **Delete** | 366日〜 | 削除 |

---

## 📊 インデックステンプレート

### siem-events テンプレート

```json
{
  "index_patterns": ["siem-events-*"],
  "template": {
    "settings": {
      "number_of_shards": 3,
      "number_of_replicas": 1,
      "index.lifecycle.name": "siem-events-policy"
    },
    "mappings": {
      "properties": {
        "@timestamp": { "type": "date" },
        "event_id": { "type": "keyword" },
        "source_ip": { "type": "ip" },
        "dest_ip": { "type": "ip" },
        "event_type": { "type": "keyword" },
        "severity": { "type": "keyword" },
        "device_id": { "type": "keyword" },
        "user_id": { "type": "keyword" },
        "action": { "type": "keyword" },
        "outcome": { "type": "keyword" },
        "hostname": { "type": "keyword" },
        "port": { "type": "integer" },
        "protocol": { "type": "keyword" },
        "file_hash": { "type": "keyword" },
        "file_name": { "type": "keyword" },
        "url": { "type": "text" },
        "geo_location": { "type": "geo_point" },
        "raw_log": { "type": "text", "index": false },
        "tags": { "type": "keyword" },
        "details": { "type": "object", "enabled": true },
        "normalized_by": { "type": "keyword" },
        "ingested_at": { "type": "date" }
      }
    }
  },
  "priority": 200
}
```

---

## 🔍 主要クエリパターン

### 時間範囲検索

| ユースケース | クエリ条件 | 想定レスポンス |
|-------------|-----------|:-------------:|
| 📊 直近1時間のイベント | `@timestamp` range + `severity` filter | < 5秒 |
| 🔍 特定 IP の履歴 | `source_ip` term + 時間範囲 | < 10秒 |
| 📐 CAD ファイルアクセス | `event_type` + `file_name` wildcard | < 15秒 |
| 🔗 相関分析 | 複数フィールド aggregation | < 30秒 |

### インデックスパフォーマンス考慮事項

| 項目 | 設定 | 理由 |
|------|------|------|
| 🔹 `raw_log` を `index: false` | 非検索対象 | ストレージ・インデックスサイズ削減 |
| 🔹 `keyword` 型の活用 | 完全一致検索用 | フィルタリング・集約の高速化 |
| 🔹 `ip` 型の使用 | IP 範囲検索対応 | CIDR 検索の最適化 |
| 🔹 日別インデックス | 時間範囲での枝刈り | 不要なシャードへのアクセス回避 |

---

## 📈 容量計画

### イベント1件のサイズ見積もり

| フィールド群 | 平均サイズ |
|-------------|:---------:|
| 固定フィールド（timestamp, severity 等） | ~200 bytes |
| IP フィールド | ~40 bytes |
| テキストフィールド（url, raw_log） | ~300 bytes |
| オブジェクトフィールド（details） | ~100 bytes |
| **合計（平均）** | **~640 bytes** |

### 月間ストレージ見積もり

| 指標 | 値 |
|------|-----|
| 📥 EPS | 10,000 |
| 📅 日間イベント数 | 864,000,000 |
| 💾 日間データ量（raw） | ~553 GB |
| 💾 日間データ量（圧縮後、インデックス含む） | ~500 GB |
| 📅 月間データ量（hot+warm） | ~15 TB |
| 📅 3ヶ月データ量（全フェーズ） | ~45 TB |

---

## 🔗 関連ドキュメント

- [システムアーキテクチャ](./01_システムアーキテクチャ(system-architecture).md)
- [データフロー設計](./02_データフロー設計(data-flow).md)
- [非機能要件](../02_要件定義(requirements)/02_非機能要件(non-functional-requirements).md)
