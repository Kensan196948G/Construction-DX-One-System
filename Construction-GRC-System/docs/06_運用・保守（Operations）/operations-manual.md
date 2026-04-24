# 運用マニュアル -- Construction-GRC-System

## 目次
1. システム概要
2. 日常運用
3. 監視・アラート
4. バックアップ・リストア
5. トラブルシューティング
6. セキュリティ運用

## 1. システム概要
| コンポーネント | 技術 | ポート | ヘルスチェック |
|---|---|---|---|
| Frontend | Nginx + Vue.js | 80 | HTTP GET / |
| Backend | Gunicorn + Django | 8000 | GET /api/health/ |
| Database | PostgreSQL 16 | 5432 | pg_isready |
| Cache | Redis 7 | 6379 | redis-cli ping |
| Worker | Celery | -- | celery inspect ping |
| Scheduler | Celery Beat | -- | -- |

## 2. 日常運用
### ヘルスチェック
GET /api/health/ → DB・Redis接続確認

### Celeryタスク確認
| タスク | スケジュール | 内容 |
|---|---|---|
| check_assessment_deadlines | 毎日 09:00 | 評価期限チェック |
| generate_compliance_report | 毎月1日 | 準拠率レポート生成 |
| check_control_reviews | 毎日 08:00 | 管理策レビュー期限 |
| calculate_soa_status | 毎週月曜 | SoA集計 |
| check_review_deadlines | 毎日 07:00 | リスクレビュー期限 |
| generate_risk_summary | 毎週金曜 | リスクサマリー生成 |

### ログ確認
```bash
docker compose logs -f backend
docker compose logs -f celery
```

## 3. 監視・アラート
### 推奨監視項目
| 項目 | 閾値 | アクション |
|---|---|---|
| API応答時間 | >2秒 | 調査 |
| エラー率 | >1% | アラート |
| DB接続数 | >80% | スケーリング |
| Redis メモリ | >80% | 調査 |
| ディスク使用率 | >85% | 拡張 |

## 4. バックアップ・リストア
### PostgreSQL バックアップ
```bash
pg_dump -h localhost -U grc_admin grc_db > backup_$(date +%Y%m%d).sql
```

### リストア
```bash
psql -h localhost -U grc_admin grc_db < backup_20260401.sql
```

## 5. トラブルシューティング
| 症状 | 原因 | 対処 |
|---|---|---|
| 502 Bad Gateway | Backend停止 | docker compose restart backend |
| DB接続エラー | PostgreSQL停止 | docker compose restart db |
| Celeryタスク未実行 | Worker停止 | docker compose restart celery |
| ログイン不可 | JWT設定 | SECRET_KEY確認 |

## 6. セキュリティ運用
- JWT トークン: 1時間有効、7日リフレッシュ
- パスワード: Django validators (最低8文字、一般的なパスワード拒否)
- RBAC: 6ロール (grc_admin/risk_owner/compliance_officer/auditor/executive/general)
- CORS: 本番は CORS_ALLOWED_ORIGINS で制限
