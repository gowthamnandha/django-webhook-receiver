import hashlib
import hmac
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Tuple

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from .models import WebhookEvent

logger = logging.getLogger("webhook")
_executor = ThreadPoolExecutor(max_workers=4)


class WebhookValidationError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def get_provider_config(provider: str) -> Dict[str, Any]:
    return settings.WEBHOOK_PROVIDERS.get(provider, settings.WEBHOOK_PROVIDERS["default"])


def parse_json_body(raw_body: bytes) -> Dict[str, Any]:
    if not raw_body:
        return {}
    try:
        return json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise WebhookValidationError("Invalid JSON payload") from exc


def extract_signature(signature_header: str) -> str:
    if not signature_header:
        return ""
    if "v1=" in signature_header:
        parts = [segment.strip() for segment in signature_header.split(",")]
        for part in parts:
            if part.startswith("v1="):
                return part.split("=", 1)[1]
    if "=" in signature_header:
        return signature_header.split("=", 1)[1]
    return signature_header


def verify_signature(raw_body: bytes, provider: str, headers: Dict[str, Any]) -> bool:
    config = get_provider_config(provider)
    secret = config.get("secret")
    if not secret:
        return False
    header_name = config.get("signature_header", "X-Signature")
    provided_signature = headers.get(header_name)
    if not provided_signature:
        return False
    signature_value = extract_signature(provided_signature)
    digest = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, signature_value)


def validate_payload(provider: str, payload: Dict[str, Any]) -> None:
    config = get_provider_config(provider)
    required_fields = config.get("required_fields", [])
    missing = [field for field in required_fields if field not in payload]
    if missing:
        raise WebhookValidationError(
            f"Missing required fields: {', '.join(missing)}",
            status_code=422,
        )


def enforce_rate_limit(provider: str, client_ip: str) -> None:
    config = get_provider_config(provider)
    rate_limit = config.get("rate_limit", {})
    max_requests = rate_limit.get("max_requests")
    window_seconds = rate_limit.get("window_seconds")
    if not max_requests or not window_seconds:
        return
    key = f"webhook:{provider}:{client_ip}"
    current = cache.get(key, 0)
    if current >= max_requests:
        raise WebhookValidationError("Rate limit exceeded", status_code=429)
    if current == 0:
        cache.set(key, 1, timeout=window_seconds)
    else:
        cache.incr(key)


def process_webhook_event(event_id: int) -> None:
    event = WebhookEvent.objects.get(id=event_id)
    try:
        event.status = WebhookEvent.STATUS_PROCESSED
        event.processed_at = timezone.now()
        event.save(update_fields=["status", "processed_at"])
    except Exception as exc:
        logger.exception("Webhook processing failed", extra={"event_id": event_id})
        event.status = WebhookEvent.STATUS_FAILED
        event.error_message = str(exc)
        event.processed_at = timezone.now()
        event.save(update_fields=["status", "error_message", "processed_at"])


def enqueue_processing(event_id: int) -> None:
    if not settings.WEBHOOK_ASYNC_ENABLED:
        process_webhook_event(event_id)
        return
    _executor.submit(process_webhook_event, event_id)
