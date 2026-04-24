# 📏 コーディング規約（Coding Standards）

> Construction SIEM Platform のコード品質基準と規約

---

## 📋 規約サマリー

| カテゴリ | ツール/規約 | 設定 |
|----------|-----------|------|
| 🐍 スタイル | PEP 8 + black | `line-length=120` |
| 📦 インポート | isort | black互換プロファイル |
| 🔍 リンター | flake8 | `max-line-length=120`, `max-complexity=10` |
| 🛡 セキュリティ | bandit | High/Medium/Low = 0 必須 |
| 🧪 テスト | pytest | `test_*.py` 命名規則 |
| 🌐 API | FastAPI + Pydantic | RBAC 必須 |
| 📝 コミット | Conventional Commits | `feat/fix/docs/...` |
| 🔀 ブランチ | feature/* → main | squash merge |

---

## 🐍 Python コードスタイル

### PEP 8 + Black

| 項目 | 設定値 |
|------|--------|
| フォーマッター | black |
| 行の最大長 | 120文字 |
| 文字列クォート | ダブルクォート（`"`） |
| 末尾カンマ | あり（trailing comma） |

#### black の設定（`pyproject.toml`）

```toml
[tool.black]
line-length = 120
target-version = ['py312']
```

#### 実行コマンド

```bash
# フォーマット実行
black . --line-length 120

# チェックのみ（CI用）
black . --check --line-length 120
```

### isort（インポート順序）

```toml
[tool.isort]
profile = "black"
line_length = 120
```

#### インポート順序

```python
# 1. 標準ライブラリ
import os
import sys
from datetime import datetime

# 2. サードパーティ
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# 3. ローカル
from api.auth import verify_token
from api.models import AlertModel
```

#### 実行コマンド

```bash
# ソート実行
isort .

# チェックのみ（CI用）
isort . --check-only
```

---

## 🔍 flake8 リンター

### 設定（`.flake8` または `setup.cfg`）

```ini
[flake8]
max-line-length = 120
max-complexity = 10
exclude = .git,__pycache__,venv,build,dist
ignore = E203,W503
```

| 設定項目 | 値 | 説明 |
|---------|------|------|
| `max-line-length` | 120 | 最大行長 |
| `max-complexity` | 10 | McCabe 循環的複雑度の上限 |
| `E203` | 無視 | black との互換性 |
| `W503` | 無視 | 二項演算子の改行位置（PEP 8更新済み） |

#### 実行コマンド

```bash
flake8 api/ tests/
```

---

## 🛡 bandit セキュリティスキャン

### 必須条件

| レベル | 許容数 |
|--------|:-----:|
| 🔴 High | **0** |
| 🟡 Medium | **0** |
| 🔵 Low | **0** |

> CI パイプラインで bandit スキャンが実行され、いずれかのレベルで検出があった場合はビルドが失敗します。

### 設定（`.bandit.yml`）

```yaml
exclude_dirs:
  - tests
  - venv
skips: []
```

#### 実行コマンド

```bash
# 全スキャン
bandit -r api/ -f json

# 重要度指定
bandit -r api/ -ll  # Medium以上
bandit -r api/ -lll # High のみ
```

### よくある検出と対処

| コード | 検出内容 | 対処方法 |
|--------|---------|---------|
| B105 | ハードコードされたパスワード | 環境変数から取得に変更 |
| B301 | 安全でないデシリアライズの使用 | JSON等の安全な形式に置き換え |
| B608 | SQL インジェクション | パラメータ化クエリを使用 |
| B201 | Flask デバッグモード | 本番では `debug=False` |

---

## 🌐 FastAPI + Pydantic 規約

### API エンドポイント

```python
from fastapi import APIRouter, Depends, HTTPException, status
from api.auth import get_current_user, require_role
from api.models import AlertCreate, AlertResponse

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


@router.post(
    "/ingest",
    response_model=AlertResponse,
    status_code=status.HTTP_201_CREATED,
    summary="アラートインジェスト",
    description="新しいアラートをシステムに取り込みます",
)
async def ingest_alert(
    alert: AlertCreate,
    current_user: dict = Depends(require_role(["admin", "analyst"])),
):
    """アラートをインジェストする。admin または analyst ロールが必要。"""
    ...
```

### Pydantic モデル

```python
from pydantic import BaseModel, Field, validator
from enum import Enum
from datetime import datetime
from typing import Optional


class SeverityLevel(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


class AlertCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="アラートタイトル")
    severity: SeverityLevel = Field(..., description="重要度")
    source: str = Field(..., description="ソース")
    description: str = Field(..., description="説明")
    site: Optional[str] = Field(None, description="建設現場名")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "不審なポートスキャン検出",
                "severity": "critical",
                "source": "firewall",
                "description": "192.168.1.100 から複数ポートへのスキャンを検出",
                "site": "東京建設現場A",
            }
        }
```

### RBAC（ロールベースアクセス制御）

全てのエンドポイントに RBAC を適用すること。

```python
# ロール制限の適用
@router.get("/roles", dependencies=[Depends(require_role(["admin"]))])
async def list_roles():
    ...

# 全認証ユーザー許可
@router.get("/alerts", dependencies=[Depends(get_current_user)])
async def list_alerts():
    ...
```

---

## 🧪 テスト規約

### ファイル命名規則

| パターン | 説明 | 例 |
|---------|------|------|
| `test_*.py` | テストファイル | `test_api.py`, `test_auth.py` |
| `test_*` | テスト関数 | `test_create_alert_success` |
| `conftest.py` | フィクスチャ定義 | テストディレクトリ直下 |

### テスト構造

```python
import pytest
from httpx import AsyncClient


class TestAlertIngest:
    """アラートインジェストのテストクラス"""

    @pytest.mark.asyncio
    async def test_ingest_valid_alert(self, client: AsyncClient, auth_headers: dict):
        """正常なアラートのインジェストが成功すること"""
        # Arrange
        alert_data = {
            "title": "テストアラート",
            "severity": "high",
            "source": "firewall",
            "description": "テスト説明",
        }

        # Act
        response = await client.post("/api/v1/alerts/ingest", json=alert_data, headers=auth_headers)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["severity"] == "high"

    @pytest.mark.asyncio
    async def test_ingest_invalid_severity(self, client: AsyncClient, auth_headers: dict):
        """不正な severity でバリデーションエラーになること"""
        alert_data = {
            "title": "テストアラート",
            "severity": "invalid",
            "source": "firewall",
            "description": "テスト説明",
        }

        response = await client.post("/api/v1/alerts/ingest", json=alert_data, headers=auth_headers)

        assert response.status_code == 422
```

### テスト実行コマンド

```bash
# 全テスト実行
pytest tests/ -v

# カバレッジ付き
pytest tests/ --cov=api --cov-report=term-missing --cov-report=html

# 特定テストのみ
pytest tests/test_auth.py -v -k "test_token"

# 非同期テスト
pytest tests/ -v --asyncio-mode=auto
```

---

## 📝 コミットメッセージ規約

### Conventional Commits

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### タイプ一覧

| タイプ | 説明 | 例 |
|--------|------|------|
| `feat` | 新機能 | `feat(alerts): アラートインジェストAPI追加` |
| `fix` | バグ修正 | `fix(auth): トークン期限切れの判定を修正` |
| `docs` | ドキュメント | `docs(api): Swagger説明を更新` |
| `refactor` | リファクタリング | `refactor(models): Pydanticモデル共通化` |
| `style` | フォーマット修正 | `style: blackフォーマット適用` |
| `test` | テスト追加・修正 | `test(kpi): KPI計算のエッジケース追加` |
| `chore` | その他雑務 | `chore(deps): requirements.txt更新` |

### コミットメッセージ例

```
feat(incidents): SLAタイマー自動開始機能を追加

インシデント作成時に優先度に基づいてSLAタイマーを自動的に
開始するようにした。P1は15分、P2は30分、P3は2時間、P4は8時間。

Closes #42
```

---

## 🔀 プルリクエスト規約

### ブランチ命名

```
feature/<issue-number>-<short-description>
```

例: `feature/42-incident-sla-timer`

### PR ルール

| ルール | 説明 |
|--------|------|
| ✅ ブランチ | `feature/*` → `main` |
| ✅ マージ方式 | Squash Merge |
| ✅ CI 必須 | 全ジョブ成功が必要 |
| ✅ レビュー | 最低1名の承認 |
| ❌ main 直接 push | **禁止** |

### PR テンプレート

```markdown
## 概要
<!-- 変更内容の説明 -->

## 変更種別
- [ ] 新機能（feat）
- [ ] バグ修正（fix）
- [ ] リファクタリング（refactor）
- [ ] テスト（test）
- [ ] ドキュメント（docs）

## テスト
- [ ] pytest 全テスト PASSED
- [ ] カバレッジ 85% 以上を維持
- [ ] bandit スキャン 0 件

## 関連 Issue
Closes #
```
