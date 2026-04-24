# コーディング規約（Coding Standards）

| 項目 | 内容 |
|------|------|
| 文書番号 | DEV-002 |
| バージョン | 1.0 |
| 作成日 | 2026-03-26 |
| 最終更新日 | 2026-03-26 |
| 作成者 | 開発チーム |
| 対象プロジェクト | 建設業 統合リスク＆コンプライアンス管理システム（Construction-GRC-System） |

---

## 1. 概要

本文書は、Construction-GRC-Systemの開発におけるコーディング規約を定める。チーム全体でのコードの一貫性、可読性、保守性を確保することを目的とする。

---

## 2. 共通ルール

### 2.1 基本原則

- **DRY（Don't Repeat Yourself）**: 重複コードを避け、共通処理は抽象化する
- **KISS（Keep It Simple, Stupid）**: シンプルな設計を心がける
- **YAGNI（You Aren't Gonna Need It）**: 現時点で不要な機能は実装しない
- **単一責任の原則**: 1つのモジュール・クラス・関数は1つの責任を持つ
- **早期リターン**: ネストを深くせず、条件を満たさない場合は早期にリターンする

### 2.2 ファイルのエンコーディング

- 文字コード: UTF-8（BOMなし）
- 改行コード: LF
- ファイル末尾に改行を1つ入れる
- 末尾の空白文字を除去する

### 2.3 コメント規則

- コードの「なぜ（Why）」を説明するコメントを書く
- コードの「何（What）」は変数名・関数名で自明にする
- TODO/FIXME/HACK コメントには担当者と日付を記載する

```python
# TODO(yamada, 2026-03-26): パフォーマンス改善が必要
# FIXME(suzuki, 2026-03-26): 境界値のバリデーションが未実装
```

---

## 3. Python コーディング規約

### 3.1 基本規約

- PEP 8 に準拠する
- 自動フォーマッターとして **Ruff** を使用する（Black互換フォーマット）
- インポート順序は **isort**（Ruff統合）で自動整理する
- リンターとして **Ruff** を使用する

### 3.2 ツール設定

#### pyproject.toml

```toml
[tool.ruff]
target-version = "py312"
line-length = 120
src = ["backend"]

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "UP",   # pyupgrade
    "S",    # flake8-bandit (security)
    "T20",  # flake8-print
    "SIM",  # flake8-simplify
    "DJ",   # flake8-django
]
ignore = [
    "E501",   # line-length（formatterに任せる）
    "S101",   # assert使用（テストでは許可）
]

[tool.ruff.lint.isort]
known-first-party = ["apps", "config"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

### 3.3 命名規則

| 対象 | 規則 | 例 |
|------|------|-----|
| モジュール | snake_case | `risk_assessment.py` |
| クラス | PascalCase | `RiskAssessment` |
| 関数・メソッド | snake_case | `calculate_risk_score()` |
| 変数 | snake_case | `risk_level` |
| 定数 | UPPER_SNAKE_CASE | `MAX_RISK_SCORE` |
| プライベート属性 | 先頭アンダースコア | `_internal_state` |
| Django モデル | PascalCase（単数形） | `Risk`, `ComplianceItem` |
| シリアライザー | PascalCase + Serializer | `RiskSerializer` |
| ビュー | PascalCase + ViewSet/APIView | `RiskViewSet` |
| URL パターン | kebab-case | `risk-assessments/` |

### 3.4 Django モデル規約

```python
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel


class Risk(BaseModel):
    """リスク管理モデル。

    建設プロジェクトに関連するリスクを管理する。
    """

    class RiskLevel(models.TextChoices):
        """リスクレベルの選択肢。"""

        LOW = "low", _("低")
        MEDIUM = "medium", _("中")
        HIGH = "high", _("高")
        CRITICAL = "critical", _("重大")

    title = models.CharField(
        _("タイトル"),
        max_length=200,
    )
    description = models.TextField(
        _("説明"),
        blank=True,
        default="",
    )
    risk_level = models.CharField(
        _("リスクレベル"),
        max_length=20,
        choices=RiskLevel.choices,
        default=RiskLevel.MEDIUM,
    )
    probability = models.DecimalField(
        _("発生確率"),
        max_digits=5,
        decimal_places=2,
    )
    impact = models.DecimalField(
        _("影響度"),
        max_digits=5,
        decimal_places=2,
    )

    class Meta:
        verbose_name = _("リスク")
        verbose_name_plural = _("リスク")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["risk_level", "-created_at"]),
        ]

    def __str__(self) -> str:
        return self.title

    @property
    def risk_score(self) -> float:
        """リスクスコアを計算する。"""
        return float(self.probability * self.impact)
