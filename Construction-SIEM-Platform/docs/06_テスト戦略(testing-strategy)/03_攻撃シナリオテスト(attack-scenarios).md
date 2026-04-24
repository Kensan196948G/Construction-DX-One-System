# 🎯 攻撃シナリオテスト（Attack Scenarios）

> 建設業界向け SIEM の10攻撃シナリオによる検知能力テスト

---

## 📋 シナリオ一覧

| # | シナリオ | MITRE ATT&CK | 重要度 | 検知ソース |
|:-:|---------|:------------:|:------:|-----------|
| 1 | 🔒 ランサムウェア | T1486 | Critical | Endpoint |
| 2 | 🔑 ブルートフォース | T1110 | High | IDS/Firewall |
| 3 | 🔀 横展開 | T1021 | Critical | Network |
| 4 | 📤 データ窃取 | T1041 | Critical | Firewall/DLP |
| 5 | 🔍 ポートスキャン | T1046 | Medium | Firewall |
| 6 | 📡 IoTファームウェア改ざん | - | Critical | IoT |
| 7 | 📐 CAD大量エクスポート | T1567 | High | DLP/Endpoint |
| 8 | 💾 シャドーコピー削除 | T1490 | Critical | Endpoint |
| 9 | ⚡ 不正プロセス実行 | T1059 | High | Endpoint |
| 10 | 👑 権限昇格 | T1068 | Critical | Endpoint/AD |

---

## 1️⃣ ランサムウェア（Ransomware）

### 概要

| 項目 | 値 |
|------|------|
| MITRE ATT&CK | **T1486** - Data Encrypted for Impact |
| タクティック | Impact |
| 重要度 | 🔴 Critical |
| 対象 | 建設管理端末、ファイルサーバー |

### 攻撃シナリオ

```
1. フィッシングメールから初期アクセス
2. マルウェアダウンロード・実行
3. ファイル暗号化開始（.encrypted 拡張子）
4. 身代金要求メモ作成
5. シャドーコピー削除（T1490 との複合）
```

### 検知ポイント

| # | 検知内容 | ソース | 検知ルール |
|:-:|---------|--------|-----------|
| 1 | 短時間での大量ファイル変更 | Endpoint | ファイル変更率 > 100件/分 |
| 2 | 暗号化拡張子の出現 | Endpoint | `.encrypted`, `.locked`, `.crypt` |
| 3 | 身代金要求ファイル検出 | Endpoint | `README_DECRYPT.*`, `HOW_TO_RECOVER.*` |
| 4 | C2通信 | Firewall | 既知C2サーバーへの通信 |

### テスト手順

```python
async def test_ransomware_detection():
    """ランサムウェア攻撃パターンの検知テスト"""
    # ファイル暗号化パターンのアラート生成
    alert = {
        "title": "大量ファイル暗号化検出",
        "severity": "critical",
        "source": "endpoint",
        "mitre_technique": "T1486",
        "description": "PC-A01で150件/分のファイル名変更を検出。.encrypted拡張子。"
    }
    response = await client.post("/api/v1/alerts/ingest", json=alert)
    assert response.status_code == 201

    # 相関分析でキルチェーン検出
    correlation = await client.post("/api/v1/correlation/analyze", json={
        "alert_ids": [alert_id],
        "analysis_type": "kill_chain"
    })
    assert correlation.json()["data"]["kill_chain"]["impact"]["detected"] is True
```

### 期待される応答

| 対応 | SLA | 説明 |
|------|-----|------|
| 🚨 P1 インシデント自動作成 | 15分 | 即座に対応開始 |
| 🔔 Teams/Slack 通知 | 即座 | セキュリティチームに通知 |
| 🔒 ネットワーク隔離推奨 | 5分以内 | 感染拡大防止 |

---

## 2️⃣ ブルートフォース（Brute Force）

### 概要

| 項目 | 値 |
|------|------|
| MITRE ATT&CK | **T1110** - Brute Force |
| タクティック | Credential Access |
| 重要度 | 🟠 High |
| 対象 | SSH, RDP, Web ログイン |

### 攻撃シナリオ

```
1. 外部IPからSSHへのログイン試行
2. 辞書攻撃パターン（50回/分以上）
3. 異なるユーザー名で繰り返し試行
4. 成功した場合、不正アクセス開始
```

### 検知ポイント

| # | 検知内容 | ソース | 検知ルール |
|:-:|---------|--------|-----------|
| 1 | ログイン失敗の異常増加 | IDS | 失敗 > 10回/分/IP |
| 2 | 複数ユーザーへの試行 | AD | 異なるユーザー > 5種 |
| 3 | 既知の攻撃ツールシグネチャ | IDS | Hydra, Medusa パターン |
| 4 | 成功後の異常行動 | Endpoint | 非業務時間のログイン |

### テスト手順

```python
async def test_bruteforce_detection():
    """ブルートフォース攻撃パターンの検知テスト"""
    alerts = []
    for i in range(50):
        alert = {
            "title": f"SSH認証失敗 ({i+1}回目)",
            "severity": "high",
            "source": "ids",
            "mitre_technique": "T1110",
            "source_ip": "203.0.113.50",
            "description": f"SSH認証失敗: user{i}@target-server"
        }
        alerts.append(alert)

    response = await client.post("/api/v1/data/batch-ingest", json={
        "data_type": "alerts",
        "records": alerts
    })
    assert response.status_code == 202
```

