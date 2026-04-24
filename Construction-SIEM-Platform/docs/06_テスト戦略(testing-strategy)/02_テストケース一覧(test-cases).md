# 📋 テストケース一覧（Test Cases）

> 全210テストの分類と詳細

---

## 📊 テスト分布サマリー

| テストファイル | テスト数 | カテゴリ |
|---------------|:-------:|---------|
| 🌐 test_api.py | 22 | API基本+統合 |
| 🔐 test_auth.py | 15 | JWT認証・RBAC |
| 📊 test_kpi.py | 18 | KPI計算・監査ログ・Kafka |
| 🛡 test_threat_intel.py | 16 | 脅威インテリジェンス |
| 🔔 test_notifications.py | 11 | 通知・ヘルスチェック |
| ⏱ test_rate_limit.py | 6 | レート制限 |
| ✅ test_data_validation.py | 11 | データ検証 |
| 📈 test_metrics.py | 9 | メトリクス |
| 📜 test_compliance.py | 9 | コンプライアンス |
| 🔗 test_correlation.py | 9 | 相関分析 |
| 🔍 test_es_client.py | 7 | ESクライアント |
| 🔍 test_elasticsearch.py | - | ES統合 |
| 🌐 test_integration.py | - | E2E統合 |
| 📏 test_sigma_rules.py | - | Sigma/MLルール |
| | **合計 210** | |

---

## 1️⃣ test_api.py — API基本+統合テスト（22件）

> API エンドポイントの基本動作と統合テスト

| # | テスト名 | 説明 | 種別 |
|:-:|---------|------|:----:|
| 1 | `test_health_check` | ヘルスチェックエンドポイント正常応答 | ユニット |
| 2 | `test_root_endpoint` | ルートエンドポイント応答 | ユニット |
| 3 | `test_get_alerts_list` | アラート一覧取得 | 統合 |
| 4 | `test_get_alerts_with_pagination` | ページネーション動作 | 統合 |
| 5 | `test_get_alerts_filter_severity` | severity フィルター | 統合 |
| 6 | `test_get_alerts_filter_acknowledged` | acknowledged フィルター | 統合 |
| 7 | `test_get_alert_detail` | アラート詳細取得 | 統合 |
| 8 | `test_get_alert_not_found` | 存在しないアラートで404 | ユニット |
| 9 | `test_acknowledge_alert` | アラート承認 | 統合 |
| 10 | `test_alerts_summary_by_severity` | 重要度別サマリー | 統合 |
| 11 | `test_ingest_alert` | アラートインジェスト | 統合 |
| 12 | `test_ingest_alert_validation_error` | インジェストバリデーションエラー | ユニット |
| 13 | `test_get_incidents_list` | インシデント一覧取得 | 統合 |
| 14 | `test_create_incident` | インシデント作成 | 統合 |
| 15 | `test_get_incident_detail` | インシデント詳細取得 | 統合 |
| 16 | `test_update_incident_status` | インシデントステータス更新 | 統合 |
| 17 | `test_incident_stats_summary` | インシデント統計 | 統合 |
| 18 | `test_invalid_status_transition` | 無効なステータス遷移で400 | ユニット |
| 19 | `test_openapi_schema` | OpenAPI スキーマ取得 | ユニット |
| 20 | `test_swagger_ui` | Swagger UI 応答 | ユニット |
| 21 | `test_cors_headers` | CORS ヘッダー | ユニット |
| 22 | `test_request_id_header` | リクエストID付与 | ユニット |

---

## 2️⃣ test_auth.py — JWT認証・RBAC（15件）

> 認証・認可の網羅的テスト

