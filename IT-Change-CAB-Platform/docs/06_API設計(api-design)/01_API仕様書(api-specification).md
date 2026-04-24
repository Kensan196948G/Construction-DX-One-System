# API仕様書
## IT変更管理・リリース自動化プラットフォーム（IT-Change-CAB-Platform）

| 項目 | 内容 |
|------|------|
| **文書番号** | API-SPEC-001 |
| **バージョン** | 1.0.0 |
| **作成日** | 2026-03-26 |
| **作成者** | みらい建設工業 IT部門 |
| **承認者** | IT部門長 |
| **対象リポジトリ** | Kensan196948G/IT-Change-CAB-Platform |

---

## 1. API設計方針

### 1.1 基本方針

| 項目 | 方針 |
|------|------|
| プロトコル | HTTPS (TLS 1.2以上) |
| スタイル | RESTful API |
| ベースURL | `/api/v1` |
| データ形式 | JSON (Content-Type: application/json) |
| 文字コード | UTF-8 |
| 日時形式 | ISO 8601 (YYYY-MM-DDTHH:mm:ssZ) |
| ページネーション | Offset方式（page, limit） |
| ソート | sort=field:asc/desc |
| フィルタ | クエリパラメータ方式 |
| バージョニング | URLパス方式 (/api/v1/) |
| ドキュメント | OpenAPI 3.0 (Swagger UI) |

### 1.2 認証

| 項目 | 内容 |
|------|------|
| 方式 | Bearer Token (JWT) |
| ヘッダー | `Authorization: Bearer <access_token>` |
| アクセストークン有効期限 | 1時間 |
| リフレッシュトークン有効期限 | 7日間 |
| トークンリフレッシュ | POST /api/v1/auth/refresh |

### 1.3 共通レスポンス形式

**成功レスポンス:**
```json
{
  "data": { ... },
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "totalPages": 5
  }
}
```

**エラーレスポンス:**
```json
{
  "error": {
    "code": "ERR_VALIDATION",
    "message": "入力値が不正です",
    "details": [
      { "field": "title", "message": "タイトルは必須です" }
    ],
    "timestamp": "2026-03-26T10:00:00Z",
    "requestId": "req_abc123"
  }
}
```

### 1.4 HTTPステータスコード

| コード | 用途 |
|--------|------|
| 200 | 成功（取得・更新） |
| 201 | 作成成功 |
| 204 | 削除成功（レスポンスボディなし） |
| 400 | バリデーションエラー |
| 401 | 認証エラー |
| 403 | 認可エラー（権限不足） |
| 404 | リソース未存在 |
| 409 | データ競合 |
| 422 | 処理不可（状態遷移エラー等） |
| 429 | レート制限超過 |
| 500 | 内部サーバーエラー |

---

## 2. 認証API

### 2.1 ログイン

| 項目 | 内容 |
|------|------|
| **メソッド** | POST |
| **エンドポイント** | /api/v1/auth/login |
| **認証** | 不要 |
| **レート制限** | 5回/分（IPベース） |

**リクエスト:**
```json
{
  "username": "yamada",
  "password": "P@ssw0rd123!"
}
```

**レスポンス (200):**
```json
{
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIs...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIs...",
    "expiresIn": 3600,
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "username": "yamada",
      "displayName": "山田太郎",
      "role": "requester",
      "department": "IT部門"
    }
  }
}
```

### 2.2 トークンリフレッシュ

| 項目 | 内容 |
|------|------|
| **メソッド** | POST |
| **エンドポイント** | /api/v1/auth/refresh |
| **認証** | refreshToken必須 |

**リクエスト:**
```json
{
  "refreshToken": "eyJhbGciOiJIUzI1NiIs..."
}
```

### 2.3 ログアウト

| 項目 | 内容 |
|------|------|
| **メソッド** | POST |
| **エンドポイント** | /api/v1/auth/logout |
| **認証** | 必須 |

### 2.4 現在のユーザ情報取得

| 項目 | 内容 |
|------|------|
| **メソッド** | GET |
| **エンドポイント** | /api/v1/auth/me |
| **認証** | 必須 |

---

## 3. RFC管理API

### 3.1 RFC一覧取得

| 項目 | 内容 |
|------|------|
| **メソッド** | GET |
| **エンドポイント** | /api/v1/rfcs |
| **認証** | 必須 |
| **権限** | 全ロール（表示範囲はロールに依存） |