```

### 3.5 Django REST Framework 規約

#### シリアライザー

```python
from rest_framework import serializers

from apps.risks.models import Risk


class RiskListSerializer(serializers.ModelSerializer):
    """リスク一覧用シリアライザー。"""

    risk_score = serializers.ReadOnlyField()

    class Meta:
        model = Risk
        fields = [
            "id",
            "title",
            "risk_level",
            "risk_score",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class RiskDetailSerializer(serializers.ModelSerializer):
    """リスク詳細用シリアライザー。"""

    risk_score = serializers.ReadOnlyField()

    class Meta:
        model = Risk
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_probability(self, value):
        """発生確率のバリデーション。"""
        if not (0 <= value <= 1):
            raise serializers.ValidationError("発生確率は0から1の間で指定してください。")
        return value
```

#### ビューセット

```python
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.risks.models import Risk
from apps.risks.serializers import RiskDetailSerializer, RiskListSerializer


class RiskViewSet(viewsets.ModelViewSet):
    """リスク管理のビューセット。"""

    queryset = Risk.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["risk_level", "status"]
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "risk_level"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return RiskListSerializer
        return RiskDetailSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
```

### 3.6 テストコード規約

```python
import pytest
from django.urls import reverse
from rest_framework import status

from apps.risks.factories import RiskFactory


@pytest.mark.django_db
class TestRiskAPI:
    """リスクAPIのテスト。"""

    def setup_method(self):
        """テストの前処理。"""
        self.url = reverse("api:risk-list")

    def test_リスク一覧を取得できること(self, authenticated_client):
        """認証済みユーザーはリスク一覧を取得できる。"""
        RiskFactory.create_batch(3)

        response = authenticated_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 3

    def test_未認証ユーザーはリスク一覧を取得できないこと(self, api_client):
        """未認証ユーザーは401エラーになる。"""
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
```

### 3.7 docstring 規約

Google スタイルの docstring を使用する。

```python
def calculate_risk_score(probability: float, impact: float, weight: float = 1.0) -> float:
    """リスクスコアを計算する。

    発生確率と影響度からリスクスコアを算出する。
    オプションで重み付け係数を指定可能。

    Args:
        probability: 発生確率（0.0 - 1.0）。
        impact: 影響度（1 - 10）。
        weight: 重み付け係数。デフォルトは1.0。

    Returns:
        算出されたリスクスコア。

    Raises:
        ValueError: probability が 0-1 の範囲外の場合。
        ValueError: impact が 1-10 の範囲外の場合。
    """
    if not 0 <= probability <= 1:
        raise ValueError(f"probability must be between 0 and 1, got {probability}")
    if not 1 <= impact <= 10:
        raise ValueError(f"impact must be between 1 and 10, got {impact}")
    return probability * impact * weight
```

---

## 4. TypeScript / Vue.js コーディング規約

### 4.1 基本規約

- TypeScript を使用し、`strict` モードを有効にする
- フォーマッターとして **Prettier** を使用する
- リンターとして **ESLint**（`@typescript-eslint`、`eslint-plugin-vue`）を使用する
- Composition API（`<script setup>` 構文）を使用する

### 4.2 ツール設定

#### .eslintrc.cjs

```javascript
module.exports = {
  root: true,
  env: {
    browser: true,
    es2022: true,
    node: true,
  },
  extends: [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:vue/vue3-recommended",
    "@vue/eslint-config-typescript",
    "@vue/eslint-config-prettier",
  ],
  parserOptions: {
    ecmaVersion: "latest",
  },
  rules: {
    "vue/multi-word-component-names": "error",
    "vue/component-name-in-template-casing": ["error", "PascalCase"],
    "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
    "@typescript-eslint/explicit-function-return-type": "warn",
    "no-console": ["warn", { allow: ["warn", "error"] }],
  },
};
```

#### .prettierrc

```json
{
  "semi": false,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "all",
  "printWidth": 100,
  "arrowParens": "always",
  "endOfLine": "lf",
  "vueIndentScriptAndStyle": false
}
```

### 4.3 命名規則

| 対象 | 規則 | 例 |
|------|------|-----|
| コンポーネントファイル | PascalCase | `RiskAssessmentForm.vue` |
| コンポーネント名 | PascalCase | `RiskAssessmentForm` |
| Composable | camelCase + `use`プレフィックス | `useRiskAssessment.ts` |
| ストア | camelCase + `use`プレフィックス + `Store` | `useRiskStore.ts` |
| 型・インターフェース | PascalCase | `RiskItem`, `ApiResponse` |
| 定数 | UPPER_SNAKE_CASE | `MAX_RISK_SCORE` |
| 変数・関数 | camelCase | `riskLevel`, `calculateScore()` |
| イベント | camelCase | `@update:modelValue` |
| CSS クラス | kebab-case（BEM推奨） | `risk-card__header--active` |

### 4.4 Vue コンポーネント規約

#### 単一ファイルコンポーネント（SFC）構造

```vue
<script setup lang="ts">
/**
 * リスク評価フォームコンポーネント
 *
 * リスクの新規作成・編集に使用するフォーム。
 */
import { computed, ref } from 'vue'
import { useRiskStore } from '@/stores/useRiskStore'
import type { RiskFormData } from '@/types/risk'

// ---- Props ----
interface Props {
  /** 編集対象のリスクID（新規作成時はundefined） */
  riskId?: number
  /** 読み取り専用モード */
  readonly?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  riskId: undefined,
  readonly: false,
})

