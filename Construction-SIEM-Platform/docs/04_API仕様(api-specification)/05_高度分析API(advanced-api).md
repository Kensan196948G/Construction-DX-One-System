# 🔬 高度分析API（Advanced API）

> 脅威インテリジェンス・相関分析・KPI・コンプライアンス・通知・監査

---

## 📋 エンドポイント総覧

| カテゴリ | プレフィックス | エンドポイント数 |
|----------|---------------|:---------------:|
| 🛡 脅威インテリジェンス | `/api/v1/threat-intel/*` | 4 |
| 🔗 相関分析 | `/api/v1/correlation/*` | 2 |
| 📊 KPI | `/api/v1/kpi/*` | 3 |
| ✅ コンプライアンス | `/api/v1/compliance/*` | 2 |
| 📥 データ検証 | `/api/v1/data/*` | 2 |
| 🔔 通知 | `/api/v1/notifications/*` | 2 |
| 📝 監査 | `/api/v1/audit/*` | 2 |

---

## 🛡 脅威インテリジェンス（Threat Intelligence）

### エンドポイント一覧

| メソッド | パス | ロール | 説明 |
|----------|------|--------|------|
| `GET` | `/api/v1/threat-intel/ioc` | 全ロール | IoC一覧取得 |
| `POST` | `/api/v1/threat-intel/ioc` | admin, analyst | IoC登録 |
| `POST` | `/api/v1/threat-intel/match` | admin, analyst | IoC照合 |
| `GET` | `/api/v1/threat-intel/feeds` | 全ロール | フィード一覧 |

### POST /api/v1/threat-intel/ioc — IoC登録

#### リクエスト例

```json
{
  "type": "ip",
  "value": "203.0.113.50",
  "threat_type": "c2_server",
  "confidence": 85,
  "source": "internal_analysis",
  "description": "建設現場ネットワークからのC2通信先",
  "tags": ["apt", "construction-target"],
  "expiry": "2026-06-24T00:00:00Z"
}
```

#### IoC タイプ一覧

| タイプ | 説明 | 例 |
|--------|------|------|
| `ip` | IPアドレス | `203.0.113.50` |
| `domain` | ドメイン名 | `malware.example.com` |
| `hash_md5` | MD5ハッシュ | `d41d8cd98f00b204e9800998ecf8427e` |
| `hash_sha256` | SHA256ハッシュ | `e3b0c44298fc1c149afbf4...` |
| `url` | URL | `https://evil.example.com/payload` |
| `email` | メールアドレス | `phish@evil.example.com` |

#### レスポンス例（201 Created）

```json
{
  "status": "success",
  "data": {
    "id": "ioc-001",
    "type": "ip",
    "value": "203.0.113.50",
    "threat_type": "c2_server",
    "confidence": 85,
    "created_at": "2026-03-24T10:00:00Z"
  }
}
```

### POST /api/v1/threat-intel/match — IoC照合

#### リクエスト例

```json
{
  "indicators": [
    {"type": "ip", "value": "203.0.113.50"},
    {"type": "domain", "value": "safe.example.com"},
    {"type": "hash_sha256", "value": "e3b0c44298fc1c149afbf4..."}
  ]
}
```

#### レスポンス例（200 OK）

```json
{
  "status": "success",
  "data": {
    "matches": [
      {
        "indicator": {"type": "ip", "value": "203.0.113.50"},
        "matched": true,
        "ioc_id": "ioc-001",
        "threat_type": "c2_server",
        "confidence": 85
      }
    ],
    "total_checked": 3,
    "total_matched": 1,
    "match_rate": 33.3
  }
}
```

---

## 🔗 相関分析（Correlation Analysis）

### エンドポイント一覧

| メソッド | パス | ロール | 説明 |
|----------|------|--------|------|
| `POST` | `/api/v1/correlation/analyze` | admin, analyst | 相関分析実行 |
| `GET` | `/api/v1/correlation/rules` | 全ロール | 相関ルール一覧 |

### POST /api/v1/correlation/analyze — 相関分析実行

> MITRE ATT&CK キルチェーンに基づく相関分析を実行します。

#### リクエスト例

```json
{
  "alert_ids": ["alert-001", "alert-002", "alert-003"],
  "time_window": "24h",
  "analysis_type": "kill_chain"
}
```

#### レスポンス例（200 OK）

```json
{
  "status": "success",
  "data": {
    "correlation_id": "corr-001",
    "kill_chain": {
      "reconnaissance": {
        "detected": true,
        "alerts": ["alert-001"],
        "techniques": ["T1046"]
      },
      "initial_access": {
        "detected": false,
        "alerts": [],
        "techniques": []
      },
      "execution": {
        "detected": true,
        "alerts": ["alert-002"],
        "techniques": ["T1059"]
      },
      "lateral_movement": {
        "detected": true,
        "alerts": ["alert-003"],
        "techniques": ["T1021"]
      },
      "impact": {
        "detected": false,
        "alerts": [],
        "techniques": []
      }
    },
    "risk_score": 82,
    "risk_level": "high",
    "recommendation": "キルチェーンの3段階が検出されました。横展開の封じ込めを優先してください。",
    "analyzed_at": "2026-03-24T10:05:00Z"
  }
}
```

