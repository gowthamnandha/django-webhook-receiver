import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import WebhookEvent
from .services import (
    WebhookValidationError,
    enqueue_processing,
    enforce_rate_limit,
    get_provider_config,
    parse_json_body,
    validate_payload,
    verify_signature,
)

logger = logging.getLogger("webhook")


@csrf_exempt
def webhook_receiver(request, provider="default"):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    client_ip = request.META.get("REMOTE_ADDR", "unknown")

    try:
        enforce_rate_limit(provider, client_ip)
        payload = parse_json_body(request.body)
        validate_payload(provider, payload)
    except WebhookValidationError as exc:
        logger.warning(
            "Webhook validation failed",
            extra={"provider": provider, "error": exc.message, "correlation_id": request.correlation_id},
        )
        return JsonResponse({"error": exc.message}, status=exc.status_code)

    headers = {key: value for key, value in request.headers.items()}
    signature_valid = verify_signature(request.body, provider, headers)
    if not signature_valid:
        return JsonResponse({"error": "Invalid signature"}, status=401)

    config = get_provider_config(provider)
    event_type_header = config.get("event_type_header")
    event_type = ""
    if event_type_header:
        event_type = headers.get(event_type_header, "")
    if not event_type:
        event_type = payload.get("type", "") if isinstance(payload, dict) else ""

    event = WebhookEvent.objects.create(
        provider=provider,
        event_type=event_type,
        correlation_id=request.correlation_id,
        signature_valid=signature_valid,
        headers=headers,
        payload=payload,
    )

    logger.info(
        "Webhook received",
        extra={
            "provider": provider,
            "event_id": event.id,
            "event_type": event.event_type,
            "correlation_id": request.correlation_id,
        },
    )

    enqueue_processing(event.id)

    return JsonResponse({"status": "received", "id": event.id})