---

## 3️⃣ 横展開（Lateral Movement）

### 概要

| 項目 | 値 |
|------|------|
| MITRE ATT&CK | **T1021** - Remote Services |
| タクティック | Lateral Movement |
| 重要度 | 🔴 Critical |
| 対象 | 内部ネットワーク、RDP/SMB |

### 攻撃シナリオ

```
1. 初期侵入端末から内部スキャン
2. 管理者資格情報の窃取
3. RDP/SMB を使った他端末へのアクセス
4. 建設管理サーバーへの到達
```

### 検知ポイント

| # | 検知内容 | ソース | 検知ルール |
|:-:|---------|--------|-----------|
| 1 | 内部からの異常なRDP接続 | Network | 通常パターンからの逸脱 |
| 2 | SMB共有への不正アクセス | Network | 非業務ファイルへのアクセス |
| 3 | Pass-the-Hash パターン | AD | 異常な認証イベント |
| 4 | 新規サービス作成 | Endpoint | PsExec, WMI 使用 |

---

## 4️⃣ データ窃取（Data Exfiltration）

### 概要

| 項目 | 値 |
|------|------|
| MITRE ATT&CK | **T1041** - Exfiltration Over C2 Channel |
| タクティック | Exfiltration |
| 重要度 | 🔴 Critical |
| 対象 | 設計図面、建設データ |

### 攻撃シナリオ

```
1. 機密ファイル（CADデータ、設計図面）の収集
2. ファイルの圧縮・暗号化
3. C2チャネル経由での外部送信
4. DNS トンネリングまたはHTTPS経由
```

### 検知ポイント

| # | 検知内容 | ソース | 検知ルール |
|:-:|---------|--------|-----------|
| 1 | 大量データの外部転送 | Firewall | アップロード > 100MB/h |
| 2 | DNSトンネリング | DNS | 異常なDNSクエリ長 |
| 3 | 非業務時間のデータアクセス | DLP | 深夜のファイルアクセス |
| 4 | 機密ファイルへの一括アクセス | DLP | 短時間での大量アクセス |

---

## 5️⃣ ポートスキャン（Port Scanning）

### 概要

| 項目 | 値 |
|------|------|
| MITRE ATT&CK | **T1046** - Network Service Scanning |
| タクティック | Discovery |
| 重要度 | 🟡 Medium |
| 対象 | ネットワーク全体 |

### 攻撃シナリオ

```
1. 外部または内部IPからのポートスキャン
2. SYN スキャン（ステルススキャン）
3. サービスバージョン特定
4. 脆弱なサービスの発見
```

### 検知ポイント

| # | 検知内容 | ソース | 検知ルール |
|:-:|---------|--------|-----------|
| 1 | 同一IPからの多数ポートアクセス | Firewall | > 20ポート/分 |
| 2 | SYN パケットの急増 | IDS | SYN フラグのみパケット |
| 3 | 連続ポート番号へのアクセス | Firewall | シーケンシャルスキャン |
| 4 | 既知スキャンツールのシグネチャ | IDS | Nmap パターン |

---

## 6️⃣ IoTファームウェア改ざん

### 概要

| 項目 | 値 |
|------|------|
| MITRE ATT&CK | カスタム（ICSに近い） |
| タクティック | Persistence / Impact |
| 重要度 | 🔴 Critical |
| 対象 | 建設現場IoTデバイス（センサー、カメラ） |

### 攻撃シナリオ

```
1. IoTデバイスの脆弱な管理画面にアクセス
2. デフォルト認証情報でログイン
3. 悪意のあるファームウェアをアップロード
4. デバイスの制御奪取
5. 偽センサーデータの送信
```

### 検知ポイント

| # | 検知内容 | ソース | 検知ルール |
|:-:|---------|--------|-----------|
| 1 | ファームウェア更新イベント | IoT | 予定外の更新 |
| 2 | デバイスからの異常な通信先 | Firewall | 未知IPへの通信 |
| 3 | センサーデータの異常値 | IoT | 通常範囲からの逸脱 |
| 4 | デフォルト認証情報の使用 | IoT | admin/admin等 |

---

## 7️⃣ CAD大量エクスポート（Mass CAD Export）

### 概要

| 項目 | 値 |
|------|------|
| MITRE ATT&CK | **T1567** - Exfiltration Over Web Service |
| タクティック | Exfiltration |
| 重要度 | 🟠 High |
| 対象 | CADファイル、設計図面 |

### 攻撃シナリオ

```
1. 正規ユーザーアカウントの不正利用
2. CADファイルの一括ダウンロード
3. クラウドストレージへのアップロード
4. 知的財産の流出
```

### 検知ポイント

