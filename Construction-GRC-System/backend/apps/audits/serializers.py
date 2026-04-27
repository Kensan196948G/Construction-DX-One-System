from rest_framework import serializers

from .models import Audit, Finding


class FindingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Finding
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class AuditSerializer(serializers.ModelSerializer):
    findings = FindingSerializer(many=True, read_only=True)
    findings_count = serializers.SerializerMethodField()

    class Meta:
        model = Audit
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_findings_count(self, obj):
        return obj.findings.count()
