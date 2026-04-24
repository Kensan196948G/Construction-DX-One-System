# コーディング規約
## IT変更管理・リリース自動化プラットフォーム（IT-Change-CAB-Platform）

| 項目 | 内容 |
|------|------|
| **文書番号** | DEV-CAB-002 |
| **バージョン** | 1.0.0 |
| **作成日** | 2026-03-26 |
| **作成者** | みらい建設工業 IT部門 |
| **対象リポジトリ** | Kensan196948G/IT-Change-CAB-Platform |

---

## 1. 共通規約

### 1.1 フォーマッター・リンター

| ツール | 設定ファイル | 用途 |
|-------|------------|------|
| Prettier | `.prettierrc` | コードフォーマット |
| ESLint | `.eslintrc.js` | コード品質チェック |
| TypeScript | `tsconfig.json` | 型チェック |

### 1.2 Prettier設定

```json
{
  "semi": true,
  "trailingComma": "all",
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false,
  "bracketSpacing": true,
  "arrowParens": "always",
  "endOfLine": "lf"
}
```

### 1.3 共通ルール

| ルール | 規約 |
|-------|------|
| インデント | スペース2つ |
| 行末 | LF（Unix形式） |
| ファイル末尾 | 空行1行 |
| 最大行長 | 100文字 |
| 文字コード | UTF-8 |
| クォート | シングルクォート |
| セミコロン | あり |

---

## 2. TypeScript規約

### 2.1 型定義

| ルール | 良い例 | 悪い例 |
|-------|--------|--------|
| 明示的な型注釈 | `const name: string = 'test';` | `const name = 'test';`（プリミティブは許容） |
| any禁止 | `unknown` を使用 | `any` |
| interface優先 | `interface User { ... }` | `type User = { ... }`（union/intersectionはtype使用） |
| enum非推奨 | `const STATUSES = { ... } as const;` | `enum Status { ... }` |
| 戻り値型明示 | `function getUser(): User { ... }` | `function getUser() { ... }` |

### 2.2 命名規則

| 対象 | 規則 | 例 |
|------|------|-----|
| 変数・関数 | camelCase | `rfcNumber`, `getRfcById()` |
| クラス | PascalCase | `ImpactAnalyzer`, `ConflictDetector` |
| インターフェース | PascalCase（I接頭辞なし） | `ChangeRequest`, `CabDecision` |
| 型エイリアス | PascalCase | `RfcStatus`, `ChangeType` |
| 定数 | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT`, `DEFAULT_PAGE_SIZE` |
| ファイル名（コンポーネント） | PascalCase | `RFCCreate.tsx`, `CABDashboard.tsx` |
| ファイル名（ユーティリティ） | kebab-case | `impact-analyzer.ts`, `date-utils.ts` |
| ディレクトリ名 | kebab-case | `api/`, `services/`, `custom-hooks/` |
| テストファイル | 対象ファイル名 + `.test` | `impact-analyzer.test.ts` |

### 2.3 インポート順序

```typescript
// 1. Node.js組み込みモジュール
import path from 'path';
import { readFile } from 'fs/promises';

// 2. 外部パッケージ（空行で区切る）
import express from 'express';
import { Pool } from 'pg';
import { Queue } from 'bullmq';

// 3. 内部モジュール（空行で区切る）
import { ImpactAnalyzer } from '../services/impact-analyzer';
import { ConflictDetector } from '../services/conflict-detector';

// 4. 型のみのインポート（空行で区切る）
import type { ChangeRequest, CabDecision } from '../types';
```

### 2.4 エラーハンドリング

```typescript
// 良い例：カスタムエラークラスの使用
class RfcNotFoundError extends Error {
  constructor(rfcId: string) {
    super(`RFC not found: ${rfcId}`);
    this.name = 'RfcNotFoundError';
  }
}

// 良い例：適切なエラーハンドリング
async function getRfc(id: string): Promise<ChangeRequest> {
  try {
    const rfc = await rfcRepository.findById(id);
    if (!rfc) {
      throw new RfcNotFoundError(id);
    }
    return rfc;
  } catch (error) {
    if (error instanceof RfcNotFoundError) {
      throw error; // 既知のエラーはそのままスロー
    }
    logger.error('RFC取得エラー', { id, error });
    throw new InternalError('RFC取得に失敗しました');
  }
}
```

### 2.5 非同期処理

| ルール | 説明 |
|-------|------|
| async/await 使用 | コールバックや`.then()`チェーンの代わりにasync/awaitを使用 |
| Promise.all 活用 | 独立した非同期処理は`Promise.all`で並列実行 |
| エラーハンドリング | async関数は必ずtry-catchで囲む、または呼び出し元で処理 |

---

## 3. React / フロントエンド規約

### 3.1 コンポーネント設計

| ルール | 説明 |
|-------|------|
| 関数コンポーネント | クラスコンポーネントは使用しない |
| コンポーネントの分割 | 200行を超える場合はサブコンポーネントに分割 |
| Props型定義 | interfaceで明示的に定義 |
| デフォルトエクスポート | ページコンポーネントのみ許容、それ以外はnamed export |

### 3.2 コンポーネント構造

```typescript
// 良い例：標準的なコンポーネント構造
import { useState, useCallback } from 'react';
import { Button, Form, Input, message } from 'antd';

