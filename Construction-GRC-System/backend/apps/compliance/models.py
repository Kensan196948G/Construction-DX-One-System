import uuid

from django.db import models


class Control(models.Model):
    APPLICABILITY_CHOICES = [
        ("applicable", "Applicable"),
        ("not_applicable", "Not Applicable"),
    ]
    IMPLEMENTATION_STATUS_CHOICES = [
        ("not_started", "Not Started"),
        ("in_progress", "In Progress"),
        ("implemented", "Implemented"),
        ("verified", "Verified"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    control_number = models.CharField(max_length=16, unique=True)
    title = models.CharField(max_length=256)
    domain = models.CharField(max_length=128)
    applicability = models.CharField(
        max_length=16, choices=APPLICABILITY_CHOICES, default="applicable"
    )
    implementation_status = models.CharField(
        max_length=16,
        choices=IMPLEMENTATION_STATUS_CHOICES,
        default="not_started",
        db_index=True,
    )
    description = models.TextField(blank=True)
    justification = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["control_number"]

    def __str__(self):
        return f"{self.control_number} {self.title}"