**クエリパラメータ:**

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| page | integer | 任意 | ページ番号（デフォルト: 1） |
| limit | integer | 任意 | 件数（デフォルト: 20、最大: 100） |
| status | string | 任意 | ステータスフィルタ（カンマ区切り） |
| change_type | string | 任意 | 変更種別フィルタ |
| target_system | string | 任意 | 対象システムフィルタ |
| priority | string | 任意 | 優先度フィルタ |
| date_from | string | 任意 | 計画開始日の下限（ISO 8601） |
| date_to | string | 任意 | 計画開始日の上限（ISO 8601） |
| search | string | 任意 | タイトル・説明の全文検索 |
| sort | string | 任意 | ソート（例: created_at:desc） |

**レスポンス (200):**
```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "rfcNumber": "RFC-2026-045",
      "title": "AD設定変更",
      "changeType": "normal",
      "priority": "high",
      "status": "cab_review",
      "targetSystems": ["ActiveDirectory", "EntraID"],
      "affectedUsers": 150,
      "plannedStart": "2026-04-01T22:00:00Z",
      "plannedEnd": "2026-04-01T23:00:00Z",
      "technicalRisk": "high",
      "riskScore": 15,
      "requester": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "displayName": "山田太郎"
      },
      "createdAt": "2026-03-25T10:00:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 45,
    "totalPages": 3
  }
}
```

---

### 3.2 RFC詳細取得

| 項目 | 内容 |
|------|------|
| **メソッド** | GET |
| **エンドポイント** | /api/v1/rfcs/:id |
| **認証** | 必須 |

**レスポンス (200):**
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "rfcNumber": "RFC-2026-045",
    "title": "AD設定変更",
    "description": "Active Directoryのパスワードポリシーを変更...",
    "changeType": "normal",
    "priority": "high",
    "status": "cab_review",
    "targetSystems": ["ActiveDirectory", "EntraID"],
    "affectedUsers": 150,
    "plannedStart": "2026-04-01T22:00:00Z",
    "plannedEnd": "2026-04-01T23:00:00Z",
    "businessImpact": "認証基盤の設定変更のため...",
    "technicalRisk": "high",
    "riskAssessment": "AD/EntraIDの同期設定変更...",
    "riskScore": 15,
    "rollbackPlan": "設定変更前のバックアップから復元...",
    "rollbackTrigger": "認証エラー率5%超過時",
    "rollbackDuration": "30分",
    "requester": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "displayName": "山田太郎",
      "department": "IT部門"
    },
    "implementer": null,
    "impactAnalysis": {
      "affectedSystems": ["ActiveDirectory", "EntraID", "HENGEONE", "Microsoft365"],
      "riskLevel": "high",
      "dependencies": [
        { "from": "ActiveDirectory", "to": "EntraID", "type": "sync" },
        { "from": "EntraID", "to": "HENGEONE", "type": "sso" }
      ]
    },
    "conflicts": {
      "hasConflict": false,
      "conflicts": [],
      "warnings": [
        {
          "type": "DEPENDENCY_CHANGE",
          "message": "依存システムに変更が予定されています",
          "relatedRFCs": ["RFC-2026-046"]
        }
      ]
    },
    "approval": {
      "decision": null,
      "requiredApprovals": 2,
      "currentApprovals": 1,
      "votes": [
        {
          "voterId": "user-uuid",
          "voterName": "鈴木一郎",
          "vote": "approve",
          "comment": "問題なし",
          "votedAt": "2026-03-25T14:00:00Z"
        }
      ]
    },
    "submittedAt": "2026-03-25T10:00:00Z",
    "createdAt": "2026-03-25T09:30:00Z",
    "updatedAt": "2026-03-25T14:00:00Z"
  }
}
```

---

### 3.3 RFC作成

| 項目 | 内容 |
|------|------|
| **メソッド** | POST |
| **エンドポイント** | /api/v1/rfcs |
| **認証** | 必須 |
| **権限** | requester以上 |

**リクエスト:**
```json
{
  "title": "AD設定変更",
  "description": "Active Directoryのパスワードポリシーを変更...",
  "changeType": "normal",
  "priority": "high",
  "targetSystems": ["ActiveDirectory", "EntraID"],
  "affectedUsers": 150,
  "plannedStart": "2026-04-01T22:00:00Z",
  "plannedEnd": "2026-04-01T23:00:00Z",
  "businessImpact": "認証基盤の設定変更のため...",
  "technicalRisk": "high",
  "riskAssessment": "AD/EntraIDの同期設定変更...",
  "rollbackPlan": "設定変更前のバックアップから復元...",
  "rollbackTrigger": "認証エラー率5%超過時",
  "rollbackDuration": "30分",
  "isDraft": true
}
```

**レスポンス (201):**
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "rfcNumber": "RFC-2026-045",
    "status": "draft",
    "autoClassifiedType": "normal",
    "impactAnalysis": { ... },
    "conflicts": { ... },
    "createdAt": "2026-03-25T09:30:00Z"
  }
}
```

