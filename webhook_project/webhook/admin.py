from django.contrib import admin

from .models import WebhookEvent


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "provider",
        "event_type",
        "status",
        "signature_valid",
        "received_at",
    )
    list_filter = ("provider", "status", "signature_valid", "received_at")
    search_fields = ("provider", "event_type", "correlation_id")
    readonly_fields = ("received_at", "processed_at")