// ---- Emits ----
interface Emits {
  (e: 'submit', data: RiskFormData): void
  (e: 'cancel'): void
}

const emit = defineEmits<Emits>()

// ---- Store ----
const riskStore = useRiskStore()

// ---- State ----
const formData = ref<RiskFormData>({
  title: '',
  description: '',
  riskLevel: 'medium',
  probability: 0,
  impact: 0,
})

// ---- Computed ----
const riskScore = computed<number>(() => {
  return formData.value.probability * formData.value.impact
})

const isValid = computed<boolean>(() => {
  return formData.value.title.length > 0 && formData.value.probability > 0
})

// ---- Methods ----
function handleSubmit(): void {
  if (!isValid.value) return
  emit('submit', formData.value)
}

function handleCancel(): void {
  emit('cancel')
}
</script>

<template>
  <VCard>
    <VCardTitle>リスク評価</VCardTitle>
    <VCardText>
      <VForm @submit.prevent="handleSubmit">
        <VTextField
          v-model="formData.title"
          label="タイトル"
          :readonly="readonly"
          required
        />
        <VTextarea
          v-model="formData.description"
          label="説明"
          :readonly="readonly"
        />
        <VSelect
          v-model="formData.riskLevel"
          :items="riskStore.riskLevelOptions"
          label="リスクレベル"
          :readonly="readonly"
        />
        <div class="risk-score">
          リスクスコア: {{ riskScore }}
        </div>
      </VForm>
    </VCardText>
    <VCardActions>
      <VSpacer />
      <VBtn variant="text" @click="handleCancel">
        キャンセル
      </VBtn>
      <VBtn
        color="primary"
        :disabled="!isValid || readonly"
        @click="handleSubmit"
      >
        保存
      </VBtn>
    </VCardActions>
  </VCard>
</template>

<style scoped>
.risk-score {
  margin-top: 16px;
  font-size: 1.2rem;
  font-weight: bold;
}
</style>
```

### 4.5 型定義規約

```typescript
// types/risk.ts

/** リスクレベル */
export type RiskLevel = 'low' | 'medium' | 'high' | 'critical'

