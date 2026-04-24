# 外部連携仕様書
## IT変更管理・リリース自動化プラットフォーム（IT-Change-CAB-Platform）

| 項目 | 内容 |
|------|------|
| **文書番号** | API-EXT-001 |
| **バージョン** | 1.0.0 |
| **作成日** | 2026-03-26 |
| **作成者** | みらい建設工業 IT部門 |
| **承認者** | IT部門長 |
| **対象リポジトリ** | Kensan196948G/IT-Change-CAB-Platform |

---

## 1. 外部連携概要

### 1.1 連携先一覧

| 連携先 | 連携方式 | 通信方向 | 用途 | 優先度 |
|--------|---------|---------|------|--------|
| Microsoft Teams | Incoming Webhook | 送信のみ | 通知・承認依頼 | 必須（P1） |
| メールサーバ(SMTP) | SMTP | 送信のみ | 通知メール送信 | 必須（P1） |
| GitHub Actions | REST API | 双方向 | CI/CDパイプライン連携 | 推奨（P2） |
| ITSM システム | REST API | 双方向 | インシデント・問題管理連携 | 推奨（P2） |
| CMDB | REST API | 受信のみ | 構成情報取得 | 推奨（P2） |

### 1.2 連携アーキテクチャ

```
┌──────────────────────────────────────────────────────────┐
│              IT変更管理プラットフォーム                       │
│                                                          │
│  ┌──────────────────────────────────────────────────┐    │
│  │              NotificationService                  │    │
│  │                                                  │    │
│  │  ┌────────────────┐  ┌────────────────────────┐ │    │
│  │  │TemplateEngine  │  │ChannelRouter           │ │    │
│  │  │通知テンプレート   │  │チャネル振り分け         │ │    │
│  │  └────────────────┘  └──────┬──────┬──────┬───┘ │    │
│  └──────────────────────────────┼──────┼──────┼──────┘    │
│                                │      │      │           │
│  ┌─────────────────────────────┼──────┼──────┼─────────┐ │
│  │         IntegrationAdapters │      │      │          │ │
│  │                             │      │      │          │ │
│  │  ┌──────────────┐  ┌──────▼┐ ┌──▼────┐ ┌▼───────┐ │ │
│  │  │ ITSMConnector│  │Teams  │ │Email  │ │GitHub  │ │ │
│  │  │              │  │Webhook│ │Sender │ │Actions │ │ │
│  │  └──────┬───────┘  └──┬────┘ └──┬────┘ └──┬─────┘ │ │
│  └─────────┼─────────────┼────────┼─────────┼────────┘ │
└────────────┼─────────────┼────────┼─────────┼──────────┘
             │             │        │         │
             ▼             ▼        ▼         ▼
        ┌─────────┐  ┌─────────┐ ┌──────┐ ┌───────┐
        │ ITSM    │  │ Teams   │ │ SMTP │ │GitHub │
        │ System  │  │         │ │Server│ │ API   │
        └─────────┘  └─────────┘ └──────┘ └───────┘
```

---

## 2. Microsoft Teams Webhook連携

### 2.1 連携概要

| 項目 | 内容 |
|------|------|
| 連携方式 | Incoming Webhook（Power Automate Workflows対応） |
| プロトコル | HTTPS POST |
| データ形式 | Adaptive Card JSON |
| 認証 | Webhook URL（シークレット含む） |
| リトライ | 3回（1分, 5分, 15分間隔） |
| タイムアウト | 30秒 |
| フォールバック | メール通知に切り替え |

### 2.2 通知テンプレート

#### 2.2.1 CAB承認依頼通知