import { useCreateRfc } from '../../hooks/useRfc';
import type { RfcFormValues } from '../../types';

interface RFCCreateFormProps {
  onSuccess: (rfcId: string) => void;
  onCancel: () => void;
}

export const RFCCreateForm: React.FC<RFCCreateFormProps> = ({ onSuccess, onCancel }) => {
  // 1. Hooks
  const [form] = Form.useForm<RfcFormValues>();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { mutateAsync: createRfc } = useCreateRfc();

  // 2. イベントハンドラ
  const handleSubmit = useCallback(async (values: RfcFormValues) => {
    setIsSubmitting(true);
    try {
      const result = await createRfc(values);
      message.success('RFCを作成しました');
      onSuccess(result.id);
    } catch (error) {
      message.error('RFC作成に失敗しました');
    } finally {
      setIsSubmitting(false);
    }
  }, [createRfc, onSuccess]);

  // 3. レンダリング
  return (
    <Form form={form} onFinish={handleSubmit} layout="vertical">
      <Form.Item name="title" label="タイトル" rules={[{ required: true }]}>
        <Input />
      </Form.Item>
      {/* ... */}
      <Button type="primary" htmlType="submit" loading={isSubmitting}>
        作成
      </Button>
      <Button onClick={onCancel}>キャンセル</Button>
    </Form>
  );
};
```

### 3.3 カスタムフック

| ルール | 説明 |
|-------|------|
| 命名 | `use` プレフィックス（例: `useRfc`, `useAuth`） |
| 配置 | `src/hooks/` ディレクトリ |
| 責務 | 1フックにつき1つの関心事 |
| テスト | `@testing-library/react-hooks` でテスト |

### 3.4 状態管理

| 状態の種類 | 管理方法 |
|-----------|---------|
| ローカル状態（フォーム入力等） | `useState` |
| サーバー状態（API データ） | React Query（TanStack Query） |
| グローバル状態（認証情報等） | React Context |
| URL状態（フィルタ・ページング） | URL パラメータ（React Router） |

---

## 4. バックエンドAPI規約

### 4.1 RESTful API設計

| ルール | 説明 | 例 |
|-------|------|-----|
| リソース名は複数形 | コレクションは複数形 | `/api/v1/rfcs` |
| ネスト制限 | 2階層まで | `/api/v1/rfcs/:id/decisions` |
| バージョニング | URLにバージョンを含める | `/api/v1/...` |
| ケバブケース | URLパスはケバブケース | `/api/v1/freeze-periods` |

### 4.2 HTTPステータスコード

| コード | 用途 |
|--------|------|
| 200 | 取得・更新成功 |
| 201 | 作成成功 |
| 204 | 削除成功（レスポンスボディなし） |
| 400 | バリデーションエラー |
| 401 | 認証エラー |
| 403 | 認可エラー（権限不足） |
| 404 | リソース未検出 |
| 409 | 競合（重複等） |
| 422 | 処理不可能（ビジネスルール違反） |
| 429 | レート制限超過 |
| 500 | サーバーエラー |

### 4.3 レスポンス形式

```typescript
// 成功レスポンス
{
  "data": { ... },
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 150
  }
}