/** リスクアイテム（API レスポンス） */
export interface RiskItem {
  id: number
  title: string
  description: string
  riskLevel: RiskLevel
  probability: number
  impact: number
  riskScore: number
  createdAt: string
  updatedAt: string
}

/** リスクフォームデータ */
export interface RiskFormData {
  title: string
  description: string
  riskLevel: RiskLevel
  probability: number
  impact: number
}

/** ページネーション付きレスポンス */
export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}
```

### 4.6 API通信規約

```typescript
// services/api/riskApi.ts

import { apiClient } from '@/services/api/client'
import type { PaginatedResponse, RiskFormData, RiskItem } from '@/types/risk'

const BASE_URL = '/api/v1/risks/'

export const riskApi = {
  /** リスク一覧を取得する */
  async getList(params?: Record<string, unknown>): Promise<PaginatedResponse<RiskItem>> {
    const { data } = await apiClient.get<PaginatedResponse<RiskItem>>(BASE_URL, { params })
    return data
  },

  /** リスク詳細を取得する */
  async getDetail(id: number): Promise<RiskItem> {
    const { data } = await apiClient.get<RiskItem>(`${BASE_URL}${id}/`)
    return data
  },

  /** リスクを作成する */
  async create(formData: RiskFormData): Promise<RiskItem> {
    const { data } = await apiClient.post<RiskItem>(BASE_URL, formData)
    return data
  },

  /** リスクを更新する */
  async update(id: number, formData: Partial<RiskFormData>): Promise<RiskItem> {
    const { data } = await apiClient.patch<RiskItem>(`${BASE_URL}${id}/`, formData)
    return data
  },

  /** リスクを削除する */
  async delete(id: number): Promise<void> {
    await apiClient.delete(`${BASE_URL}${id}/`)
  },
}
```

### 4.7 Pinia ストア規約

```typescript
// stores/useRiskStore.ts

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { riskApi } from '@/services/api/riskApi'
import type { RiskItem, RiskFormData } from '@/types/risk'