```json
{
  "type": "message",
  "attachments": [
    {
      "contentType": "application/vnd.microsoft.card.adaptive",
      "contentUrl": null,
      "content": {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
          {
            "type": "TextBlock",
            "text": "変更承認依頼",
            "size": "Large",
            "weight": "Bolder",
            "color": "Accent"
          },
          {
            "type": "FactSet",
            "facts": [
              { "title": "RFC番号", "value": "${rfcNumber}" },
              { "title": "タイトル", "value": "${title}" },
              { "title": "変更種別", "value": "${changeType}" },
              { "title": "対象システム", "value": "${targetSystems}" },
              { "title": "リスクレベル", "value": "${riskLevel}" },
              { "title": "影響ユーザ", "value": "${affectedUsers}名" },
              { "title": "実施予定", "value": "${plannedStart}" },
              { "title": "申請者", "value": "${requesterName}" }
            ]
          },
          {
            "type": "TextBlock",
            "text": "承認期限: ${approvalDeadline}",
            "color": "Attention",
            "weight": "Bolder"
          }
        ],
        "actions": [
          {
            "type": "Action.OpenUrl",
            "title": "承認する",
            "url": "${approveUrl}"
          },
          {
            "type": "Action.OpenUrl",
            "title": "却下する",
            "url": "${rejectUrl}"
          },
          {
            "type": "Action.OpenUrl",
            "title": "詳細確認",
            "url": "${detailUrl}"
          }
        ]
      }
    }
  ]
}
```

#### 2.2.2 変更実施開始通知

```json
{
  "type": "message",
  "attachments": [
    {
      "contentType": "application/vnd.microsoft.card.adaptive",
      "content": {
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
          {
            "type": "TextBlock",
            "text": "変更実施開始",
            "size": "Large",
            "weight": "Bolder",
            "color": "Warning"
          },
          {
            "type": "FactSet",
            "facts": [
              { "title": "RFC番号", "value": "${rfcNumber}" },
              { "title": "タイトル", "value": "${title}" },
              { "title": "実施者", "value": "${implementerName}" },
              { "title": "開始時刻", "value": "${actualStart}" },
              { "title": "完了予定", "value": "${plannedEnd}" }
            ]
          }
        ]
      }
    }
  ]
}
```

#### 2.2.3 ロールバック緊急通知

```json
{
  "type": "message",
  "attachments": [
    {
      "contentType": "application/vnd.microsoft.card.adaptive",
      "content": {
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
          {
            "type": "TextBlock",
            "text": "ロールバック開始（緊急）",
            "size": "Large",
            "weight": "Bolder",
            "color": "Attention"
          },
          {
            "type": "FactSet",
            "facts": [
              { "title": "RFC番号", "value": "${rfcNumber}" },
              { "title": "タイトル", "value": "${title}" },
              { "title": "ロールバック理由", "value": "${rollbackReason}" },
              { "title": "開始時刻", "value": "${rollbackStart}" },
              { "title": "実施者", "value": "${implementerName}" }
            ]
          },
          {
            "type": "TextBlock",
            "text": "ロールバック手順に従い作業中です。完了次第再度通知します。",
            "wrap": true
          }
        ]
      }
    }
  ]
}
```

#### 2.2.4 フリーズ期間警告通知

```json
{
  "type": "message",
  "attachments": [
    {
      "contentType": "application/vnd.microsoft.card.adaptive",
      "content": {
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
          {
            "type": "TextBlock",
            "text": "フリーズ期間 変更ブロック",
            "size": "Large",
            "weight": "Bolder",
            "color": "Attention"
          },
          {
            "type": "FactSet",
            "facts": [
              { "title": "RFC番号", "value": "${rfcNumber}" },
              { "title": "フリーズ期間", "value": "${freezeName}" },
              { "title": "期間", "value": "${freezeStart} 〜 ${freezeEnd}" },
              { "title": "ブロック理由", "value": "${reason}" }
            ]
          }
        ]
      }
    }
  ]
}
```

### 2.3 Teams連携設定

| 設定項目 | 説明 | 設定場所 |
|---------|------|---------|
| TEAMS_WEBHOOK_URL | Incoming Webhook URL | 環境変数 / システム設定 |
| TEAMS_RETRY_COUNT | リトライ回数 | システム設定（デフォルト: 3） |
| TEAMS_RETRY_INTERVAL | リトライ間隔（ms） | システム設定（デフォルト: [60000, 300000, 900000]） |
| TEAMS_TIMEOUT | タイムアウト（ms） | システム設定（デフォルト: 30000） |

### 2.4 実装仕様