---

## 📊 KPI ダッシュボード

### エンドポイント一覧

| メソッド | パス | ロール | 説明 |
|----------|------|--------|------|
| `GET` | `/api/v1/kpi/dashboard` | 全ロール | KPIダッシュボード |
| `GET` | `/api/v1/kpi/mttd` | 全ロール | MTTD詳細 |
| `GET` | `/api/v1/kpi/mttr` | 全ロール | MTTR詳細 |

### GET /api/v1/kpi/dashboard — KPIダッシュボード

> MTTD（平均検出時間）・MTTR（平均対応時間）・SLA遵守率を自動計算します。

#### レスポンス例（200 OK）

```json
{
  "status": "success",
  "data": {
    "mttd": {
      "average_minutes": 4.2,
      "target_minutes": 5.0,
      "status": "on_target",
      "trend": "improving"
    },
    "mttr": {
      "average_minutes": 45.8,
      "target_minutes": 60.0,
      "status": "on_target",
      "trend": "stable"
    },
    "sla_compliance": {
      "response_rate": 95.2,
      "resolution_rate": 88.7,
      "target_rate": 95.0
    },
    "alert_volume": {
      "today": 23,
      "this_week": 156,
      "this_month": 612,
      "trend": "decreasing"
    },
    "top_attack_types": [
      {"technique": "T1110", "name": "Brute Force", "count": 45},
      {"technique": "T1046", "name": "Network Service Scanning", "count": 32},
      {"technique": "T1059", "name": "Command and Scripting Interpreter", "count": 18}
    ],
    "period": {
      "start": "2026-03-01T00:00:00Z",
      "end": "2026-03-24T23:59:59Z"
    }
  }
}
```

---

## ✅ コンプライアンス（Compliance）

### エンドポイント一覧

| メソッド | パス | ロール | 説明 |
|----------|------|--------|------|
| `POST` | `/api/v1/compliance/check` | admin | コンプライアンスチェック実行 |
| `GET` | `/api/v1/compliance/report` | admin, analyst | レポート取得 |

### POST /api/v1/compliance/check — コンプライアンスチェック

> ISO 27001 および NIST CSF フレームワークに基づくチェックを実行します。

#### リクエスト例

```json
{
  "frameworks": ["iso27001", "nist_csf"],
  "scope": "full"
}
```

#### レスポンス例（200 OK）

```json
{
  "status": "success",
  "data": {
    "check_id": "comp-001",
    "results": {
      "iso27001": {
        "overall_score": 87.5,
        "status": "compliant",
        "controls": {
          "A.5_Information_Security_Policies": {"score": 95, "status": "pass"},
          "A.6_Organization_of_Information_Security": {"score": 88, "status": "pass"},
          "A.12_Operations_Security": {"score": 82, "status": "pass"},
          "A.16_Information_Security_Incident_Management": {"score": 90, "status": "pass"},
          "A.18_Compliance": {"score": 78, "status": "warning"}
        }
      },
      "nist_csf": {
        "overall_score": 84.2,
        "status": "compliant",
        "functions": {
          "identify": {"score": 88, "status": "pass"},
          "protect": {"score": 85, "status": "pass"},
          "detect": {"score": 92, "status": "pass"},
          "respond": {"score": 80, "status": "pass"},
          "recover": {"score": 76, "status": "warning"}
        }
      }
    },
    "recommendations": [
      "A.18_Compliance: 外部監査スケジュールの見直しを推奨",
      "NIST Recover: 災害復旧計画のテスト頻度を増やすことを推奨"
    ],
    "checked_at": "2026-03-24T10:00:00Z"
  }
}
```

---

## 📥 データ検証（Data Validation）

### エンドポイント一覧

| メソッド | パス | ロール | 説明 |
|----------|------|--------|------|
| `POST` | `/api/v1/data/validate` | admin, analyst | データバリデーション |
| `POST` | `/api/v1/data/batch-ingest` | admin | バッチインジェスト |

### POST /api/v1/data/validate — データバリデーション

#### リクエスト例

```json
{
  "data_type": "syslog",
  "records": [
    {
      "timestamp": "2026-03-24T08:00:00Z",
      "source": "firewall",
      "message": "DROP IN=eth0 SRC=192.168.1.100 DST=10.0.0.1 ..."
    }
  ]
}
```

#### レスポンス例（200 OK）

