import uuid

from django.db import models


class Risk(models.Model):
    LIKELIHOOD_CHOICES = [(i, str(i)) for i in range(1, 6)]
    IMPACT_CHOICES = [(i, str(i)) for i in range(1, 6)]
    STATUS_CHOICES = [
        ("open", "Open"),
        ("mitigated", "Mitigated"),
        ("accepted", "Accepted"),
        ("closed", "Closed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=256)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=64, blank=True)
    likelihood = models.IntegerField(choices=LIKELIHOOD_CHOICES, default=3)
    impact = models.IntegerField(choices=IMPACT_CHOICES, default=3)
    risk_score = models.FloatField(default=0.0)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="open", db_index=True)
    owner = models.CharField(max_length=128, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-risk_score", "-created_at"]

    def save(self, *args, **kwargs):
        self.risk_score = float(self.likelihood * self.impact)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} (score={self.risk_score})"
