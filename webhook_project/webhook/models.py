from django.db import models


class WebhookEvent(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PROCESSED = "processed"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PROCESSED, "Processed"),
        (STATUS_FAILED, "Failed"),
    ]

    provider = models.CharField(max_length=100, default="default")
    event_type = models.CharField(max_length=200, blank=True)
    correlation_id = models.CharField(max_length=200, blank=True)
    signature_valid = models.BooleanField(default=False)
    headers = models.JSONField(default=dict, blank=True)
    payload = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    error_message = models.TextField(blank=True)
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.provider}:{self.event_type or 'event'} ({self.status})"
