from rest_framework import serializers

from .models import Risk


class RiskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Risk
        fields = "__all__"
        read_only_fields = ["id", "risk_score", "created_at", "updated_at"]