// エラーレスポンス
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "入力内容に誤りがあります",
    "details": [
      { "field": "title", "message": "タイトルは必須です" }
    ]
  }
}
```

---

## 5. ディレクトリ構成

### 5.1 バックエンド

```
backend/
├── src/
│   ├── api/                    # APIエンドポイント
│   │   ├── rfcs/               # RFC管理
│   │   │   ├── rfc.controller.ts
│   │   │   ├── rfc.service.ts
│   │   │   ├── rfc.repository.ts
│   │   │   ├── rfc.validator.ts
│   │   │   └── rfc.routes.ts
│   │   ├── cab/                # CAB管理
│   │   ├── calendar/           # カレンダー
│   │   └── reports/            # レポート
│   ├── services/               # ビジネスロジック
│   │   ├── impact-analyzer.ts
│   │   ├── conflict-detector.ts
│   │   └── notification.ts
│   ├── jobs/                   # バックグラウンドジョブ
│   ├── middleware/             # Express ミドルウェア
│   │   ├── auth.ts
│   │   ├── error-handler.ts
│   │   └── rate-limiter.ts
│   ├── database/               # DB設定・マイグレーション
│   │   ├── migrations/
│   │   └── seeds/
│   ├── types/                  # 型定義
│   ├── utils/                  # ユーティリティ
│   └── config/                 # 設定
├── tests/                      # テスト
│   ├── unit/
│   ├── integration/
│   └── fixtures/
└── package.json
```

### 5.2 フロントエンド

```
frontend/
├── src/
│   ├── pages/                  # ページコンポーネント
│   │   ├── RFCList.tsx
│   │   ├── RFCCreate.tsx
│   │   ├── RFCDetail.tsx
│   │   ├── CABDashboard.tsx
│   │   ├── ChangeCalendar.tsx
│   │   └── KPIDashboard.tsx
│   ├── components/             # 共有コンポーネント
│   │   ├── common/             # 汎用コンポーネント
│   │   ├── rfc/                # RFC関連コンポーネント
│   │   ├── cab/                # CAB関連コンポーネント
│   │   └── layout/             # レイアウトコンポーネント
│   ├── hooks/                  # カスタムフック
│   ├── services/               # API呼び出し
│   ├── types/                  # 型定義
│   ├── utils/                  # ユーティリティ
│   ├── contexts/               # React Context
│   ├── constants/              # 定数
│   └── styles/                 # スタイル
├── tests/                      # テスト
│   ├── components/
│   └── pages/
└── package.json
```

---

## 6. テストコード規約

### 6.1 テストファイル命名

| 対象 | テストファイル名 | 配置 |
|------|---------------|------|
| サービスクラス | `impact-analyzer.test.ts` | `tests/unit/services/` |
| APIエンドポイント | `rfc.integration.test.ts` | `tests/integration/api/` |
| Reactコンポーネント | `RFCCreate.test.tsx` | `tests/components/` |

### 6.2 テスト構造

```typescript
describe('ImpactAnalyzer', () => {
  describe('analyze', () => {
    it('ActiveDirectoryの変更で依存システムを検出すること', async () => {
      // Arrange
      const rfc = createTestRfc({ targetSystems: ['ActiveDirectory'] });

      // Act
      const result = await analyzer.analyze(rfc);

      // Assert
      expect(result.affectedSystems).toContain('EntraID');
      expect(result.affectedSystems).toContain('HENGEONE');
    });

    it('コアシステム変更でリスクレベルがhigh以上になること', async () => {
      // Arrange
      const rfc = createTestRfc({
        targetSystems: ['ActiveDirectory'],
        changeType: 'major',
      });

      // Act
      const result = await analyzer.analyze(rfc);

      // Assert
      expect(['high', 'critical']).toContain(result.riskLevel);
    });
  });
});
```

---

## 7. コメント・ドキュメント規約

### 7.1 コメントルール

| ルール | 説明 |
|-------|------|
| JSDoc | 公開API・サービスクラスのメソッドに記載 |
| なぜ（Why） | コードの意図・理由を記載（何をしているかはコードで表現） |
| TODO | `// TODO: <説明>` 形式で記載、Issue番号を付与推奨 |
| 日本語コメント | ビジネスロジックの説明は日本語で記載可 |

### 7.2 JSDoc例

```typescript
/**
 * 変更申請（RFC）の影響分析を実行する
 *
 * @param rfc - 分析対象のRFC
 * @returns 影響分析結果（影響システム、リスクレベル、推奨事項）
 * @throws {ValidationError} RFCの対象システムが未指定の場合
 */
async analyze(rfc: ChangeRequest): Promise<ImpactAnalysisResult> {
  // ...
}
```

---

## 8. Git コミットメッセージ規約

### 8.1 Conventional Commits

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 8.2 Type一覧

| Type | 説明 | 例 |
|------|------|-----|
| feat | 新機能追加 | `feat(rfc): RFC起票フォームバリデーション追加` |
| fix | バグ修正 | `fix(cab): 承認数カウントの不具合を修正` |
| docs | ドキュメント | `docs: テスト計画書を追加` |
| style | フォーマット変更 | `style: Prettier適用` |
| refactor | リファクタリング | `refactor(services): ImpactAnalyzerのメソッド分割` |
| test | テスト追加・修正 | `test(rfc): RFC作成APIの結合テスト追加` |
| chore | その他 | `chore: 依存パッケージ更新` |
| perf | 性能改善 | `perf(calendar): カレンダークエリの最適化` |
| ci | CI/CD設定 | `ci: E2Eテストのワークフロー追加` |

---

*文書管理：本文書はバージョン管理対象。変更時はバージョン番号を更新すること。*
