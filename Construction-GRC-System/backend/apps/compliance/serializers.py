from rest_framework import serializers

from .models import Control


class ControlSerializer(serializers.ModelSerializer):
    class Meta:
        model = Control
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