| # | 検知内容 | ソース | 検知ルール |
|:-:|---------|--------|-----------|
| 1 | CADファイルの大量アクセス | DLP | > 50ファイル/時間 |
| 2 | クラウドストレージへの送信 | Firewall | Dropbox, Google Drive等 |
| 3 | USB大容量デバイスの接続 | Endpoint | USB書き込み検出 |
| 4 | 非業務時間のファイルアクセス | DLP | 営業時間外の操作 |

---

## 8️⃣ シャドーコピー削除（Shadow Copy Deletion）

### 概要

| 項目 | 値 |
|------|------|
| MITRE ATT&CK | **T1490** - Inhibit System Recovery |
| タクティック | Impact |
| 重要度 | 🔴 Critical |
| 対象 | Windowsサーバー |

### 攻撃シナリオ

```
1. 管理者権限の取得
2. vssadmin delete shadows /all コマンド実行
3. バックアップカタログの削除
4. ランサムウェア実行の前段階
```

### 検知ポイント

| # | 検知内容 | ソース | 検知ルール |
|:-:|---------|--------|-----------|
| 1 | vssadmin コマンド実行 | Endpoint | プロセス監視 |
| 2 | wmic shadowcopy delete | Endpoint | WMI コマンド監視 |
| 3 | bcdedit /set {default} recoveryenabled no | Endpoint | ブート設定変更 |
| 4 | バックアップサービス停止 | Endpoint | サービス停止イベント |

---

## 9️⃣ 不正プロセス実行（Unauthorized Process Execution）

### 概要

| 項目 | 値 |
|------|------|
| MITRE ATT&CK | **T1059** - Command and Scripting Interpreter |
| タクティック | Execution |
| 重要度 | 🟠 High |
| 対象 | 建設現場端末 |

### 攻撃シナリオ

```
1. PowerShell の不正実行
2. エンコードされたコマンドの実行
3. スクリプトベースのマルウェアダウンロード
4. メモリ上での実行（ファイルレス攻撃）
```

### 検知ポイント

| # | 検知内容 | ソース | 検知ルール |
|:-:|---------|--------|-----------|
| 1 | PowerShell -EncodedCommand | Endpoint | Base64エンコードコマンド |
| 2 | cmd.exe からの不審な子プロセス | Endpoint | プロセスツリー異常 |
| 3 | certutil -urlcache | Endpoint | ファイルダウンロード用途 |
| 4 | mshta, wscript の実行 | Endpoint | スクリプトエンジン監視 |

---

## 🔟 権限昇格（Privilege Escalation）

### 概要

| 項目 | 値 |
|------|------|
| MITRE ATT&CK | **T1068** - Exploitation for Privilege Escalation |
| タクティック | Privilege Escalation |
| 重要度 | 🔴 Critical |
| 対象 | Windows/Linux サーバー、Active Directory |

### 攻撃シナリオ

```
1. 一般ユーザーアカウントで初期アクセス
2. ローカル脆弱性の悪用
3. 管理者権限への昇格
4. ドメイン管理者への昇格（Golden Ticket等）
```

### 検知ポイント

| # | 検知内容 | ソース | 検知ルール |
|:-:|---------|--------|-----------|
| 1 | 特権グループへのユーザー追加 | AD | グループメンバーシップ変更 |
| 2 | 異常なトークン操作 | Endpoint | SeDebugPrivilege 使用 |
| 3 | Kerberos チケット異常 | AD | Golden/Silver Ticket検出 |
| 4 | sudo/su の異常使用 | Linux | 非許可ユーザーの特権使用 |

---

## 📊 シナリオテスト結果サマリーテンプレート

| # | シナリオ | 検知 | アラート生成 | インシデント作成 | 通知 | 相関分析 |
|:-:|---------|:----:|:----------:|:--------------:|:----:|:-------:|
| 1 | ランサムウェア | ✅ | ✅ | ✅ | ✅ | ✅ |
| 2 | ブルートフォース | ✅ | ✅ | ✅ | ✅ | ✅ |
| 3 | 横展開 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 4 | データ窃取 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 5 | ポートスキャン | ✅ | ✅ | ✅ | ✅ | ✅ |
| 6 | IoT改ざん | ✅ | ✅ | ✅ | ✅ | ✅ |
| 7 | CADエクスポート | ✅ | ✅ | ✅ | ✅ | ✅ |
| 8 | シャドーコピー削除 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 9 | 不正プロセス | ✅ | ✅ | ✅ | ✅ | ✅ |
| 10 | 権限昇格 | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## 🔗 MITRE ATT&CK マッピング

### キルチェーンカバレッジ

| フェーズ | テクニック | シナリオ |
|---------|-----------|---------|
| 🔍 Reconnaissance | - | (外部偵察は対象外) |
| 📧 Initial Access | フィッシング | #1, #6 |
| ⚡ Execution | T1059 | #9 |
| 🔒 Persistence | ファームウェア改ざん | #6 |
| 👑 Privilege Escalation | T1068 | #10 |
| 🔑 Credential Access | T1110 | #2 |
| 🔍 Discovery | T1046 | #5 |
| 🔀 Lateral Movement | T1021 | #3 |
| 📤 Exfiltration | T1041, T1567 | #4, #7 |
| 💥 Impact | T1486, T1490 | #1, #8 |