```typescript
// integrations/teams-webhook.ts
interface TeamsWebhookConfig {
  webhookUrl: string;
  retryCount: number;
  retryIntervals: number[];
  timeout: number;
}

class TeamsWebhookService {
  async send(card: AdaptiveCard): Promise<void>;
  async sendWithRetry(card: AdaptiveCard, attempt: number): Promise<void>;
}
```

---

## 3. メール通知連携

### 3.1 連携概要

| 項目 | 内容 |
|------|------|
| プロトコル | SMTP (TLS) |
| ライブラリ | Nodemailer |
| 認証 | SMTP認証（ユーザ名/パスワード） |
| テンプレート | Handlebars HTMLテンプレート |
| 送信元 | noreply@mirai-kensetsu.co.jp |
| リトライ | 3回（1分, 5分, 15分間隔） |

### 3.2 メールテンプレート一覧

| テンプレートID | 件名 | 用途 |
|-------------|------|------|
| MAIL_CAB_REVIEW | 【変更承認依頼】${rfcNumber}: ${title} | CAB承認依頼 |
| MAIL_RFC_APPROVED | 【変更承認】${rfcNumber}: ${title} が承認されました | RFC承認通知 |
| MAIL_RFC_REJECTED | 【変更却下】${rfcNumber}: ${title} が却下されました | RFC却下通知 |
| MAIL_RFC_RETURNED | 【変更差戻し】${rfcNumber}: ${title} が差し戻されました | RFC差戻し通知 |
| MAIL_EXECUTION_STARTED | 【変更実施開始】${rfcNumber}: ${title} | 実施開始通知 |
| MAIL_EXECUTION_COMPLETED | 【変更完了】${rfcNumber}: ${title} | 実施完了通知 |
| MAIL_ROLLBACK_STARTED | 【緊急】ロールバック開始: ${rfcNumber} | ロールバック通知 |
| MAIL_CAB_MEETING | 【CAB会議】${sessionDate} 定期CAB会議のご案内 | CAB会議招集 |
| MAIL_CAB_REMINDER | 【リマインダー】明日のCAB会議 | CABリマインダー |
| MAIL_APPROVAL_OVERDUE | 【承認期限超過】${rfcNumber}: 承認期限を超過しています | エスカレーション |
| MAIL_FREEZE_WARNING | 【フリーズ期間】${rfcNumber}: 変更禁止期間中の申請 | フリーズ警告 |
| MAIL_PIR_REQUIRED | 【PIR依頼】${rfcNumber}: 事後レビューの入力をお願いします | PIR依頼 |

### 3.3 メール設定

| 設定項目 | 説明 | 環境変数 |
|---------|------|---------|
| SMTPホスト | メールサーバホスト名 | SMTP_HOST |
| SMTPポート | SMTPポート（587/465） | SMTP_PORT |
| SMTP認証ユーザ | 送信用アカウント | SMTP_USER |
| SMTP認証パスワード | 送信用パスワード | SMTP_PASS |
| TLS有効 | TLS暗号化 | SMTP_TLS=true |
| 送信元アドレス | From: アドレス | SMTP_FROM |
| 送信元名 | From: 表示名 | SMTP_FROM_NAME |

### 3.4 メールHTML例（CAB承認依頼）

