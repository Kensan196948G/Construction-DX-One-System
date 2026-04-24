# API設計書（API Design）

## 建設業 統合リスク＆コンプライアンス管理システム（Construction-GRC-System）

| 項目 | 内容 |
|------|------|
| **文書番号** | DES-GRC-004 |
| **バージョン** | 1.0.0 |
| **作成日** | 2026-03-26 |
| **最終更新日** | 2026-03-26 |
| **作成者** | みらい建設工業 IT部門 |
| **承認者** | 情報セキュリティ管理責任者（CISO） |
| **対象リポジトリ** | Kensan196948G/Construction-GRC-System |
| **準拠規格** | ISO27001:2022 / NIST CSF 2.0 / 建設業法 / 品確法 / 労安法 |
| **技術スタック** | Django+DRF / Vue.js 3+Vuetify 3 / PostgreSQL / Redis / Celery |

---

## 改訂履歴

| バージョン | 日付 | 変更内容 | 変更者 |
|-----------|------|---------|--------|
| 1.0.0 | 2026-03-26 | 初版作成 | IT部門 |

---

## 目次

1. [API設計原則](#1-api設計原則)
2. [認証・認可API](#2-認証認可api)
3. [リスク管理API](#3-リスク管理api)
4. [コンプライアンス管理API](#4-コンプライアンス管理api)
5. [統制管理API](#5-統制管理api)
6. [監査管理API](#6-監査管理api)
7. [レポート管理API](#7-レポート管理api)
8. [共通仕様](#8-共通仕様)

---

## 1. API設計原則

### 1.1 基本方針

| 項目 | 仕様 |
|------|------|
| ベースURL | `/api/v1/` |
| プロトコル | HTTPS（TLS 1.3） |
| データ形式 | JSON（UTF-8） |
| 認証方式 | Bearer Token（JWT） |
| バージョニング | URLパスバージョニング（/api/v1/） |
| ページネーション | limit-offset方式（デフォルト20件） |
| 日付形式 | ISO 8601（YYYY-MM-DD / YYYY-MM-DDTHH:MM:SSZ） |
| エラー形式 | RFC 7807 Problem Details |

### 1.2 認証ヘッダー

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json
```

### 1.3 ページネーションパラメータ

| パラメータ | 型 | デフォルト | 説明 |
|----------|-----|----------|------|
| limit | integer | 20 | 取得件数（最大100） |
| offset | integer | 0 | スキップ件数 |

**レスポンス形式:**

```json
{
  "count": 150,
  "next": "https://api.example.com/api/v1/risks/?limit=20&offset=20",
  "previous": null,
  "results": [...]
}
```

### 1.4 エラーレスポンス形式

```json
{
  "type": "validation_error",
  "title": "バリデーションエラー",
  "status": 400,
  "detail": "入力データに誤りがあります",
  "errors": [
    {
      "field": "title",
      "message": "この項目は必須です",
      "code": "required"
    }
  ]
}
```

### 1.5 HTTPステータスコード

| コード | 用途 |
|-------|------|
| 200 | 成功（取得・更新・削除） |
| 201 | 作成成功 |
| 202 | 非同期タスク受付 |
| 204 | 削除成功（レスポンスボディなし） |
| 400 | バリデーションエラー |
| 401 | 認証エラー |
| 403 | 権限不足 |
| 404 | リソース不存在 |
| 409 | 競合（重複等） |
| 429 | レート制限超過 |
| 500 | サーバーエラー |

---

## 2. 認証・認可API

### POST /api/v1/auth/login/

**説明:** ログイン（JWTトークン取得）

**認証:** 不要

**リクエスト:**

```json
{
  "email": "admin@example.com",
  "password": "SecurePassword123!"
}
```

**レスポンス（200）:**

```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "admin@example.com",
    "username": "admin",
    "first_name": "太郎",
    "last_name": "管理",
    "role": "admin",
    "department": "IT部門"
  }
}
```

**エラー（401）:**

```json
{
  "type": "authentication_error",
  "title": "認証エラー",
  "status": 401,
  "detail": "ユーザー名またはパスワードが正しくありません"
}
```

### POST /api/v1/auth/refresh/

**説明:** アクセストークンのリフレッシュ

**リクエスト:**

```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**レスポンス（200）:**

```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### POST /api/v1/auth/logout/

**説明:** ログアウト（リフレッシュトークン無効化）

**認証:** 必要

### GET /api/v1/auth/me/

**説明:** ログインユーザー情報取得

**認証:** 必要

**レスポンス（200）:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "admin@example.com",
  "username": "admin",
  "first_name": "太郎",
  "last_name": "管理",
  "role": "admin",
  "department": "IT部門",
  "permissions": ["risk.create", "risk.read", "risk.update", "risk.delete", "..."]
}
```

---

## 3. リスク管理API

### エンドポイント一覧

| メソッド | パス | 説明 | 権限 |
|---------|------|------|------|
| GET | /api/v1/risks/ | リスク一覧 | 全認証ユーザー |
| POST | /api/v1/risks/ | リスク登録 | admin, risk_owner |
| GET | /api/v1/risks/{id}/ | リスク詳細 | 全認証ユーザー |
| PUT | /api/v1/risks/{id}/ | リスク更新 | admin, risk_owner(自担当) |
| DELETE | /api/v1/risks/{id}/ | リスク削除（論理） | admin |
| POST | /api/v1/risks/{id}/evaluate/ | リスク評価 | admin, risk_owner(自担当) |
| GET | /api/v1/risks/{id}/evaluations/ | 評価履歴 | 全認証ユーザー |
| POST | /api/v1/risks/{id}/treatment-plans/ | 対応計画作成 | admin, risk_owner |
| GET | /api/v1/risks/heatmap/ | ヒートマップデータ | 全認証ユーザー |
| GET | /api/v1/risks/summary/ | リスクサマリー | 全認証ユーザー |
| POST | /api/v1/risks/report/ | 簡易リスク報告 | 全認証ユーザー |

### GET /api/v1/risks/

**クエリパラメータ:**

| パラメータ | 型 | 説明 |
|----------|-----|------|
| category | string | カテゴリフィルタ |
| status | string | ステータスフィルタ |
| inherent_level | string | リスクレベルフィルタ |
| owner | UUID | オーナーフィルタ |
| search | string | フリーテキスト検索（title, description） |
| ordering | string | ソート（created_at, inherent_score, -updated_at） |
| limit | integer | 取得件数 |
| offset | integer | オフセット |

**レスポンス（200）:**

```json
{
  "count": 45,
  "next": "/api/v1/risks/?limit=20&offset=20",
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "risk_id": "RSK-2026-0001",
      "title": "社内ネットワークへの不正アクセス",
      "category": "information_security",
      "category_display": "情報セキュリティ",
      "owner_name": "田中太郎",
      "inherent_score": 12,
      "inherent_level": "high",
      "inherent_level_display": "高",
      "residual_score": 6,
      "residual_level": "medium",
      "status": "monitoring",
      "status_display": "モニタリング中",
      "created_at": "2026-03-15T09:00:00Z"
    }
  ]
}
```

### POST /api/v1/risks/

**リクエスト:**

```json
{
  "title": "建設現場の転落事故リスク",
  "description": "高所作業における転落事故のリスク。安全帯未着用、足場不備等が原因となる。",
  "category": "occupational_safety",
  "sub_category": "高所作業",
  "owner": "550e8400-e29b-41d4-a716-446655440002",
  "department": "安全管理部",
  "project": "東京駅前再開発プロジェクト",
  "inherent_likelihood": 3,
  "inherent_impact": 5,
  "framework_controls": [
    "550e8400-e29b-41d4-a716-446655440010"
  ]
}
```

**レスポンス（201）:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440099",
  "risk_id": "RSK-2026-0046",
  "title": "建設現場の転落事故リスク",
  "inherent_score": 15,
  "inherent_level": "high",
  "status": "identified",
  "created_at": "2026-03-26T10:30:00Z"
}
```

### POST /api/v1/risks/{id}/evaluate/

**リクエスト:**

```json
{
  "evaluation_date": "2026-03-26",
  "likelihood": 3,
  "impact_financial": 4,
  "impact_operational": 3,
  "impact_legal": 5,
  "impact_safety": 5,
  "impact_reputation": 4,
  "control_effectiveness": "partially_effective",
  "comments": "法令リスクと安全リスクが高い。統制は一部有効。"
}
```

**レスポンス（201）:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440100",
  "risk_id": "RSK-2026-0046",
  "max_impact": 5,
  "inherent_score": 15,
  "inherent_level": "high",
  "residual_score": 10,
  "residual_level": "medium",
  "evaluation_date": "2026-03-26"
}
```

### GET /api/v1/risks/heatmap/

**クエリパラメータ:** category, department, project, risk_type(inherent/residual)

**レスポンス（200）:**

```json
{
  "risk_type": "inherent",
  "matrix": [
    {"likelihood": 1, "impact": 1, "count": 2, "risks": ["RSK-2026-0010", "RSK-2026-0015"]},
    {"likelihood": 1, "impact": 2, "count": 0, "risks": []},
    {"likelihood": 3, "impact": 4, "count": 5, "risks": ["RSK-2026-0001", "..."]},
    {"likelihood": 5, "impact": 5, "count": 1, "risks": ["RSK-2026-0003"]}
  ],
  "total_risks": 45,
  "filters_applied": {"category": null, "department": null}
}
```

---

## 4. コンプライアンス管理API

### エンドポイント一覧

| メソッド | パス | 説明 | 権限 |
|---------|------|------|------|
| GET | /api/v1/compliance/ | 要件一覧 | 全認証ユーザー |
| POST | /api/v1/compliance/ | 要件登録 | admin, compliance_officer |
| GET | /api/v1/compliance/{id}/ | 要件詳細 | 全認証ユーザー |
| PUT | /api/v1/compliance/{id}/ | 要件更新 | admin, compliance_officer |
| POST | /api/v1/compliance/{id}/assess/ | 準拠評価 | admin, compliance_officer |
| GET | /api/v1/compliance/{id}/assessments/ | 評価履歴 | 全認証ユーザー |
| GET | /api/v1/compliance/rate/ | 準拠率 | 全認証ユーザー |
| POST | /api/v1/compliance/import/ | CSV一括インポート | admin |
| GET | /api/v1/compliance/gap-analysis/ | ギャップ分析一覧 | admin, compliance_officer, auditor |
| POST | /api/v1/compliance/gap-analysis/ | ギャップ分析実施 | admin, compliance_officer |
| POST | /api/v1/compliance/gap-analysis/{id}/plans/ | 改善計画作成 | admin, compliance_officer |
| GET | /api/v1/compliance/legal-updates/ | 法令改正一覧 | admin, compliance_officer |
| POST | /api/v1/compliance/legal-updates/ | 法令改正登録 | admin, compliance_officer |

### GET /api/v1/compliance/rate/

**クエリパラメータ:** framework (フレームワークコード)

**レスポンス（200）:**

```json
{
  "rates": [
    {
      "framework": "ISO27001",
      "framework_name": "ISO/IEC 27001:2022",
      "total": 93,
      "compliant": 75,
      "partially_compliant": 8,
      "non_compliant": 5,
      "not_applicable": 5,
      "not_assessed": 0,
      "compliance_rate": 85.23
    },
    {
      "framework": "NIST_CSF",
      "framework_name": "NIST CSF 2.0",
      "total": 106,
      "compliant": 80,
      "partially_compliant": 10,
      "non_compliant": 8,
      "not_applicable": 8,
      "not_assessed": 0,
      "compliance_rate": 81.63
    }
  ]
}
```

---

## 5. 統制管理API

### エンドポイント一覧

| メソッド | パス | 説明 | 権限 |
|---------|------|------|------|
| GET | /api/v1/controls/ | 統制一覧 | 全認証ユーザー |
| POST | /api/v1/controls/ | 統制登録 | admin, compliance_officer |
| GET | /api/v1/controls/{id}/ | 統制詳細 | 全認証ユーザー |
| PUT | /api/v1/controls/{id}/ | 統制更新 | admin, compliance_officer |
| POST | /api/v1/controls/{id}/test/ | テスト結果登録 | admin, auditor |
| GET | /api/v1/controls/{id}/tests/ | テスト履歴 | 全認証ユーザー |
| POST | /api/v1/controls/{id}/evaluate/ | 有効性評価 | admin, compliance_officer |
| POST | /api/v1/controls/import/ | 一括インポート | admin |
| GET | /api/v1/evidence/ | エビデンス一覧 | 全認証ユーザー |
| POST | /api/v1/evidence/ | エビデンスアップロード | 全認証ユーザー |
| DELETE | /api/v1/evidence/{id}/ | エビデンス削除（論理） | admin, 作成者 |
| GET | /api/v1/corrective-actions/ | 是正措置一覧 | 全認証ユーザー |
| POST | /api/v1/corrective-actions/ | 是正措置登録 | admin, compliance_officer |
| POST | /api/v1/corrective-actions/{id}/complete/ | 完了申請 | 担当者 |
| POST | /api/v1/corrective-actions/{id}/verify/ | 完了確認 | admin, compliance_officer |

### POST /api/v1/controls/{id}/test/

**リクエスト:**

```json
{
  "test_date": "2026-03-26",
  "result": "fail",
  "comments": "退職者3名の特権アカウントが未削除",
  "findings": "アカウント削除プロセスの不備を確認"
}
```

**レスポンス（201）:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440200",
  "control_id": "CTL-ISO-0001",
  "test_date": "2026-03-26",
  "result": "fail",
  "result_display": "不合格",
  "corrective_action_created": {
    "id": "550e8400-e29b-41d4-a716-446655440201",
    "title": "統制テスト不合格に対する是正措置",
    "status": "planned"
  }
}
```

### POST /api/v1/evidence/

**リクエスト（multipart/form-data）:**

| フィールド | 型 | 必須 | 説明 |
|----------|-----|:----:|------|
| file | File | YES | アップロードファイル |
| description | string | NO | 説明 |
| tags | string(JSON) | NO | タグ配列 |
| content_type | string | YES | 紐付け先タイプ（risk/control/finding） |
| object_id | UUID | YES | 紐付け先ID |

**レスポンス（201）:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440300",
  "original_filename": "特権アカウント棚卸結果.xlsx",
  "file_size": 5242880,
  "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "sha256_hash": "a3f2b8c9d4e5f6...",
  "description": "2026年Q1 特権アカウント棚卸結果",
  "uploaded_by": "田中太郎",
  "created_at": "2026-03-26T11:00:00Z"
}
```

---

## 6. 監査管理API

### エンドポイント一覧

| メソッド | パス | 説明 | 権限 |
|---------|------|------|------|
| GET | /api/v1/audits/ | 監査一覧 | 全認証ユーザー |
| POST | /api/v1/audits/ | 監査計画作成 | admin, auditor |
| GET | /api/v1/audits/{id}/ | 監査詳細 | 全認証ユーザー |
| PUT | /api/v1/audits/{id}/ | 監査更新 | admin, auditor |
| POST | /api/v1/audits/{id}/approve/ | 監査計画承認 | admin, executive |
| POST | /api/v1/audits/{id}/reject/ | 監査計画却下 | admin, executive |
| POST | /api/v1/audits/{id}/start/ | 監査開始 | auditor（主任） |
| POST | /api/v1/audits/{id}/suspend/ | 監査中断 | auditor（主任） |
| POST | /api/v1/audits/{id}/resume/ | 監査再開 | auditor（主任） |
| POST | /api/v1/audits/{id}/complete/ | 監査完了 | auditor（主任） |
| GET | /api/v1/audits/{id}/checklist/ | チェックリスト取得 | auditor |
| PUT | /api/v1/audits/{id}/checklist/{item_id}/ | チェック結果入力 | auditor |
| GET | /api/v1/audits/{id}/findings/ | 所見一覧 | 全認証ユーザー |
| POST | /api/v1/audits/{id}/findings/ | 所見記録 | auditor |
| POST | /api/v1/findings/{id}/car/ | 是正勧告発行 | auditor |
| POST | /api/v1/findings/{id}/follow-up/ | フォローアップ結果登録 | auditor |

### POST /api/v1/audits/

**リクエスト:**

```json
{
  "title": "2026年度 Q2内部監査",
  "audit_type": "internal",
  "scope": "ISO27001 A.8 技術的管理策",
  "target_department": "情報システム部門",
  "framework": "550e8400-e29b-41d4-a716-446655440500",
  "team_members": [
    "550e8400-e29b-41d4-a716-446655440501",
    "550e8400-e29b-41d4-a716-446655440502"
  ],
  "planned_start_date": "2026-04-15",
  "planned_end_date": "2026-04-30",
  "methodology": ["document_review", "interview", "inspection"]
}
```

**レスポンス（201）:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440600",
  "audit_id": "AUD-2026-0001",
  "title": "2026年度 Q2内部監査",
  "status": "draft",
  "checklist_items_count": 15,
  "created_at": "2026-03-26T14:00:00Z"
}
```

### POST /api/v1/findings/{id}/car/

**リクエスト:**

```json
{
  "description": "特権アカウント管理手順の策定と未削除アカウントの即時削除を求める",
  "due_date": "2026-05-15",
  "responsible_person": "550e8400-e29b-41d4-a716-446655440700"
}
```

**レスポンス（201）:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440800",
  "finding_id": "FND-2026-0001",
  "description": "特権アカウント管理手順の策定と未削除アカウントの即時削除を求める",
  "due_date": "2026-05-15",
  "responsible_person_name": "佐藤次郎",
  "status": "issued",
  "pdf_url": "/api/v1/findings/FND-2026-0001/car/pdf/",
  "corrective_action_id": "550e8400-e29b-41d4-a716-446655440801",
  "follow_up_date": "2026-05-20"
}
```

---

## 7. レポート管理API

### エンドポイント一覧

| メソッド | パス | 説明 | 権限 |
|---------|------|------|------|
| GET | /api/v1/dashboard/ | ダッシュボードデータ | 全認証ユーザー |
| GET | /api/v1/dashboard/risk-summary/ | リスクサマリー | 全認証ユーザー |
| GET | /api/v1/dashboard/compliance-rate/ | 準拠率 | 全認証ユーザー |
| GET | /api/v1/dashboard/control-effectiveness/ | 統制有効性 | 全認証ユーザー |
| GET | /api/v1/dashboard/open-findings/ | 未対応所見 | 全認証ユーザー |
| GET | /api/v1/dashboard/overdue-tasks/ | 期限超過タスク | 全認証ユーザー |
| GET | /api/v1/reports/templates/ | テンプレート一覧 | admin, compliance_officer |
| POST | /api/v1/reports/generate/ | レポート生成 | admin, compliance_officer |
| GET | /api/v1/reports/{id}/ | レポート詳細 | 全認証ユーザー |
| GET | /api/v1/reports/{id}/download/ | レポートダウンロード | 全認証ユーザー |
| POST | /api/v1/export/ | データエクスポート | 全認証ユーザー |
| GET | /api/v1/export/{task_id}/status/ | エクスポートステータス | 全認証ユーザー |
| GET | /api/v1/export/{task_id}/download/ | エクスポートダウンロード | 全認証ユーザー |
| GET | /api/v1/alerts/ | アラートルール一覧 | admin |
| POST | /api/v1/alerts/ | アラートルール作成 | admin |
| GET | /api/v1/alerts/history/ | アラート発報履歴 | admin |
| GET | /api/v1/notifications/ | 通知一覧 | 全認証ユーザー |
| PUT | /api/v1/notifications/{id}/read/ | 通知既読 | 全認証ユーザー |

### GET /api/v1/dashboard/

**クエリパラメータ:** period (7d/30d/90d/1y)

**レスポンス（200）:**

```json
{
  "risk_summary": {
    "total": 45,
    "by_level": {
      "critical": 2,
      "high": 8,
      "medium": 20,
      "low": 10,
      "very_low": 5
    },
    "trend": [
      {"date": "2026-03-01", "total": 42, "high_and_above": 9},
      {"date": "2026-03-15", "total": 44, "high_and_above": 10},
      {"date": "2026-03-26", "total": 45, "high_and_above": 10}
    ]
  },
  "compliance_rate": {
    "overall": 83.5,
    "by_framework": [
      {"framework": "ISO27001", "rate": 85.23},
      {"framework": "NIST_CSF", "rate": 81.63}
    ]
  },
  "control_effectiveness": {
    "effective": 120,
    "partially_effective": 30,
    "ineffective": 10,
    "not_assessed": 5
  },
  "open_findings": {
    "total": 12,
    "major_nc": 2,
    "minor_nc": 5,
    "observations": 5
  },
  "overdue_tasks": {
    "total": 3,
    "items": [
      {
        "type": "treatment_plan",
        "title": "ファイアウォール設定見直し",
        "due_date": "2026-03-20",
        "days_overdue": 6,
        "assignee": "田中太郎"
      }
    ]
  }
}
```

### POST /api/v1/reports/generate/

**リクエスト:**

```json
{
  "template_id": "550e8400-e29b-41d4-a716-446655440900",
  "title": "2026年3月度 GRC月次レポート",
  "period_start": "2026-03-01",
  "period_end": "2026-03-31",
  "format": "pdf"
}
```

**レスポンス（202 Accepted）:**

```json
{
  "report_id": "550e8400-e29b-41d4-a716-446655440901",
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "generating",
  "message": "レポート生成を開始しました。完了後に通知されます。"
}
```

### POST /api/v1/export/

**リクエスト:**

```json
{
  "data_source": "risks",
  "format": "csv",
  "filters": {
    "category": "information_security",
    "status": ["identified", "assessing", "treating"]
  },
  "fields": ["risk_id", "title", "category", "inherent_level", "status", "owner_name"]
}
```

**レスポンス（202 Accepted）:**

```json
{
  "task_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "status": "processing",
  "message": "エクスポートを開始しました。"
}
```

---

## 8. 共通仕様

### 8.1 ヘルスチェック

#### GET /api/v1/health/

**認証:** 不要

**レスポンス（200）:**

```json
{
  "status": "healthy",
  "components": {
    "django": {"status": "healthy", "version": "5.1"},
    "postgresql": {"status": "healthy", "version": "16.2"},
    "redis": {"status": "healthy", "version": "7.2"},
    "celery": {"status": "healthy", "workers": 3}
  },
  "timestamp": "2026-03-26T15:00:00Z"
}
```

### 8.2 レート制限

| エンドポイント | 制限 |
|-------------|------|
| /api/v1/auth/login/ | 5回/分（IPアドレスごと） |
| /api/v1/auth/refresh/ | 30回/分 |
| 一般API（GET） | 100回/分（ユーザーごと） |
| 一般API（POST/PUT/DELETE） | 30回/分（ユーザーごと） |
| エクスポートAPI | 5回/時（ユーザーごと） |
| レポート生成API | 10回/時（ユーザーごと） |

### 8.3 フレームワークAPI

| メソッド | パス | 説明 |
|---------|------|------|
| GET | /api/v1/frameworks/ | フレームワーク一覧 |
| GET | /api/v1/frameworks/{id}/ | フレームワーク詳細 |
| GET | /api/v1/frameworks/{id}/controls/ | 管理策ツリー |
| GET | /api/v1/frameworks/{id}/mappings/ | マッピング一覧 |

### 8.4 監査ログAPI

| メソッド | パス | 説明 | 権限 |
|---------|------|------|------|
| GET | /api/v1/audit-logs/ | 監査ログ検索 | admin |
| GET | /api/v1/audit-logs/export/ | ログエクスポート | admin |

**クエリパラメータ:**

| パラメータ | 型 | 説明 |
|----------|-----|------|
| user | UUID | ユーザーフィルタ |
| action | string | 操作種別フィルタ |
| resource_type | string | リソースタイプフィルタ |
| from_date | date | 開始日 |
| to_date | date | 終了日 |
