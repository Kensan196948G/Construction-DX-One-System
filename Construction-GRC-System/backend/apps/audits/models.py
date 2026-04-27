import uuid

from django.db import models


class Audit(models.Model):
    STATUS_CHOICES = [
        ("planned", "Planned"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=256)
    scope = models.TextField(blank=True)
    auditor = models.CharField(max_length=128, blank=True)
    status = models.CharField(
        max_length=16, choices=STATUS_CHOICES, default="planned", db_index=True
    )
    planned_date = models.DateField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.status})"


class Finding(models.Model):
    SEVERITY_CHOICES = [
        ("critical", "Critical"),
        ("high", "High"),
        ("medium", "Medium"),
        ("low", "Low"),
        ("info", "Info"),
    ]
    STATUS_CHOICES = [
        ("open", "Open"),
        ("in_remediation", "In Remediation"),
        ("resolved", "Resolved"),
        ("accepted", "Accepted"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    audit = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name="findings")
    title = models.CharField(max_length=256)
    description = models.TextField(blank=True)
    severity = models.CharField(
        max_length=16, choices=SEVERITY_CHOICES, default="medium", db_index=True
    )
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="open", db_index=True)
    recommendation = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["severity", "-created_at"]

    def __str__(self):
        return f"{self.title} [{self.severity}]"