```html
<!DOCTYPE html>
<html>
<head>
  <style>
    body { font-family: 'Noto Sans JP', sans-serif; }
    .header { background: #1890ff; color: white; padding: 20px; }
    .content { padding: 20px; }
    .fact-table { width: 100%; border-collapse: collapse; }
    .fact-table td { padding: 8px; border-bottom: 1px solid #eee; }
    .fact-label { font-weight: bold; width: 150px; }
    .btn { display: inline-block; padding: 10px 20px; margin: 5px;
           text-decoration: none; border-radius: 4px; color: white; }
    .btn-approve { background: #52c41a; }
    .btn-reject { background: #ff4d4f; }
    .btn-detail { background: #1890ff; }
  </style>
</head>
<body>
  <div class="header">
    <h2>変更承認依頼</h2>
  </div>
  <div class="content">
    <table class="fact-table">
      <tr><td class="fact-label">RFC番号</td><td>{{rfcNumber}}</td></tr>
      <tr><td class="fact-label">タイトル</td><td>{{title}}</td></tr>
      <tr><td class="fact-label">変更種別</td><td>{{changeType}}</td></tr>
      <tr><td class="fact-label">対象システム</td><td>{{targetSystems}}</td></tr>
      <tr><td class="fact-label">リスクレベル</td><td>{{riskLevel}}</td></tr>
      <tr><td class="fact-label">影響ユーザ</td><td>{{affectedUsers}}名</td></tr>
      <tr><td class="fact-label">実施予定</td><td>{{plannedStart}}</td></tr>
      <tr><td class="fact-label">申請者</td><td>{{requesterName}}</td></tr>
      <tr><td class="fact-label">承認期限</td><td>{{approvalDeadline}}</td></tr>
    </table>
    <br>
    <a href="{{approveUrl}}" class="btn btn-approve">承認する</a>
    <a href="{{rejectUrl}}" class="btn btn-reject">却下する</a>
    <a href="{{detailUrl}}" class="btn btn-detail">詳細確認</a>
  </div>
</body>
</html>
```

---

## 4. GitHub Actions連携

### 4.1 連携概要

| 項目 | 内容 |
|------|------|
| 連携方式 | REST API (GitHub API v3) |
| 認証 | Personal Access Token (PAT) / GitHub App |
| 通信方向 | 双方向（Workflow Dispatch + Webhook受信） |
| 用途 | デプロイ自動化、ロールバック自動化 |
| 優先度 | 推奨（P2） |

### 4.2 連携フロー

```
プラットフォーム                              GitHub Actions
     │                                           │
     │ POST /repos/{owner}/{repo}/actions/       │
     │       workflows/{workflow_id}/dispatches   │
     │ (RFC承認後、実施開始時)                       │
     │──────────────────────────────────────────>│
     │                                           │
     │                                    workflow実行
     │                                    (deploy/rollback)
     │                                           │
     │ POST /api/v1/webhooks/github              │
     │ (実行結果Webhook)                           │
     │◄──────────────────────────────────────────│
     │                                           │
     │ RFC状態更新                                 │
     │ (completed / rolled_back)                  │
```

### 4.3 Workflow Dispatch API呼び出し

```typescript
// integrations/github-actions.ts
interface GitHubActionsConfig {
  apiUrl: string;         // https://api.github.com
  owner: string;          // リポジトリオーナー
  repo: string;           // リポジトリ名
  workflowId: string;     // ワークフローファイル名
  token: string;          // PAT or GitHub App Token
}

class GitHubActionsService {
  async triggerDeployment(rfcNumber: string, branch: string): Promise<void> {
    await axios.post(
      `${config.apiUrl}/repos/${config.owner}/${config.repo}/actions/workflows/${config.workflowId}/dispatches`,
      {
        ref: branch,
        inputs: {
          rfc_number: rfcNumber,
          action: 'deploy'
        }
      },
      {
        headers: {
          'Authorization': `Bearer ${config.token}`,
          'Accept': 'application/vnd.github.v3+json'
        }
      }
    );
  }

  async triggerRollback(rfcNumber: string, branch: string): Promise<void> {
    // 同様にrollbackアクションをdispatch
  }
}
```

### 4.4 Webhook受信エンドポイント

| 項目 | 内容 |
|------|------|
| **メソッド** | POST |
| **エンドポイント** | /api/v1/webhooks/github |
| **認証** | GitHub Webhook Secret（HMAC-SHA256検証） |

**受信ペイロード（Workflow Run完了）:**
```json
{
  "action": "completed",
  "workflow_run": {
    "id": 12345,
    "name": "Change Management Integration",
    "status": "completed",
    "conclusion": "success",
    "inputs": {
      "rfc_number": "RFC-2026-045",
      "action": "deploy"
    }
  }
}
```

### 4.5 連携先ワークフローテンプレート

