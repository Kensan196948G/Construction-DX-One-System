# OWASP Top 10 (2021) セキュリティチェックリスト

Construction-GRC-System における OWASP Top 10 対応状況。

## チェックリスト

| # | OWASP ID | カテゴリ | 対応状況 | 実装内容 |
|---|----------|---------|---------|---------|
| 1 | A01 | Broken Access Control | 対応済 | JWT 認証必須 (IsAuthenticated), エンドポイント単位の権限制御, Django admin ログイン必須 |
| 2 | A02 | Cryptographic Failures | 対応済 | PBKDF2 パスワードハッシュ (Django デフォルト), SECRET_KEY 環境変数化, HTTPS 前提設計 |
| 3 | A03 | Injection | 対応済 | Django ORM によるパラメータ化クエリ, DRF シリアライザによる入力バリデーション |
| 4 | A04 | Insecure Design | 一部対応 | セキュリティ設計ドキュメント整備済, 脅威モデリングは今後実施予定 |
| 5 | A05 | Security Misconfiguration | 対応済 | SecurityHeadersMiddleware (CSP, X-Frame-Options 等), DEBUG=False (本番), CORS 制限 |
| 6 | A06 | Vulnerable and Outdated Components | 対応済 | CI で pip-audit / npm audit 実行, Bandit による静的解析 |
| 7 | A07 | Identification and Authentication Failures | 対応済 | JWT トークン有効期限 1 時間, リフレッシュトークンローテーション, パスワードバリデータ 4 種 |
| 8 | A08 | Software and Data Integrity Failures | 一部対応 | CI/CD パイプラインによるビルド検証, 署名付きコンテナイメージは今後対応 |
| 9 | A09 | Security Logging and Monitoring Failures | 対応済 | AuditLogMiddleware による監査ログ, RequestLoggingMiddleware によるリクエスト記録 |
| 10 | A10 | Server-Side Request Forgery (SSRF) | 低リスク | 外部 URL 取得機能なし, 将来の機能追加時に対策予定 |

## テスト

セキュリティテストは `backend/tests/test_security.py` に実装。

```bash
cd backend && python -m pytest tests/test_security.py -v
```

## 静的解析

Bandit によるセキュリティスキャン。

```bash
cd backend && bandit -r apps/ grc/ -c .bandit
```

## CI 統合

GitHub Actions (`claudeos-ci.yml`) の security ジョブで以下を自動実行:

- pip-audit: Python 依存パッケージの脆弱性チェック
- npm audit: フロントエンド依存パッケージの脆弱性チェック
- Bandit: Python コードの静的セキュリティ解析

## 参考

- [OWASP Top 10 (2021)](https://owasp.org/www-project-top-ten/)
- [Django Security](https://docs.djangoproject.com/en/5.0/topics/security/)
- [DRF Authentication](https://www.django-rest-framework.org/api-guide/authentication/)