export const useRiskStore = defineStore('risk', () => {
  // ---- State ----
  const risks = ref<RiskItem[]>([])
  const currentRisk = ref<RiskItem | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const totalCount = ref(0)

  // ---- Getters ----
  const highRisks = computed(() =>
    risks.value.filter((r) => r.riskLevel === 'high' || r.riskLevel === 'critical'),
  )

  const riskLevelOptions = computed(() => [
    { title: '低', value: 'low' },
    { title: '中', value: 'medium' },
    { title: '高', value: 'high' },
    { title: '重大', value: 'critical' },
  ])

  // ---- Actions ----
  async function fetchRisks(params?: Record<string, unknown>): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const response = await riskApi.getList(params)
      risks.value = response.results
      totalCount.value = response.count
    } catch (e) {
      error.value = '一覧の取得に失敗しました。'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function createRisk(formData: RiskFormData): Promise<RiskItem> {
    loading.value = true
    error.value = null
    try {
      const newRisk = await riskApi.create(formData)
      risks.value.unshift(newRisk)
      totalCount.value += 1
      return newRisk
    } catch (e) {
      error.value = '作成に失敗しました。'
      throw e
    } finally {
      loading.value = false
    }
  }

  // ---- Reset ----
  function $reset(): void {
    risks.value = []
    currentRisk.value = null
    loading.value = false
    error.value = null
    totalCount.value = 0
  }

  return {
    risks,
    currentRisk,
    loading,
    error,
    totalCount,
    highRisks,
    riskLevelOptions,
    fetchRisks,
    createRisk,
    $reset,
  }
})
```

---

## 5. ディレクトリ構成規則

### 5.1 バックエンド（Django）

```
backend/apps/<app_name>/
├── __init__.py
├── admin.py             # 管理画面設定
├── apps.py              # アプリケーション設定
├── constants.py         # 定数定義
├── exceptions.py        # カスタム例外
├── factories.py         # テスト用ファクトリ
├── filters.py           # フィルター定義
├── managers.py          # カスタムマネージャー
├── models.py            # モデル定義
├── permissions.py       # カスタムパーミッション
├── serializers.py       # シリアライザー定義
├── services.py          # ビジネスロジック
├── signals.py           # シグナル定義
├── tasks.py             # Celery タスク
├── tests/               # テストディレクトリ
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_serializers.py
│   ├── test_views.py
│   └── test_services.py
├── urls.py              # URL定義
└── views.py             # ビュー定義
```

### 5.2 フロントエンド（Vue.js）

```
frontend/src/
├── assets/              # 静的リソース
│   ├── images/
│   └── styles/
│       ├── _variables.scss
│       └── main.scss
├── components/          # 共通コンポーネント
│   ├── common/          # 汎用コンポーネント
│   │   ├── AppDataTable.vue
│   │   ├── AppConfirmDialog.vue
│   │   └── AppStatusBadge.vue
│   └── domain/          # ドメイン固有コンポーネント
│       ├── risk/
│       │   ├── RiskCard.vue
│       │   └── RiskScoreChart.vue
│       └── compliance/
├── composables/         # Composition API
│   ├── useAuth.ts
│   ├── usePagination.ts
│   └── useNotification.ts
├── layouts/             # レイアウト
│   ├── DefaultLayout.vue
│   └── AuthLayout.vue
├── pages/               # ページコンポーネント
│   ├── risks/
│   │   ├── RiskListPage.vue
│   │   ├── RiskDetailPage.vue
│   │   └── RiskCreatePage.vue
│   └── compliance/
├── plugins/             # プラグイン設定
│   ├── vuetify.ts
│   └── pinia.ts
├── router/              # ルーティング
│   ├── index.ts
│   └── guards.ts
├── services/            # API通信
│   └── api/
│       ├── client.ts
│       ├── riskApi.ts
│       └── interceptors.ts
├── stores/              # Pinia ストア
│   ├── useAuthStore.ts
│   └── useRiskStore.ts
├── types/               # TypeScript型定義
│   ├── risk.ts
│   ├── compliance.ts
│   └── common.ts
├── utils/               # ユーティリティ
│   ├── date.ts
│   ├── format.ts
│   └── validation.ts
├── App.vue
└── main.ts
```

---

## 6. セキュリティ関連規約

### 6.1 バックエンド

- SQL インジェクション対策: Django ORM を使用し、生SQLは原則禁止
- XSS 対策: Django テンプレートの自動エスケープ機能を利用
- CSRF 対策: Django の CSRF ミドルウェアを有効にする
- 認証情報のハードコーディング禁止（環境変数を使用）
- `DEBUG = True` を本番環境で使用しない
- `SECRET_KEY` を環境変数で管理する
- パスワードは Django の標準ハッシュ機能を使用

### 6.2 フロントエンド

- `v-html` の使用は原則禁止（XSS リスク）
- API トークンをローカルストレージに保存しない（httpOnly Cookie 推奨）
- ユーザー入力は常にバリデーションする
- 外部リンクには `rel="noopener noreferrer"` を付与する

---

## 7. パフォーマンス規約

### 7.1 バックエンド

- N+1 クエリを避ける（`select_related`, `prefetch_related` を使用）
- 大量データの取得にはページネーションを必須とする
- 重い処理は Celery タスクに委譲する
- キャッシュを適切に活用する（Redis）

### 7.2 フロントエンド

- コンポーネントの遅延ロード（`defineAsyncComponent` / ルート分割）
- 画像の最適化（WebP形式、遅延ロード）
- 不要な再レンダリングを避ける（`v-memo`, `computed` の適切な使用）
- バンドルサイズの監視（`rollup-plugin-visualizer`）

---

## 8. アクセシビリティ規約

- WCAG 2.1 AA レベルに準拠する
- `aria-label`, `aria-describedby` を適切に使用する
- キーボード操作に対応する
- 色のコントラスト比を確保する（4.5:1以上）
- Vuetify コンポーネントの標準アクセシビリティ機能を活用する

---

## 改訂履歴

| バージョン | 日付 | 変更内容 | 変更者 |
|-----------|------|---------|--------|
| 1.0 | 2026-03-26 | 初版作成 | 開発チーム |