```yaml
# .github/workflows/change-management.yml
name: Change Management Integration

on:
  workflow_dispatch:
    inputs:
      rfc_number:
        description: 'RFC番号'
        required: true
        type: string
      action:
        description: 'アクション'
        required: true
        type: choice
        options:
          - deploy
          - rollback

jobs:
  execute-change:
    runs-on: ubuntu-latest
    steps:
      - name: 変更実施開始通知
        run: |
          curl -X PATCH \
            "${{ secrets.CAB_PLATFORM_URL }}/api/v1/rfcs/${{ inputs.rfc_number }}/status" \
            -H "Authorization: Bearer ${{ secrets.CAB_API_TOKEN }}" \
            -H "Content-Type: application/json" \
            -d '{"status": "in_progress", "actualStart": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}'

      - name: デプロイ実行
        if: ${{ inputs.action == 'deploy' }}
        id: deploy
        run: |
          echo "Executing deployment..."

      - name: 変更完了通知（成功）
        if: success() && inputs.action == 'deploy'
        run: |
          curl -X PATCH \
            "${{ secrets.CAB_PLATFORM_URL }}/api/v1/rfcs/${{ inputs.rfc_number }}/status" \
            -H "Authorization: Bearer ${{ secrets.CAB_API_TOKEN }}" \
            -H "Content-Type: application/json" \
            -d '{"status": "completed", "actualEnd": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}'

      - name: ロールバック実行（失敗時）
        if: failure()
        run: |
          curl -X POST \
            "${{ secrets.CAB_PLATFORM_URL }}/api/v1/execution/${{ inputs.rfc_number }}/rollback" \
            -H "Authorization: Bearer ${{ secrets.CAB_API_TOKEN }}" \
            -H "Content-Type: application/json" \
            -d '{"reason": "GitHub Actions deployment failed"}'
```

### 4.6 GitHub連携設定

| 設定項目 | 説明 | 環境変数 |
|---------|------|---------|
| GitHub API URL | GitHub API ベースURL | GITHUB_API_URL |
| リポジトリオーナー | 組織名またはユーザ名 | GITHUB_OWNER |
| リポジトリ名 | リポジトリ名 | GITHUB_REPO |
| ワークフローID | ワークフローファイル名 | GITHUB_WORKFLOW_ID |
| アクセストークン | PAT or GitHub App Token | GITHUB_TOKEN |
| Webhook Secret | Webhook署名検証用シークレット | GITHUB_WEBHOOK_SECRET |

---

## 5. ITSM連携

### 5.1 連携概要

| 項目 | 内容 |
|------|------|
| 連携方式 | REST API |
| 通信方向 | 双方向 |
| 用途 | インシデント連携、問題管理連携、CI情報取得 |
| 認証 | APIキー or OAuth2 |
| 優先度 | 推奨（P2） |

### 5.2 連携API

#### 5.2.1 インシデント関連RFC取得

| 項目 | 内容 |
|------|------|
| 方向 | プラットフォーム → ITSM |
| **メソッド** | GET |
| **エンドポイント** | ${ITSM_API_URL}/api/incidents/${incidentId} |
| 用途 | 緊急変更の関連インシデント情報取得 |

#### 5.2.2 変更結果のITSM反映

| 項目 | 内容 |
|------|------|
| 方向 | プラットフォーム → ITSM |
| **メソッド** | POST |
| **エンドポイント** | ${ITSM_API_URL}/api/changes |
| 用途 | RFC情報・実施結果のITSMへの同期 |

**送信ペイロード:**
```json
{
  "externalId": "RFC-2026-045",
  "title": "AD設定変更",
  "changeType": "normal",
  "status": "completed",
  "targetSystems": ["ActiveDirectory", "EntraID"],
  "plannedStart": "2026-04-01T22:00:00Z",
  "plannedEnd": "2026-04-01T23:00:00Z",
  "actualStart": "2026-04-01T22:00:00Z",
  "actualEnd": "2026-04-01T22:45:00Z",
  "result": "success",
  "requester": "yamada@mirai-kensetsu.co.jp"
}
```

#### 5.2.3 変更起因インシデント検知

| 項目 | 内容 |
|------|------|
| 方向 | ITSM → プラットフォーム |
| **メソッド** | POST |
| **エンドポイント** | /api/v1/webhooks/itsm/incidents |
| 用途 | 変更完了後24時間以内のインシデント自動関連付け |

### 5.3 ITSM連携設定

