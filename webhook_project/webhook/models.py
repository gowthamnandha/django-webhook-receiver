from django.db import models

class RawWebhookLog(models.Model):
    data = models.JSONField()  # Store entire webhook payload as-is
    received_at = models.DateTimeField(auto_now_add=True)