```json
{
  "status": "success",
  "data": {
    "total_records": 1,
    "valid": 1,
    "invalid": 0,
    "validation_details": [
      {
        "index": 0,
        "status": "valid",
        "parsed_fields": {
          "timestamp": "2026-03-24T08:00:00Z",
          "source": "firewall",
          "action": "DROP",
          "src_ip": "192.168.1.100",
          "dst_ip": "10.0.0.1"
        }
      }
    ]
  }
}
```

### POST /api/v1/data/batch-ingest — バッチインジェスト

#### リクエスト例

```json
{
  "data_type": "alerts",
  "records": [
    {
      "title": "アラート1",
      "severity": "high",
      "source": "firewall",
      "description": "..."
    },
    {
      "title": "アラート2",
      "severity": "medium",
      "source": "ids",
      "description": "..."
    }
  ]
}
```

#### レスポンス例（202 Accepted）

```json
{
  "status": "success",
  "data": {
    "batch_id": "batch-001",
    "total_records": 2,
    "accepted": 2,
    "rejected": 0,
    "status": "processing"
  },
  "message": "バッチインジェストを受け付けました。処理状況は batch_id で確認できます。"
}
```

---

## 🔔 通知（Notifications）

### エンドポイント一覧

| メソッド | パス | ロール | 説明 |
|----------|------|--------|------|
| `POST` | `/api/v1/notifications/send` | admin, analyst | 通知送信 |
| `GET` | `/api/v1/notifications/channels` | admin | チャネル一覧 |

### POST /api/v1/notifications/send — 通知送信

> Microsoft Teams / Slack / Webhook への通知を送信します。

#### リクエスト例

```json
{
  "channels": ["teams", "slack"],
  "priority": "high",
  "title": "P1インシデント発生",
  "message": "東京建設現場Aでランサムウェア感染の疑いが検出されました。",
  "incident_id": "INC-2026-0042",
  "mention": ["@security-team"]
}
```

#### レスポンス例（200 OK）

```json
{
  "status": "success",
  "data": {
    "notification_id": "notif-001",
    "results": {
      "teams": {"status": "sent", "message_id": "teams-msg-001"},
      "slack": {"status": "sent", "message_id": "slack-msg-001"}
    },
    "sent_at": "2026-03-24T10:00:00Z"
  }
}
```

#### 通知チャネル設定

| チャネル | 環境変数 | 説明 |
|----------|---------|------|
| 🟦 Teams | `TEAMS_WEBHOOK_URL` | Microsoft Teams Incoming Webhook |
| 🟪 Slack | `SLACK_WEBHOOK_URL` | Slack Incoming Webhook |
| 🔗 Webhook | `CUSTOM_WEBHOOK_URL` | カスタムWebhook（POST） |

---

## 📝 監査（Audit）

### エンドポイント一覧

| メソッド | パス | ロール | 説明 |
|----------|------|--------|------|
| `GET` | `/api/v1/audit/logs` | admin | 監査ログ取得 |
| `GET` | `/api/v1/audit/stats` | admin | 監査統計 |

### GET /api/v1/audit/logs — 監査ログ取得

#### クエリパラメータ

| パラメータ | 型 | 説明 |
|------------|------|------|
| `user` | string | ユーザーフィルター |
| `action` | string | アクションフィルター（`login`, `create`, `update`, `delete`, `acknowledge`） |
| `resource` | string | リソースフィルター（`alert`, `incident`, `user`, `setting`） |
| `start_date` | datetime | 開始日時 |
| `end_date` | datetime | 終了日時 |
| `page` | int | ページ番号 |
| `per_page` | int | 件数 |

#### レスポンス例（200 OK）

```json
{
  "status": "success",
  "data": [
    {
      "id": "audit-001",
      "timestamp": "2026-03-24T08:20:00Z",
      "user": "analyst01",
      "action": "acknowledge",
      "resource": "alert",
      "resource_id": "alert-001",
      "detail": "アラートを承認",
      "ip_address": "192.168.10.5",
      "user_agent": "Mozilla/5.0 ..."
    }
  ],
  "meta": {
    "total": 1250,
    "page": 1,
    "per_page": 20
  }
}
```

### GET /api/v1/audit/stats — 監査統計

#### レスポンス例（200 OK）

```json
{
  "status": "success",
  "data": {
    "by_action": {
      "login": 450,
      "create": 120,
      "update": 380,
      "delete": 15,
      "acknowledge": 285
    },
    "by_user": {
      "admin": 200,
      "analyst01": 450,
      "analyst02": 380,
      "viewer01": 120
    },
    "by_resource": {
      "alert": 680,
      "incident": 320,
      "user": 50,
      "setting": 30
    },
    "period": {
      "start": "2026-03-01T00:00:00Z",
      "end": "2026-03-24T23:59:59Z"
    }
  }
}
```