| 設定項目 | 説明 | 環境変数 |
|---------|------|---------|
| ITSM API URL | ITSM APIベースURL | ITSM_API_URL |
| APIキー | ITSM認証キー | ITSM_API_KEY |
| 同期有効 | 自動同期の有効/無効 | ITSM_SYNC_ENABLED |
| インシデント関連付け | インシデント自動関連付け有効 | ITSM_INCIDENT_LINK_ENABLED |

---

## 6. CMDB連携

### 6.1 連携概要

| 項目 | 内容 |
|------|------|
| 連携方式 | REST API |
| 通信方向 | 受信のみ（データ取得） |
| 用途 | CI情報取得、依存関係取得 |
| 優先度 | 推奨（P2） |

### 6.2 連携API

#### 6.2.1 CI一覧取得

| 項目 | 内容 |
|------|------|
| **メソッド** | GET |
| **エンドポイント** | ${CMDB_API_URL}/api/cis?system=${systemName} |
| 用途 | 対象システムのCI一覧取得 |

#### 6.2.2 CI依存関係取得

| 項目 | 内容 |
|------|------|
| **メソッド** | GET |
| **エンドポイント** | ${CMDB_API_URL}/api/cis/${ciId}/dependencies |
| 用途 | CIの依存関係ツリー取得 |

### 6.3 CMDB未連携時のフォールバック

CMDB連携が未設定の場合、システム内蔵の依存関係マップ（ImpactAnalyzer内のDEPENDENCY_MAP）を使用する。

---

## 7. エラーハンドリング

### 7.1 外部連携エラー分類

| エラー種別 | HTTPステータス | リトライ | フォールバック |
|-----------|-------------|---------|-------------|
| 接続タイムアウト | - | 自動リトライ（3回） | フォールバックチャネル |
| 認証エラー | 401/403 | リトライなし | 管理者アラート |
| レート制限 | 429 | Retry-Afterヘッダーに従う | 遅延送信 |
| サーバエラー | 500/502/503 | 自動リトライ（3回） | フォールバックチャネル |
| 不正リクエスト | 400 | リトライなし | エラーログ記録 |

### 7.2 サーキットブレーカー

| 項目 | 設定値 |
|------|--------|
| 失敗閾値 | 5回連続失敗 |
| オープン状態維持時間 | 60秒 |
| ハーフオープン試行回数 | 1回 |
| 監視対象 | 各外部連携アダプター |

```
Closed ──[失敗5回]──> Open ──[60秒後]──> Half-Open ──[成功]──> Closed
                                              │
                                         [失敗]──> Open
```

---

## 8. 連携監視

### 8.1 ヘルスチェック

| 連携先 | チェック方法 | 間隔 | アラート条件 |
|--------|-----------|------|------------|
| Teams Webhook | テスト送信 | 1時間 | 3回連続失敗 |
| SMTP | 接続確認 | 30分 | 2回連続失敗 |
| GitHub API | API疎通確認 | 1時間 | 3回連続失敗 |
| ITSM API | ヘルスエンドポイント | 1時間 | 3回連続失敗 |

### 8.2 メトリクス

| メトリクス | 説明 |
|-----------|------|
| external_api_request_total | 外部API呼び出し総数 |
| external_api_request_duration | 外部API応答時間 |
| external_api_error_total | 外部APIエラー総数 |
| notification_sent_total | 通知送信総数（チャネル別） |
| notification_failed_total | 通知送信失敗総数 |
| circuit_breaker_state | サーキットブレーカー状態 |

---

## 9. セキュリティ考慮事項

| 項目 | 対策 |
|------|------|
| Webhook URL | 環境変数で管理、ソースコードにハードコードしない |
| APIキー/トークン | 環境変数で管理、暗号化保存 |
| Webhook受信認証 | HMAC-SHA256署名検証（GitHub） |
| 通信暗号化 | 全外部通信はTLS 1.2以上 |
| アクセスログ | 全外部API呼び出しを監査ログに記録 |
| シークレットローテーション | 90日ごとにトークン/キーをローテーション |

---

*文書管理：本文書はバージョン管理対象。変更履歴はGitリポジトリで管理する。*