---

### 3.4 RFC更新

| 項目 | 内容 |
|------|------|
| **メソッド** | PUT |
| **エンドポイント** | /api/v1/rfcs/:id |
| **認証** | 必須 |
| **権限** | 起票者（draft時のみ）、管理者 |

---

### 3.5 RFC提出

| 項目 | 内容 |
|------|------|
| **メソッド** | POST |
| **エンドポイント** | /api/v1/rfcs/:id/submit |
| **認証** | 必須 |
| **権限** | 起票者 |

**レスポンス (200):**
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "rfcNumber": "RFC-2026-045",
    "status": "submitted",
    "submittedAt": "2026-03-25T10:00:00Z",
    "nextAction": "cab_review"
  }
}
```

**エラーレスポンス (422 - フリーズ期間):**
```json
{
  "error": {
    "code": "ERR_FREEZE",
    "message": "フリーズ期間中のため変更を提出できません",
    "details": [
      {
        "freezePeriod": "期末凍結期間",
        "startDate": "2026-03-25",
        "endDate": "2026-04-05"
      }
    ]
  }
}
```

---

### 3.6 RFCステータス更新

| 項目 | 内容 |
|------|------|
| **メソッド** | PATCH |
| **エンドポイント** | /api/v1/rfcs/:id/status |
| **認証** | 必須 |
| **権限** | ロールに応じた状態遷移権限 |

**リクエスト:**
```json
{
  "status": "in_progress",
  "actualStart": "2026-04-01T22:00:00Z"
}
```

---

### 3.7 RFC取消し

| 項目 | 内容 |
|------|------|
| **メソッド** | POST |
| **エンドポイント** | /api/v1/rfcs/:id/cancel |
| **認証** | 必須 |
| **権限** | 起票者（draft/submitted時）、管理者 |

**リクエスト:**
```json
{
  "reason": "変更不要となったため"
}
```

---

### 3.8 RFCコメント

| メソッド | エンドポイント | 説明 |
|---------|-------------|------|
| GET | /api/v1/rfcs/:id/comments | コメント一覧取得 |
| POST | /api/v1/rfcs/:id/comments | コメント追加 |

**POST リクエスト:**
```json
{
  "content": "影響範囲を確認しました。問題ありません。"
}
```

---

### 3.9 RFC添付ファイル

| メソッド | エンドポイント | 説明 |
|---------|-------------|------|
| GET | /api/v1/rfcs/:id/attachments | 添付ファイル一覧取得 |
| POST | /api/v1/rfcs/:id/attachments | 添付ファイルアップロード（multipart/form-data） |
| GET | /api/v1/rfcs/:id/attachments/:fileId/download | 添付ファイルダウンロード |
| DELETE | /api/v1/rfcs/:id/attachments/:fileId | 添付ファイル削除 |

---

## 4. CAB管理API

### 4.1 CABセッション管理

| メソッド | エンドポイント | 説明 | 権限 |
|---------|-------------|------|------|
| GET | /api/v1/cab/sessions | CABセッション一覧取得 | cab_member以上 |
| GET | /api/v1/cab/sessions/:id | CABセッション詳細取得 | cab_member以上 |
| POST | /api/v1/cab/sessions | CABセッション作成（臨時CAB） | cab_chair, admin |
| PUT | /api/v1/cab/sessions/:id | CABセッション更新 | cab_chair, admin |
| POST | /api/v1/cab/sessions/:id/start | CABセッション開始 | cab_chair |
| POST | /api/v1/cab/sessions/:id/end | CABセッション終了 | cab_chair |
| POST | /api/v1/cab/sessions/:id/cancel | CABセッションキャンセル | cab_chair |

### 4.2 CAB議題取得

| 項目 | 内容 |
|------|------|
| **メソッド** | GET |
| **エンドポイント** | /api/v1/cab/sessions/:id/agenda |
| **認証** | 必須 |
| **権限** | cab_member以上 |

**レスポンス (200):**
```json
{
  "data": {
    "sessionId": "session-uuid",
    "sessionNumber": "CAB-2026-012",
    "scheduledDate": "2026-03-28T14:00:00Z",
    "followUpItems": [
      {
        "rfcNumber": "RFC-2026-040",
        "title": "前回保留案件",
        "previousDecision": "deferred",
        "status": "submitted"
      }
    ],
    "newItems": [
      {
        "rfcNumber": "RFC-2026-045",
        "title": "AD設定変更",
        "changeType": "normal",
        "riskLevel": "high",
        "riskScore": 15,
        "targetSystems": ["ActiveDirectory", "EntraID"],
        "plannedStart": "2026-04-01T22:00:00Z",
        "requester": "山田太郎",
        "impactSummary": "全社員(150名)に影響",
        "conflictWarnings": 1
      }
    ],
    "upcomingChanges": [
      {
        "rfcNumber": "RFC-2026-043",
        "title": "FWルール変更",
        "plannedStart": "2026-03-29T20:00:00Z",
        "status": "approved"
      }
    ]
  }
}
```

### 4.3 RFC承認/却下

| 項目 | 内容 |
|------|------|
| **メソッド** | POST |
| **エンドポイント** | /api/v1/cab/decisions/:decisionId/vote |
| **認証** | 必須 |
| **権限** | cab_member, cab_chair, executive |

**リクエスト:**
```json
{
  "vote": "approve",
  "comment": "影響範囲を確認済み。問題なし。"
}
```

**レスポンス (200):**
```json
{
  "data": {
    "voteId": "vote-uuid",
    "decisionId": "decision-uuid",
    "rfcId": "rfc-uuid",
    "vote": "approve",
    "approvalStatus": {
      "currentApprovals": 2,
      "requiredApprovals": 2,
      "isApproved": true,
      "requiredApproversStatus": [
        { "role": "cab_chair", "approved": true },
        { "role": "cab_member", "approved": true }
      ]
    },
    "rfcNewStatus": "approved"
  }
}
```

### 4.4 CAB議事録

| メソッド | エンドポイント | 説明 |
|---------|-------------|------|
| GET | /api/v1/cab/sessions/:id/minutes | 議事録取得 |
| PUT | /api/v1/cab/sessions/:id/minutes | 議事録更新（追記・修正） |
| GET | /api/v1/cab/sessions/:id/minutes/pdf | 議事録PDF出力 |

---

## 5. 変更実施API

### 5.1 実施管理

| メソッド | エンドポイント | 説明 | 権限 |
|---------|-------------|------|------|
| POST | /api/v1/execution/:rfcId/start | 実施開始 | implementer |
| POST | /api/v1/execution/:rfcId/complete | 実施完了 | implementer |
| POST | /api/v1/execution/:rfcId/rollback | ロールバック開始 | implementer |
| POST | /api/v1/execution/:rfcId/rollback-complete | ロールバック完了 | implementer |
| PUT | /api/v1/execution/:rfcId/record | 実施記録更新 | implementer |

**実施開始リクエスト:**
```json
{
  "actualStart": "2026-04-01T22:00:00Z",
  "implementerId": "user-uuid"
}
```

**ロールバック開始リクエスト:**
```json
{
  "reason": "認証エラー率が10%に達したため",
  "rollbackStart": "2026-04-01T22:30:00Z"
}
```

### 5.2 チェックリストAPI

| メソッド | エンドポイント | 説明 |
|---------|-------------|------|
| GET | /api/v1/execution/:rfcId/checklists | チェックリスト取得 |
| PUT | /api/v1/execution/:rfcId/checklists/:phase | チェックリスト更新 |

**チェックリスト更新リクエスト:**
```json
{
  "items": [
    {
      "id": "chk-001",
      "checked": true,
      "comment": "バックアップ取得完了"
    }
  ]
}
```

---

## 6. カレンダーAPI

| メソッド | エンドポイント | 説明 |
|---------|-------------|------|
| GET | /api/v1/calendar/events | カレンダーイベント取得 |
| GET | /api/v1/calendar/freeze-periods | フリーズ期間取得 |
| GET | /api/v1/calendar/export/ical | iCal形式エクスポート |

**GET /api/v1/calendar/events クエリパラメータ:**

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| start | string | 必須 | 期間開始日（ISO 8601） |
| end | string | 必須 | 期間終了日（ISO 8601） |
| change_type | string | 任意 | 変更種別フィルタ |
| target_system | string | 任意 | 対象システムフィルタ |

**レスポンス (200):**
```json
{
  "data": [
    {
      "id": "rfc-uuid",
      "title": "RFC-2026-045: AD設定変更",
      "start": "2026-04-01T22:00:00Z",
      "end": "2026-04-01T23:00:00Z",
      "type": "change",
      "changeType": "normal",
      "status": "approved",
      "color": "#1890ff"
    },
    {
      "id": "cab-uuid",
      "title": "CAB会議 CAB-2026-013",
      "start": "2026-04-04T14:00:00Z",
      "end": "2026-04-04T15:00:00Z",
      "type": "cab_meeting",
      "color": "#722ed1"
    },
    {
      "id": "freeze-uuid",
      "title": "期末凍結期間",
      "start": "2026-03-25",
      "end": "2026-04-05",
      "type": "freeze_period",
      "color": "#d9d9d9",
      "allDay": true
    }
  ]
}
```

---

## 7. KPI・レポートAPI

### 7.1 KPIダッシュボード

| 項目 | 内容 |
|------|------|
| **メソッド** | GET |
| **エンドポイント** | /api/v1/reports/kpi |
| **認証** | 必須 |
| **権限** | cab_member以上 |

**クエリパラメータ:**

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| period | string | 任意 | month/quarter/year/custom（デフォルト: month） |
| date_from | string | 任意 | カスタム期間開始日 |
| date_to | string | 任意 | カスタム期間終了日 |

**レスポンス (200):**
```json
{
  "data": {
    "period": {
      "from": "2026-03-01",
      "to": "2026-03-31"
    },
    "changeSuccessRate": 96.5,
    "rollbackRate": 3.5,
    "totalChanges": 12,
    "changesByType": {
      "standard": 5,
      "normal": 4,
      "major": 2,
      "emergency": 1
    },
    "changesBySystem": {
      "ActiveDirectory": 8,
      "EntraID": 6,
      "Microsoft365": 4,
      "ExchangeOnline": 3,
      "HENGEONE": 2
    },
    "avgApprovalLeadTimeHours": 55.2,
    "emergencyChangeRatio": 8.3,
    "changeIncidentRate": 4.2,
    "freezeComplianceRate": 100,
    "pendingApprovals": 3,
    "overdueApprovals": 0
  }
}
```

### 7.2 トレンド分析

| 項目 | 内容 |
|------|------|
| **メソッド** | GET |
| **エンドポイント** | /api/v1/reports/trends |
| **認証** | 必須 |

**レスポンス (200):**
```json
{
  "data": {
    "monthlyChanges": [
      { "month": "2025-10", "count": 10, "successRate": 90.0 },
      { "month": "2025-11", "count": 12, "successRate": 91.7 },
      { "month": "2025-12", "count": 8, "successRate": 100.0 },
      { "month": "2026-01", "count": 11, "successRate": 90.9 },
      { "month": "2026-02", "count": 14, "successRate": 92.9 },
      { "month": "2026-03", "count": 12, "successRate": 96.5 }
    ],
    "systemHeatmap": { ... },
    "approvalLeadTimeTrend": [ ... ]
  }
}
```

### 7.3 レポートエクスポート

| メソッド | エンドポイント | 説明 |
|---------|-------------|------|
| GET | /api/v1/reports/kpi/export/pdf | KPIレポートPDF出力 |
| GET | /api/v1/reports/kpi/export/csv | KPIデータCSV出力 |
| GET | /api/v1/reports/rfcs/export/csv | RFC一覧CSV出力 |
| GET | /api/v1/reports/audit/export/csv | 監査ログCSV出力 |

---

## 8. PIR（事後レビュー）API

| メソッド | エンドポイント | 説明 |
|---------|-------------|------|
| GET | /api/v1/reviews | PIR一覧取得 |
| GET | /api/v1/reviews/:id | PIR詳細取得 |
| POST | /api/v1/reviews | PIR作成 |
| PUT | /api/v1/reviews/:id | PIR更新 |
| POST | /api/v1/reviews/:id/complete | PIR完了 |
| GET | /api/v1/reviews/improvements | 改善事項一覧 |
| PUT | /api/v1/reviews/improvements/:id | 改善事項更新 |

---

## 9. フリーズ期間管理API

| メソッド | エンドポイント | 説明 | 権限 |
|---------|-------------|------|------|
| GET | /api/v1/freeze-periods | フリーズ期間一覧取得 | 全ロール |
| POST | /api/v1/freeze-periods | フリーズ期間作成 | admin, cab_chair |
| PUT | /api/v1/freeze-periods/:id | フリーズ期間更新 | admin, cab_chair |
| DELETE | /api/v1/freeze-periods/:id | フリーズ期間削除 | admin |

---

## 10. 管理API

### 10.1 ユーザ管理

| メソッド | エンドポイント | 説明 | 権限 |
|---------|-------------|------|------|
| GET | /api/v1/admin/users | ユーザ一覧取得 | admin |
| GET | /api/v1/admin/users/:id | ユーザ詳細取得 | admin |
| POST | /api/v1/admin/users | ユーザ作成 | admin |
| PUT | /api/v1/admin/users/:id | ユーザ更新 | admin |
| PATCH | /api/v1/admin/users/:id/deactivate | ユーザ無効化 | admin |

### 10.2 システム設定

| メソッド | エンドポイント | 説明 | 権限 |
|---------|-------------|------|------|
| GET | /api/v1/admin/settings | 設定一覧取得 | admin |
| PUT | /api/v1/admin/settings/:key | 設定更新 | admin |

### 10.3 監査ログ

| メソッド | エンドポイント | 説明 | 権限 |
|---------|-------------|------|------|
| GET | /api/v1/admin/audit-logs | 監査ログ検索 | admin |

### 10.4 標準変更テンプレート

| メソッド | エンドポイント | 説明 | 権限 |
|---------|-------------|------|------|
| GET | /api/v1/admin/templates | テンプレート一覧 | admin, cab_chair |
| POST | /api/v1/admin/templates | テンプレート作成 | admin, cab_chair |
| PUT | /api/v1/admin/templates/:id | テンプレート更新 | admin, cab_chair |
| DELETE | /api/v1/admin/templates/:id | テンプレート削除 | admin |

---

## 11. エラーコード一覧

| コード | HTTP | 説明 |
|--------|------|------|
| ERR_VALIDATION | 400 | 入力バリデーションエラー |
| ERR_AUTH_INVALID_CREDENTIALS | 401 | ユーザ名またはパスワードが不正 |
| ERR_AUTH_TOKEN_EXPIRED | 401 | トークン期限切れ |
| ERR_AUTH_TOKEN_INVALID | 401 | 不正なトークン |
| ERR_AUTH_ACCOUNT_LOCKED | 401 | アカウントロック中 |
| ERR_FORBIDDEN | 403 | 権限不足 |
| ERR_NOT_FOUND | 404 | リソースが見つからない |
| ERR_RFC_NOT_FOUND | 404 | RFCが見つからない |
| ERR_CONFLICT | 409 | データ競合（楽観的ロック） |
| ERR_STATE_TRANSITION | 422 | 許可されない状態遷移 |
| ERR_FREEZE_PERIOD | 422 | フリーズ期間中の変更 |
| ERR_APPROVAL_INCOMPLETE | 422 | 承認条件未達成 |
| ERR_CHECKLIST_INCOMPLETE | 422 | チェックリスト未完了 |
| ERR_RATE_LIMIT | 429 | レート制限超過 |
| ERR_INTERNAL | 500 | 内部サーバーエラー |
| ERR_EXTERNAL_TEAMS | 502 | Teams Webhook送信失敗 |
| ERR_EXTERNAL_EMAIL | 502 | メール送信失敗 |
| ERR_EXTERNAL_GITHUB | 502 | GitHub Actions連携失敗 |

---

## 12. レート制限

| エンドポイント | 制限 | ウィンドウ |
|-------------|------|----------|
| POST /auth/login | 5回 | 1分 |
| POST /auth/refresh | 10回 | 1分 |
| GET /api/v1/* | 100回 | 1分 |
| POST /api/v1/* | 30回 | 1分 |
| PUT /api/v1/* | 30回 | 1分 |
| DELETE /api/v1/* | 10回 | 1分 |
| GET /api/v1/reports/* | 10回 | 1分 |

---

*文書管理：本文書はバージョン管理対象。変更履歴はGitリポジトリで管理する。*