| # | テスト名 | 説明 | 種別 |
|:-:|---------|------|:----:|
| 1 | `test_token_generation` | 正常なトークン発行 | ユニット |
| 2 | `test_token_with_invalid_credentials` | 不正な認証情報で401 | ユニット |
| 3 | `test_token_expiration` | トークン有効期限検証 | ユニット |
| 4 | `test_token_payload_structure` | JWTペイロード構造確認 | ユニット |
| 5 | `test_get_current_user` | /auth/me 正常応答 | 統合 |
| 6 | `test_get_current_user_without_token` | トークンなしで401 | ユニット |
| 7 | `test_get_current_user_with_expired_token` | 期限切れトークンで401 | ユニット |
| 8 | `test_get_current_user_with_invalid_token` | 不正トークンで401 | ユニット |
| 9 | `test_admin_role_access` | admin ロールのアクセス権 | 統合 |
| 10 | `test_analyst_role_access` | analyst ロールのアクセス権 | 統合 |
| 11 | `test_viewer_role_access` | viewer ロールのアクセス権 | 統合 |
| 12 | `test_viewer_cannot_acknowledge` | viewer が承認不可 | ユニット |
| 13 | `test_viewer_cannot_create_incident` | viewer がインシデント作成不可 | ユニット |
| 14 | `test_roles_endpoint_admin_only` | /auth/roles は admin のみ | 統合 |
| 15 | `test_roles_endpoint_forbidden_for_analyst` | analyst は /auth/roles にアクセス不可 | ユニット |

---

## 3️⃣ test_kpi.py — KPI計算・監査ログ・Kafka（18件）

> KPI指標の計算精度と監査ログ・メッセージキューのテスト

| # | テスト名 | 説明 | 種別 |
|:-:|---------|------|:----:|
| 1 | `test_mttd_calculation` | MTTD 平均計算 | ユニット |
| 2 | `test_mttd_with_no_data` | データなし時のMTTD | ユニット |
| 3 | `test_mttr_calculation` | MTTR 平均計算 | ユニット |
| 4 | `test_mttr_with_no_data` | データなし時のMTTR | ユニット |
| 5 | `test_sla_compliance_rate` | SLA遵守率計算 | ユニット |
| 6 | `test_sla_p1_deadline` | P1 SLA 15分期限 | ユニット |
| 7 | `test_sla_p2_deadline` | P2 SLA 30分期限 | ユニット |
| 8 | `test_sla_p3_deadline` | P3 SLA 2時間期限 | ユニット |
| 9 | `test_sla_p4_deadline` | P4 SLA 8時間期限 | ユニット |
| 10 | `test_kpi_dashboard_endpoint` | KPIダッシュボードAPI | 統合 |
| 11 | `test_kpi_trend_calculation` | トレンド計算 | ユニット |
| 12 | `test_audit_log_creation` | 監査ログ作成 | ユニット |
| 13 | `test_audit_log_query` | 監査ログ検索 | 統合 |
| 14 | `test_audit_log_user_filter` | ユーザーフィルター | ユニット |
| 15 | `test_audit_stats` | 監査統計 | 統合 |
| 16 | `test_kafka_produce_alert` | Kafkaへのアラート送信 | ユニット |
| 17 | `test_kafka_consume_alert` | Kafkaからのアラート受信 | ユニット |
| 18 | `test_kafka_connection_error` | Kafka接続エラーハンドリング | ユニット |

---

## 4️⃣ test_threat_intel.py — 脅威インテリジェンス（16件）

> IoC管理・照合・フィードのテスト

| # | テスト名 | 説明 | 種別 |
|:-:|---------|------|:----:|
| 1 | `test_create_ioc_ip` | IP型IoC登録 | ユニット |
| 2 | `test_create_ioc_domain` | ドメイン型IoC登録 | ユニット |
| 3 | `test_create_ioc_hash` | ハッシュ型IoC登録 | ユニット |
| 4 | `test_create_ioc_url` | URL型IoC登録 | ユニット |
| 5 | `test_create_ioc_invalid_type` | 不正なIoC型で422 | ユニット |
| 6 | `test_list_iocs` | IoC一覧取得 | 統合 |
| 7 | `test_list_iocs_filter_type` | タイプ別フィルター | 統合 |
| 8 | `test_match_single_ioc` | 単一IoC照合（一致） | ユニット |
| 9 | `test_match_no_match` | IoC照合（不一致） | ユニット |
| 10 | `test_match_multiple_iocs` | 複数IoC一括照合 | ユニット |
| 11 | `test_match_with_confidence` | 信頼度スコア検証 | ユニット |
| 12 | `test_ioc_expiry` | IoC有効期限検証 | ユニット |
| 13 | `test_feed_list` | フィード一覧取得 | 統合 |
| 14 | `test_feed_update` | フィード更新 | 統合 |
| 15 | `test_ioc_duplicate_check` | 重複IoC検出 | ユニット |
| 16 | `test_ioc_bulk_import` | バルクインポート | 統合 |

