# 詳細設計仕様書（Detailed Design Specification）

## 建設業 統合リスク＆コンプライアンス管理システム（Construction-GRC-System）

| 項目 | 内容 |
|------|------|
| **文書番号** | DES-GRC-002 |
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

1. [設計方針](#1-設計方針)
2. [accounts アプリ（ユーザー認証・認可）](#2-accounts-アプリユーザー認証認可)
3. [risks アプリ（リスク管理）](#3-risks-アプリリスク管理)
4. [compliance アプリ（コンプライアンス管理）](#4-compliance-アプリコンプライアンス管理)
5. [controls アプリ（統制管理）](#5-controls-アプリ統制管理)
6. [audits アプリ（監査管理）](#6-audits-アプリ監査管理)
7. [reports アプリ（レポート管理）](#7-reports-アプリレポート管理)
8. [frameworks アプリ（フレームワーク管理）](#8-frameworks-アプリフレームワーク管理)
9. [common アプリ（共通機能）](#9-common-アプリ共通機能)
10. [Celeryタスク設計](#10-celeryタスク設計)

---

## 1. 設計方針

### 1.1 コーディング規約

| 項目 | 規約 |
|------|------|
| Python | PEP 8準拠、Black フォーマッタ使用 |
| Django | Fat Models, Thin Views パターンにサービス層を追加 |
| DRF | ViewSet + Serializer + Service パターン |
| 命名規則 | snake_case（Python）、camelCase（JavaScript） |
| ドキュメント | docstring（Google Style） |

### 1.2 共通基底クラス

```python
# apps/common/models.py
class BaseModel(models.Model):
    """全モデルの共通基底クラス"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, related_name='+'
    )
    updated_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, related_name='+'
    )
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True
```

---

## 2. accounts アプリ（ユーザー認証・認可）

### 2.1 モデル設計

```python
class User(AbstractBaseUser, PermissionsMixin):
    """カスタムユーザーモデル"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    department = models.CharField(max_length=100)
    role = models.CharField(max_length=30, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    login_failure_count = models.IntegerField(default=0)
    locked_at = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True)
    password_changed_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

ROLE_CHOICES = [
    ('admin', 'GRC管理者'),
    ('risk_owner', 'リスクオーナー'),
    ('compliance_officer', 'コンプライアンス担当'),
    ('auditor', '内部監査員'),
    ('executive', '経営層'),
    ('user', '一般部門担当'),
]
```

### 2.2 シリアライザ設計

```python
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name',
                  'department', 'role', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']

class TokenRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()
```

### 2.3 ビュー設計

| エンドポイント | メソッド | ビュークラス | 説明 |
|--------------|---------|------------|------|
| /api/v1/auth/login/ | POST | LoginView | ログイン |
| /api/v1/auth/logout/ | POST | LogoutView | ログアウト |
| /api/v1/auth/refresh/ | POST | TokenRefreshView | トークンリフレッシュ |
| /api/v1/auth/me/ | GET | CurrentUserView | ログインユーザー情報取得 |
| /api/v1/auth/password/change/ | POST | PasswordChangeView | パスワード変更 |
| /api/v1/users/ | GET, POST | UserViewSet | ユーザー一覧・作成 |
| /api/v1/users/{id}/ | GET, PUT, DELETE | UserViewSet | ユーザー詳細・更新・削除 |

### 2.4 サービス層設計

```python
class AuthService:
    @staticmethod
    def authenticate(email: str, password: str) -> tuple[User, dict]:
        """ユーザー認証を実行しJWTトークンを返す"""
        # 1. ユーザー検索
        # 2. アカウントロック確認
        # 3. パスワード検証
        # 4. ログイン失敗カウント管理
        # 5. JWTトークン生成
        # 6. 監査ログ記録
        pass

    @staticmethod
    def lock_account(user: User) -> None:
        """アカウントをロックする"""
        pass

class UserService:
    @staticmethod
    def create_user(data: dict, created_by: User) -> User:
        """ユーザーを作成する"""
        pass

    @staticmethod
    def deactivate_user(user_id: UUID, deactivated_by: User) -> User:
        """ユーザーを無効化する（論理削除）"""
        pass
```

---

## 3. risks アプリ（リスク管理）

### 3.1 モデル設計

```python
class Risk(BaseModel):
    """リスクモデル"""
    risk_id = models.CharField(max_length=20, unique=True)  # RSK-YYYY-NNNN
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=RISK_CATEGORY_CHOICES)
    sub_category = models.CharField(max_length=50, blank=True)
    owner = models.ForeignKey('accounts.User', on_delete=models.PROTECT,
                              related_name='owned_risks')
    department = models.CharField(max_length=100)
    project = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=30, choices=RISK_STATUS_CHOICES,
                              default='identified')
    inherent_likelihood = models.IntegerField(validators=[MinValueValidator(1),
                                                          MaxValueValidator(5)],
                                              null=True)
    inherent_impact = models.IntegerField(validators=[MinValueValidator(1),
                                                      MaxValueValidator(5)],
                                          null=True)
    inherent_score = models.IntegerField(null=True)
    inherent_level = models.CharField(max_length=20, blank=True)
    residual_likelihood = models.IntegerField(null=True)
    residual_impact = models.IntegerField(null=True)
    residual_score = models.IntegerField(null=True)
    residual_level = models.CharField(max_length=20, blank=True)
    controls = models.ManyToManyField('controls.Control', blank=True,
                                      related_name='risks')
    frameworks = models.ManyToManyField('frameworks.FrameworkControl',
                                        blank=True, related_name='risks')

RISK_CATEGORY_CHOICES = [
    ('information_security', '情報セキュリティ'),
    ('occupational_safety', '労働安全'),
    ('environmental', '環境'),
    ('legal', '法令'),
    ('quality', '品質'),
    ('financial', '財務'),
]

RISK_STATUS_CHOICES = [
    ('identified', '識別済み'),
    ('assessing', '評価中'),
    ('treating', '対応中'),
    ('monitoring', 'モニタリング中'),
    ('accepted', '受容済み'),
    ('closed', 'クローズ'),
]

class RiskEvaluation(BaseModel):
    """リスク評価履歴"""
    risk = models.ForeignKey(Risk, on_delete=models.CASCADE,
                             related_name='evaluations')
    evaluation_date = models.DateField()
    likelihood = models.IntegerField(validators=[MinValueValidator(1),
                                                 MaxValueValidator(5)])
    impact_financial = models.IntegerField(validators=[MinValueValidator(1),
                                                       MaxValueValidator(5)])
    impact_operational = models.IntegerField(validators=[MinValueValidator(1),
                                                         MaxValueValidator(5)])
    impact_legal = models.IntegerField(validators=[MinValueValidator(1),
                                                    MaxValueValidator(5)])
    impact_safety = models.IntegerField(validators=[MinValueValidator(1),
                                                     MaxValueValidator(5)])
    impact_reputation = models.IntegerField(validators=[MinValueValidator(1),
                                                         MaxValueValidator(5)])
    max_impact = models.IntegerField()  # 自動計算
    inherent_score = models.IntegerField()  # 自動計算
    control_effectiveness = models.CharField(max_length=20,
                                             choices=CONTROL_EFFECTIVENESS_CHOICES)
    residual_score = models.IntegerField()  # 自動計算
    comments = models.TextField(blank=True)
    evaluator = models.ForeignKey('accounts.User', on_delete=models.PROTECT)

class RiskTreatmentPlan(BaseModel):
    """リスク対応計画"""
    risk = models.ForeignKey(Risk, on_delete=models.CASCADE,
                             related_name='treatment_plans')
    strategy = models.CharField(max_length=20, choices=STRATEGY_CHOICES)
    description = models.TextField()
    assigned_to = models.ForeignKey('accounts.User', on_delete=models.PROTECT)
    due_date = models.DateField()
    target_residual_level = models.CharField(max_length=20)
    budget = models.DecimalField(max_digits=12, decimal_places=0, null=True)
    status = models.CharField(max_length=20, default='planned')
    progress_percentage = models.IntegerField(default=0)

STRATEGY_CHOICES = [
    ('avoid', '回避'),
    ('mitigate', '軽減'),
    ('transfer', '移転'),
    ('accept', '受容'),
]
```

### 3.2 シリアライザ設計

```python
class RiskListSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    class Meta:
        model = Risk
        fields = ['id', 'risk_id', 'title', 'category', 'owner_name',
                  'inherent_level', 'residual_level', 'status', 'created_at']

class RiskDetailSerializer(serializers.ModelSerializer):
    evaluations = RiskEvaluationSerializer(many=True, read_only=True)
    treatment_plans = RiskTreatmentPlanSerializer(many=True, read_only=True)
    controls = ControlSummarySerializer(many=True, read_only=True)
    class Meta:
        model = Risk
        fields = '__all__'

class RiskCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Risk
        fields = ['title', 'description', 'category', 'sub_category',
                  'owner', 'department', 'project', 'inherent_likelihood',
                  'inherent_impact']

class RiskEvaluationSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskEvaluation
        fields = '__all__'
        read_only_fields = ['max_impact', 'inherent_score', 'residual_score']
```

### 3.3 ビュー設計

```python
class RiskViewSet(ModelViewSet):
    """リスク管理 ViewSet"""
    queryset = Risk.objects.active()
    permission_classes = [IsAuthenticated, RiskPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = RiskFilter
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'inherent_score', 'residual_score']

    def get_serializer_class(self):
        if self.action == 'list':
            return RiskListSerializer
        elif self.action == 'create':
            return RiskCreateSerializer
        return RiskDetailSerializer

    def perform_create(self, serializer):
        risk = RiskService.create_risk(
            data=serializer.validated_data,
            user=self.request.user
        )
        serializer.instance = risk

class RiskHeatmapView(APIView):
    """リスクヒートマップ API"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = RiskSelector.get_heatmap_data(
            filters=request.query_params
        )
        return Response(data)
```

### 3.4 サービス層設計

```python
class RiskService:
    @staticmethod
    def create_risk(data: dict, user: User) -> Risk:
        """リスクを作成する"""
        # 1. リスクID自動採番（RSK-YYYY-NNNN）
        # 2. リスクスコア計算（likelihood x impact）
        # 3. リスクレベル判定
        # 4. DB保存
        # 5. 通知タスクをキュー投入
        # 6. 監査ログ記録
        pass

    @staticmethod
    def evaluate_risk(risk_id: UUID, data: dict, user: User) -> RiskEvaluation:
        """リスク評価を実施する"""
        # 1. max_impact = max(financial, operational, legal, safety, reputation)
        # 2. inherent_score = likelihood x max_impact
        # 3. inherent_level = レベル判定マトリクス参照
        # 4. residual_score = 統制有効性に基づく残留リスク計算
        # 5. 評価履歴保存
        # 6. Riskモデルのスコア・レベル更新
        # 7. 高リスク時のアラート送信
        pass

    @staticmethod
    def calculate_risk_level(score: int) -> str:
        """リスクスコアからリスクレベルを判定"""
        if score >= 20: return 'critical'    # 極高
        elif score >= 15: return 'high'      # 高
        elif score >= 10: return 'medium'    # 中
        elif score >= 5: return 'low'        # 低
        else: return 'very_low'              # 極低

class RiskSelector:
    @staticmethod
    def get_heatmap_data(filters: dict) -> dict:
        """ヒートマップデータを取得する"""
        # 5x5マトリクスの各セルに含まれるリスク件数を集計
        pass
```

---

## 4. compliance アプリ（コンプライアンス管理）

### 4.1 モデル設計

```python
class ComplianceRequirement(BaseModel):
    """コンプライアンス要件"""
    requirement_id = models.CharField(max_length=20, unique=True)  # CMP-YYYY-NNNN
    framework = models.ForeignKey('frameworks.Framework', on_delete=models.PROTECT)
    framework_control = models.ForeignKey('frameworks.FrameworkControl',
                                          on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=300)
    description = models.TextField()
    legal_reference = models.CharField(max_length=200, blank=True)
    scope = models.CharField(max_length=50, choices=SCOPE_CHOICES)
    responsible_department = models.CharField(max_length=100)
    responsible_person = models.ForeignKey('accounts.User',
                                           on_delete=models.PROTECT)
    compliance_status = models.CharField(max_length=30,
                                         choices=COMPLIANCE_STATUS_CHOICES,
                                         default='not_assessed')
    due_date = models.DateField(null=True, blank=True)
    controls = models.ManyToManyField('controls.Control', blank=True)

COMPLIANCE_STATUS_CHOICES = [
    ('compliant', '準拠'),
    ('partially_compliant', '一部準拠'),
    ('non_compliant', '非準拠'),
    ('not_applicable', '適用外'),
    ('not_assessed', '未評価'),
    ('reassessment_required', '要再評価'),
]

class ComplianceAssessment(BaseModel):
    """準拠状況評価履歴"""
    requirement = models.ForeignKey(ComplianceRequirement,
                                    on_delete=models.CASCADE,
                                    related_name='assessments')
    assessment_date = models.DateField()
    status = models.CharField(max_length=30, choices=COMPLIANCE_STATUS_CHOICES)
    comments = models.TextField(blank=True)
    assessor = models.ForeignKey('accounts.User', on_delete=models.PROTECT)

class GapAnalysis(BaseModel):
    """ギャップ分析"""
    title = models.CharField(max_length=200)
    framework = models.ForeignKey('frameworks.Framework', on_delete=models.PROTECT)
    analysis_date = models.DateField()
    total_requirements = models.IntegerField()
    compliant_count = models.IntegerField()
    partially_compliant_count = models.IntegerField()
    non_compliant_count = models.IntegerField()
    compliance_rate = models.DecimalField(max_digits=5, decimal_places=2)
    status = models.CharField(max_length=20, default='draft')

class GapItem(BaseModel):
    """ギャップ項目"""
    gap_analysis = models.ForeignKey(GapAnalysis, on_delete=models.CASCADE,
                                     related_name='items')
    requirement = models.ForeignKey(ComplianceRequirement,
                                    on_delete=models.CASCADE)
    current_status = models.CharField(max_length=30)
    target_status = models.CharField(max_length=30, default='compliant')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES)
    remediation_plan = models.TextField(blank=True)

class ImprovementPlan(BaseModel):
    """改善計画"""
    gap_item = models.ForeignKey(GapItem, on_delete=models.CASCADE,
                                 related_name='improvement_plans')
    title = models.CharField(max_length=200)
    description = models.TextField()
    assigned_to = models.ForeignKey('accounts.User', on_delete=models.PROTECT)
    due_date = models.DateField()
    budget = models.DecimalField(max_digits=12, decimal_places=0, null=True)
    status = models.CharField(max_length=20, default='planned')
    progress_percentage = models.IntegerField(default=0)

class LegalUpdate(BaseModel):
    """法令改正追跡"""
    law_name = models.CharField(max_length=200)
    update_description = models.TextField()
    effective_date = models.DateField()
    impact_scope = models.TextField()
    affected_requirements = models.ManyToManyField(ComplianceRequirement,
                                                    blank=True)
    response_status = models.CharField(max_length=20, default='pending')
```

### 4.2 サービス層設計

```python
class ComplianceService:
    @staticmethod
    def assess_requirement(requirement_id: UUID, data: dict, user: User):
        """準拠状況を評価する"""
        # 1. 評価履歴の保存
        # 2. 要件ステータスの更新
        # 3. 準拠率の再計算（Redisキャッシュ更新）
        # 4. 非準拠時の改善計画候補登録
        pass

    @staticmethod
    def calculate_compliance_rate(framework_id: UUID) -> Decimal:
        """フレームワーク別の準拠率を計算する"""
        # 準拠率 = 準拠件数 / (全件数 - 適用外件数) * 100
        pass

    @staticmethod
    def perform_gap_analysis(framework_id: UUID, user: User) -> GapAnalysis:
        """ギャップ分析を実施する"""
        # 1. 全要件の現在ステータスを取得
        # 2. 非準拠・一部準拠の項目を抽出
        # 3. ギャップ分析レコード作成
        # 4. 各ギャップ項目の優先度算出
        pass

class LegalUpdateService:
    @staticmethod
    def register_update(data: dict, user: User) -> LegalUpdate:
        """法令改正を登録し影響分析を実施する"""
        # 1. 改正情報の登録
        # 2. 影響を受ける要件の自動抽出
        # 3. 影響要件のステータスを「要再評価」に更新
        # 4. 関連者への通知
        pass
```

---

## 5. controls アプリ（統制管理）

### 5.1 モデル設計

```python
class Control(BaseModel):
    """統制項目"""
    control_id = models.CharField(max_length=20, unique=True)  # CTL-FW-NNNN
    title = models.CharField(max_length=300)
    description = models.TextField()
    control_type = models.CharField(max_length=20, choices=CONTROL_TYPE_CHOICES)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    owner = models.ForeignKey('accounts.User', on_delete=models.PROTECT,
                              related_name='owned_controls')
    framework = models.ForeignKey('frameworks.Framework',
                                  on_delete=models.PROTECT, null=True)
    framework_control = models.ForeignKey('frameworks.FrameworkControl',
                                          on_delete=models.SET_NULL, null=True)
    test_procedure = models.TextField(blank=True)
    effectiveness = models.CharField(max_length=20,
                                     choices=EFFECTIVENESS_CHOICES,
                                     default='not_assessed')
    last_test_date = models.DateField(null=True)
    next_test_date = models.DateField(null=True)

CONTROL_TYPE_CHOICES = [
    ('preventive', '予防的'),
    ('detective', '発見的'),
    ('corrective', '是正的'),
]

FREQUENCY_CHOICES = [
    ('daily', '日次'),
    ('weekly', '週次'),
    ('monthly', '月次'),
    ('quarterly', '四半期'),
    ('annually', '年次'),
    ('ad_hoc', '随時'),
]

class ControlTest(BaseModel):
    """統制テスト結果"""
    control = models.ForeignKey(Control, on_delete=models.CASCADE,
                                related_name='tests')
    test_date = models.DateField()
    tester = models.ForeignKey('accounts.User', on_delete=models.PROTECT)
    result = models.CharField(max_length=20, choices=TEST_RESULT_CHOICES)
    comments = models.TextField(blank=True)
    findings = models.TextField(blank=True)

TEST_RESULT_CHOICES = [
    ('pass', '合格'),
    ('fail', '不合格'),
    ('partial_pass', '一部合格'),
]

class EvidenceFile(BaseModel):
    """エビデンスファイル"""
    file = models.FileField(upload_to='evidence/%Y/%m/')
    original_filename = models.CharField(max_length=255)
    file_size = models.IntegerField()
    mime_type = models.CharField(max_length=100)
    sha256_hash = models.CharField(max_length=64)
    description = models.TextField(blank=True)
    tags = models.JSONField(default=list)
    # ポリモーフィック関連
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')

class CorrectiveAction(BaseModel):
    """是正措置"""
    title = models.CharField(max_length=200)
    description = models.TextField()
    root_cause = models.TextField(blank=True)
    assigned_to = models.ForeignKey('accounts.User', on_delete=models.PROTECT,
                                    related_name='corrective_actions')
    due_date = models.DateField()
    status = models.CharField(max_length=20, default='planned',
                              choices=CA_STATUS_CHOICES)
    # ポリモーフィック関連（統制テスト or 監査所見から生成）
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE,
                                     null=True)
    object_id = models.UUIDField(null=True)
    source_object = GenericForeignKey('content_type', 'object_id')
    completion_date = models.DateField(null=True)
    completion_comment = models.TextField(blank=True)
    verified_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL,
                                    null=True, related_name='verified_cas')
    verified_at = models.DateTimeField(null=True)

CA_STATUS_CHOICES = [
    ('planned', '計画中'),
    ('in_progress', '実施中'),
    ('pending_review', '完了確認待ち'),
    ('completed', '完了'),
    ('overdue', '期限超過'),
    ('rejected', '差戻し'),
]
```

### 5.2 サービス層設計

```python
class ControlService:
    @staticmethod
    def create_control(data: dict, user: User) -> Control:
        """統制項目を作成する"""
        # 1. 統制ID自動採番
        # 2. 次回テスト日の自動計算
        # 3. DB保存
        pass

    @staticmethod
    def record_test_result(control_id: UUID, data: dict, user: User):
        """統制テスト結果を記録する"""
        # 1. テスト結果保存
        # 2. 統制有効性ステータス更新
        # 3. 不合格時: 是正措置タスク自動生成
        # 4. 次回テスト日の更新
        pass

class EvidenceService:
    @staticmethod
    def upload_evidence(file, metadata: dict, user: User) -> EvidenceFile:
        """エビデンスをアップロードする"""
        # 1. ファイル形式・サイズバリデーション
        # 2. SHA-256ハッシュ計算
        # 3. ストレージへの保存
        # 4. メタデータの記録
        # 5. 監査ログ記録
        pass

class CorrectiveActionService:
    @staticmethod
    def submit_completion(ca_id: UUID, data: dict, user: User):
        """是正措置の完了申請を処理する"""
        # 1. 完了報告の保存
        # 2. ステータスを「完了確認待ち」に更新
        # 3. 確認者（コンプライアンス担当）に通知
        pass

    @staticmethod
    def verify_completion(ca_id: UUID, approved: bool, user: User):
        """是正措置の完了を確認する"""
        # 1. 承認時: ステータスを「完了」に更新、再テストをスケジュール
        # 2. 却下時: ステータスを「差戻し」、担当者に通知
        pass
```

---

## 6. audits アプリ（監査管理）

### 6.1 モデル設計

```python
class Audit(BaseModel):
    """監査"""
    audit_id = models.CharField(max_length=20, unique=True)  # AUD-YYYY-NNNN
    title = models.CharField(max_length=200)
    audit_type = models.CharField(max_length=20, choices=AUDIT_TYPE_CHOICES)
    scope = models.TextField()
    target_department = models.CharField(max_length=100)
    framework = models.ForeignKey('frameworks.Framework',
                                  on_delete=models.PROTECT, null=True)
    lead_auditor = models.ForeignKey('accounts.User', on_delete=models.PROTECT,
                                     related_name='led_audits')
    team_members = models.ManyToManyField('accounts.User',
                                          related_name='audit_participations')
    planned_start_date = models.DateField()
    planned_end_date = models.DateField()
    actual_start_date = models.DateField(null=True)
    actual_end_date = models.DateField(null=True)
    status = models.CharField(max_length=20, choices=AUDIT_STATUS_CHOICES,
                              default='draft')
    approved_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL,
                                    null=True, related_name='approved_audits')
    approved_at = models.DateTimeField(null=True)

AUDIT_STATUS_CHOICES = [
    ('draft', '下書き'),
    ('pending_approval', '承認待ち'),
    ('approved', '承認済み'),
    ('in_progress', '実施中'),
    ('suspended', '中断中'),
    ('completed', '実施完了'),
    ('reported', '報告済み'),
    ('rejected', '差戻し'),
]

class AuditChecklist(BaseModel):
    """監査チェックリスト項目"""
    audit = models.ForeignKey(Audit, on_delete=models.CASCADE,
                              related_name='checklist_items')
    control = models.ForeignKey('controls.Control', on_delete=models.PROTECT)
    sequence = models.IntegerField()
    result = models.CharField(max_length=20, choices=CHECKLIST_RESULT_CHOICES,
                              null=True)
    notes = models.TextField(blank=True)
    auditor = models.ForeignKey('accounts.User', on_delete=models.SET_NULL,
                                null=True)

class AuditFinding(BaseModel):
    """監査所見"""
    finding_id = models.CharField(max_length=20, unique=True)  # FND-YYYY-NNNN
    audit = models.ForeignKey(Audit, on_delete=models.CASCADE,
                              related_name='findings')
    finding_type = models.CharField(max_length=30,
                                    choices=FINDING_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    reference_control = models.ForeignKey('controls.Control',
                                          on_delete=models.SET_NULL, null=True)
    impact_scope = models.CharField(max_length=200)
    risk_level = models.CharField(max_length=20, blank=True)
    is_recurrence = models.BooleanField(default=False)
    previous_finding = models.ForeignKey('self', on_delete=models.SET_NULL,
                                         null=True, blank=True)
    status = models.CharField(max_length=20, default='open')

FINDING_TYPE_CHOICES = [
    ('major_nc', '重大不適合'),
    ('minor_nc', '軽微不適合'),
    ('observation', '観察事項'),
    ('recommendation', '推奨事項'),
    ('opportunity', '改善機会'),
]

class CorrectiveActionRequest(BaseModel):
    """是正勧告（CAR）"""
    finding = models.ForeignKey(AuditFinding, on_delete=models.CASCADE,
                                related_name='corrective_action_requests')
    description = models.TextField()
    due_date = models.DateField()
    responsible_person = models.ForeignKey('accounts.User',
                                           on_delete=models.PROTECT)
    status = models.CharField(max_length=20, default='issued')
    follow_up_date = models.DateField(null=True)
    follow_up_result = models.CharField(max_length=20, null=True)
```

### 6.2 サービス層設計

```python
class AuditService:
    @staticmethod
    def create_audit_plan(data: dict, user: User) -> Audit:
        """監査計画を作成する"""
        pass

    @staticmethod
    def generate_checklist(audit_id: UUID) -> list[AuditChecklist]:
        """監査スコープに基づきチェックリストを自動生成する"""
        pass

    @staticmethod
    def record_finding(audit_id: UUID, data: dict, user: User) -> AuditFinding:
        """監査所見を記録する"""
        # 1. 所見ID自動採番
        # 2. 再発チェック（過去の類似所見検索）
        # 3. 重大不適合時のエスカレーション通知
        pass

    @staticmethod
    def issue_car(finding_id: UUID, data: dict, user: User):
        """是正勧告を発行する"""
        # 1. 是正勧告書PDF生成（Celeryタスク）
        # 2. 是正責任者への通知
        # 3. 是正措置管理への自動登録
        # 4. フォローアップ日程の自動計算
        pass
```

---

## 7. reports アプリ（レポート管理）

### 7.1 モデル設計

```python
class ReportTemplate(BaseModel):
    """レポートテンプレート"""
    name = models.CharField(max_length=200)
    template_type = models.CharField(max_length=30,
                                     choices=REPORT_TYPE_CHOICES)
    description = models.TextField(blank=True)
    configuration = models.JSONField(default=dict)
    is_system = models.BooleanField(default=False)  # システム定義テンプレート

class GeneratedReport(BaseModel):
    """生成済みレポート"""
    template = models.ForeignKey(ReportTemplate, on_delete=models.SET_NULL,
                                 null=True)
    title = models.CharField(max_length=200)
    period_start = models.DateField()
    period_end = models.DateField()
    data_snapshot = models.JSONField()
    file = models.FileField(upload_to='reports/%Y/%m/', null=True)
    status = models.CharField(max_length=20, default='generating')
    generated_by = models.ForeignKey('accounts.User', on_delete=models.PROTECT)

class ReportSchedule(BaseModel):
    """レポート自動生成スケジュール"""
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE)
    frequency = models.CharField(max_length=20)  # monthly/quarterly/yearly
    cron_expression = models.CharField(max_length=100)
    recipients = models.ManyToManyField('accounts.User')
    is_active = models.BooleanField(default=True)
    last_generated_at = models.DateTimeField(null=True)

class AlertRule(BaseModel):
    """アラートルール"""
    name = models.CharField(max_length=200)
    trigger_type = models.CharField(max_length=50)
    trigger_condition = models.JSONField()
    notification_channels = models.JSONField()  # ['email', 'slack', 'dashboard']
    recipient_roles = models.JSONField(default=list)
    recipient_users = models.ManyToManyField('accounts.User', blank=True)
    frequency = models.CharField(max_length=20, default='immediate')
    is_active = models.BooleanField(default=True)

class AlertHistory(BaseModel):
    """アラート発報履歴"""
    rule = models.ForeignKey(AlertRule, on_delete=models.CASCADE)
    triggered_at = models.DateTimeField(auto_now_add=True)
    trigger_data = models.JSONField()
    recipients_notified = models.JSONField()
    status = models.CharField(max_length=20)
```

### 7.2 サービス層設計

```python
class DashboardService:
    @staticmethod
    def get_risk_summary(user: User, period: str) -> dict:
        """リスク概況データを取得する"""
        pass

    @staticmethod
    def get_compliance_rate(user: User) -> dict:
        """コンプライアンス準拠率を取得する"""
        pass

    @staticmethod
    def get_control_effectiveness(user: User) -> dict:
        """統制有効性サマリーを取得する"""
        pass

    @staticmethod
    def get_open_findings(user: User) -> list:
        """未対応監査所見一覧を取得する"""
        pass

class ReportService:
    @staticmethod
    def generate_report(template_id: UUID, period: dict, user: User):
        """レポートを生成する（Celeryタスクとして実行）"""
        pass

    @staticmethod
    def export_data(data_source: str, filters: dict, format: str, user: User):
        """データをエクスポートする"""
        pass

class AlertService:
    @staticmethod
    def check_alert_conditions():
        """全アラートルールの条件をチェックする（Celery定期タスク）"""
        pass

    @staticmethod
    def send_notification(rule: AlertRule, trigger_data: dict):
        """アラート通知を送信する"""
        pass
```

---

## 8. frameworks アプリ（フレームワーク管理）

### 8.1 モデル設計

```python
class Framework(BaseModel):
    """フレームワーク"""
    code = models.CharField(max_length=50, unique=True)  # ISO27001, NIST_CSF
    name = models.CharField(max_length=200)
    version = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

class FrameworkCategory(BaseModel):
    """フレームワークカテゴリ（階層構造）"""
    framework = models.ForeignKey(Framework, on_delete=models.CASCADE,
                                  related_name='categories')
    parent = models.ForeignKey('self', on_delete=models.CASCADE,
                               null=True, blank=True, related_name='children')
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    sort_order = models.IntegerField(default=0)

class FrameworkControl(BaseModel):
    """フレームワーク管理策"""
    framework = models.ForeignKey(Framework, on_delete=models.CASCADE,
                                  related_name='controls')
    category = models.ForeignKey(FrameworkCategory, on_delete=models.CASCADE,
                                 related_name='controls')
    code = models.CharField(max_length=50)
    title = models.CharField(max_length=300)
    description = models.TextField()
    guidance = models.TextField(blank=True)
    sort_order = models.IntegerField(default=0)

class FrameworkMapping(BaseModel):
    """フレームワーク間マッピング"""
    source_control = models.ForeignKey(FrameworkControl,
                                       on_delete=models.CASCADE,
                                       related_name='mappings_from')
    target_control = models.ForeignKey(FrameworkControl,
                                       on_delete=models.CASCADE,
                                       related_name='mappings_to')
    mapping_type = models.CharField(max_length=20)  # exact/partial/related
    notes = models.TextField(blank=True)
```

---

## 9. common アプリ（共通機能）

### 9.1 監査ログ

```python
class AuditLog(models.Model):
    """監査ログ（改ざん防止のため BaseModel を継承しない）"""
    id = models.BigAutoField(primary_key=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL,
                             null=True)
    user_email = models.CharField(max_length=254)  # ユーザー削除後も保持
    action = models.CharField(max_length=50)  # CREATE/READ/UPDATE/DELETE/LOGIN等
    resource_type = models.CharField(max_length=100)  # モデル名
    resource_id = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(blank=True)
    request_data = models.JSONField(null=True)  # リクエストボディ（機密除外）
    response_status = models.IntegerField(null=True)
    changes = models.JSONField(null=True)  # 変更前後の差分

    class Meta:
        managed = True
        # 削除・更新を防止するカスタムマネージャを使用
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp', 'action']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
        ]
```

### 9.2 通知サービス

```python
class NotificationService:
    @staticmethod
    def send_email(recipients: list[str], subject: str, body: str,
                   attachments: list = None):
        """メール通知を送信する"""
        pass

    @staticmethod
    def send_slack(channel: str, message: str):
        """Slack通知を送信する"""
        pass

    @staticmethod
    def send_dashboard_notification(user_ids: list[UUID], message: str,
                                    severity: str):
        """ダッシュボード通知を送信する"""
        pass
```

---

## 10. Celeryタスク設計

### 10.1 タスク一覧

| タスク名 | スケジュール | 説明 |
|---------|------------|------|
| `check_risk_kri_thresholds` | 1時間ごと | KRI閾値超過チェック |
| `check_overdue_tasks` | 日次 06:00 | 期限超過タスクの検出・通知 |
| `generate_scheduled_report` | Celery Beat | 定期レポートの自動生成 |
| `check_alert_conditions` | 5分ごと | アラート条件チェック |
| `send_notification_email` | 即時（キュー） | メール通知の非同期送信 |
| `send_notification_slack` | 即時（キュー） | Slack通知の非同期送信 |
| `generate_report_pdf` | 即時（キュー） | レポートPDF生成 |
| `calculate_compliance_rate` | 評価更新時 | 準拠率の再計算 |
| `recalculate_residual_risk` | 統制評価更新時 | 残留リスクの再計算 |
| `cleanup_expired_tokens` | 日次 03:00 | 期限切れJWTトークンの削除 |
| `backup_audit_logs` | 日次 02:00 | 監査ログのアーカイブ |

### 10.2 タスク設計例

```python
# tasks/risk_tasks.py
@shared_task(bind=True, max_retries=3)
def check_risk_kri_thresholds(self):
    """KRI閾値超過をチェックしアラートを発報する"""
    try:
        risks = Risk.objects.filter(
            status__in=['monitoring', 'treating'],
            is_deleted=False
        )
        for risk in risks:
            if risk.kri_value and risk.kri_threshold:
                if risk.kri_value > risk.kri_threshold:
                    AlertService.send_notification(
                        rule_type='kri_threshold',
                        trigger_data={
                            'risk_id': str(risk.id),
                            'risk_title': risk.title,
                            'kri_value': risk.kri_value,
                            'threshold': risk.kri_threshold,
                        }
                    )
    except Exception as exc:
        self.retry(exc=exc, countdown=60)
```