---

## 5️⃣ test_notifications.py — 通知・ヘルスチェック（11件）

> 通知送信とシステムヘルスチェックのテスト

| # | テスト名 | 説明 | 種別 |
|:-:|---------|------|:----:|
| 1 | `test_send_teams_notification` | Teams通知送信 | ユニット |
| 2 | `test_send_slack_notification` | Slack通知送信 | ユニット |
| 3 | `test_send_webhook_notification` | Webhook通知送信 | ユニット |
| 4 | `test_send_multi_channel` | 複数チャネル同時送信 | ユニット |
| 5 | `test_notification_failure_handling` | 送信失敗時のエラーハンドリング | ユニット |
| 6 | `test_notification_with_mention` | メンション付き通知 | ユニット |
| 7 | `test_notification_priority_formatting` | 優先度別フォーマット | ユニット |
| 8 | `test_channels_list` | チャネル一覧取得 | 統合 |
| 9 | `test_health_check_all_healthy` | 全サービス正常 | 統合 |
| 10 | `test_health_check_es_down` | ES障害時のヘルスチェック | ユニット |
| 11 | `test_health_check_kafka_down` | Kafka障害時のヘルスチェック | ユニット |

---

## 6️⃣ test_rate_limit.py — レート制限（6件）

| # | テスト名 | 説明 | 種別 |
|:-:|---------|------|:----:|
| 1 | `test_rate_limit_headers` | レート制限ヘッダー付与 | ユニット |
| 2 | `test_rate_limit_not_exceeded` | 制限内リクエスト正常応答 | ユニット |
| 3 | `test_rate_limit_exceeded` | 100req/min 超過で429 | ユニット |
| 4 | `test_rate_limit_reset` | 制限リセット | ユニット |
| 5 | `test_rate_limit_per_ip` | IPアドレスベース制限 | ユニット |
| 6 | `test_login_rate_limit` | ログイン試行5回/分 | ユニット |

---

## 7️⃣ test_data_validation.py — データ検証（11件）

| # | テスト名 | 説明 | 種別 |
|:-:|---------|------|:----:|
| 1 | `test_validate_syslog` | syslog データバリデーション | ユニット |
| 2 | `test_validate_json_log` | JSONログバリデーション | ユニット |
| 3 | `test_validate_invalid_format` | 不正フォーマット検出 | ユニット |
| 4 | `test_validate_missing_fields` | 必須フィールド欠落検出 | ユニット |
| 5 | `test_validate_timestamp_format` | タイムスタンプ形式検証 | ユニット |
| 6 | `test_validate_ip_address` | IPアドレス形式検証 | ユニット |
| 7 | `test_batch_ingest_success` | バッチインジェスト成功 | 統合 |
| 8 | `test_batch_ingest_partial_failure` | 一部レコード失敗 | ユニット |
| 9 | `test_batch_ingest_all_invalid` | 全レコード不正 | ユニット |
| 10 | `test_batch_size_limit` | バッチサイズ上限 | ユニット |
| 11 | `test_data_type_validation` | データ型バリデーション | ユニット |

---

## 8️⃣ test_metrics.py — メトリクス（9件）

| # | テスト名 | 説明 | 種別 |
|:-:|---------|------|:----:|
| 1 | `test_prometheus_metrics_endpoint` | /metrics エンドポイント | 統合 |
| 2 | `test_request_count_metric` | リクエストカウント | ユニット |
| 3 | `test_request_duration_metric` | リクエスト処理時間 | ユニット |
| 4 | `test_alert_count_metric` | アラート数メトリクス | ユニット |
| 5 | `test_incident_count_metric` | インシデント数メトリクス | ユニット |
| 6 | `test_error_rate_metric` | エラーレートメトリクス | ユニット |
| 7 | `test_metric_labels` | メトリクスラベル確認 | ユニット |
| 8 | `test_histogram_buckets` | ヒストグラムバケット | ユニット |
| 9 | `test_metrics_disabled` | メトリクス無効化 | ユニット |

---

## 9️⃣ test_compliance.py — コンプライアンス（9件）

| # | テスト名 | 説明 | 種別 |
|:-:|---------|------|:----:|
| 1 | `test_iso27001_full_check` | ISO27001 フルチェック | 統合 |
| 2 | `test_nist_csf_full_check` | NIST CSF フルチェック | 統合 |
| 3 | `test_compliance_score_calculation` | スコア計算 | ユニット |
| 4 | `test_compliance_pass_threshold` | 合格閾値判定 | ユニット |
| 5 | `test_compliance_warning_threshold` | 警告閾値判定 | ユニット |
| 6 | `test_compliance_fail_threshold` | 不合格閾値判定 | ユニット |
| 7 | `test_compliance_report_generation` | レポート生成 | 統合 |
| 8 | `test_compliance_recommendations` | 推奨事項生成 | ユニット |
| 9 | `test_compliance_admin_only` | admin限定アクセス | ユニット |

---

## 🔟 test_correlation.py — 相関分析（9件）

| # | テスト名 | 説明 | 種別 |
|:-:|---------|------|:----:|
| 1 | `test_kill_chain_analysis` | キルチェーン分析 | ユニット |
| 2 | `test_kill_chain_partial_match` | 部分一致シナリオ | ユニット |
| 3 | `test_kill_chain_no_match` | 一致なしシナリオ | ユニット |
| 4 | `test_risk_score_calculation` | リスクスコア計算 | ユニット |
| 5 | `test_risk_level_assignment` | リスクレベル判定 | ユニット |
| 6 | `test_correlation_time_window` | 時間窓フィルター | ユニット |
| 7 | `test_correlation_recommendations` | 推奨事項生成 | ユニット |
| 8 | `test_correlation_rules_list` | ルール一覧取得 | 統合 |
| 9 | `test_correlation_analyze_endpoint` | 分析エンドポイント | 統合 |

---

## 1️⃣1️⃣ test_es_client.py — Elasticsearch クライアント（7件）

| # | テスト名 | 説明 | 種別 |
|:-:|---------|------|:----:|
| 1 | `test_es_connection` | ES接続確認 | ユニット |
| 2 | `test_es_index_creation` | インデックス作成 | ユニット |
| 3 | `test_es_document_index` | ドキュメント登録 | ユニット |
| 4 | `test_es_document_search` | ドキュメント検索 | ユニット |
| 5 | `test_es_document_update` | ドキュメント更新 | ユニット |
| 6 | `test_es_connection_error` | 接続エラーハンドリング | ユニット |
| 7 | `test_es_bulk_operation` | バルク操作 | ユニット |

---

## 1️⃣2️⃣ その他のテストファイル

### test_elasticsearch.py — Elasticsearch統合テスト

実際のElasticsearchインスタンスに対する統合テスト。Docker環境で実行。

### test_integration.py — E2E統合テスト

アラート検出からインシデント作成・通知までのエンドツーエンドシナリオテスト。

### test_sigma_rules.py — Sigma/MLルール

Sigmaルールのパース・マッチング、機械学習ベースの異常検知ルールのテスト。

---

## 📊 カテゴリ別カバレッジ

| カテゴリ | テスト数 | カバレッジ目安 |
|---------|:-------:|:------------:|
| 🌐 API | 22 | 90% |
| 🔐 認証 | 15 | 92% |
| 📊 KPI | 18 | 85% |
| 🛡 脅威インテリジェンス | 16 | 88% |
| 🔔 通知 | 11 | 80% |
| ⏱ レート制限 | 6 | 95% |
| ✅ データ検証 | 11 | 82% |
| 📈 メトリクス | 9 | 78% |
| 📜 コンプライアンス | 9 | 80% |
| 🔗 相関分析 | 9 | 75% |
| 🔍 ES | 7 | 70% |
