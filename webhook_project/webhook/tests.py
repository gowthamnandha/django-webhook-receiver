import hashlib
import hmac
import json

from django.core.cache import cache
from django.test import Client, TestCase, override_settings

from .models import WebhookEvent


TEST_PROVIDERS = {
    "default": {
        "secret": "test-secret",
        "signature_header": "X-Signature",
        "event_type_header": "X-Event-Type",
        "required_fields": ["id"],
        "rate_limit": {"max_requests": 1, "window_seconds": 60},
    }
}


@override_settings(WEBHOOK_PROVIDERS=TEST_PROVIDERS)
class WebhookReceiverTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()

    def _sign(self, payload: dict) -> str:
        raw = json.dumps(payload).encode("utf-8")
        digest = hmac.new(b"test-secret", raw, hashlib.sha256).hexdigest()
        return digest

    def test_accepts_valid_signature_and_payload(self):
        payload = {"id": "evt_123", "type": "ping"}
        signature = self._sign(payload)
        response = self.client.post(
            "/webhook/",
            data=json.dumps(payload),
            content_type="application/json",
            **{"HTTP_X_SIGNATURE": signature, "HTTP_X_EVENT_TYPE": "ping"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(WebhookEvent.objects.count(), 1)
        event = WebhookEvent.objects.first()
        self.assertEqual(event.event_type, "ping")
        self.assertTrue(event.signature_valid)

    def test_rejects_missing_required_fields(self):
        payload = {"type": "ping"}
        signature = self._sign(payload)
        response = self.client.post(
            "/webhook/",
            data=json.dumps(payload),
            content_type="application/json",
            **{"HTTP_X_SIGNATURE": signature},
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(WebhookEvent.objects.count(), 0)

    def test_rate_limit(self):
        payload = {"id": "evt_123"}
        signature = self._sign(payload)
        response = self.client.post(
            "/webhook/",
            data=json.dumps(payload),
            content_type="application/json",
            **{"HTTP_X_SIGNATURE": signature},
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            "/webhook/",
            data=json.dumps(payload),
            content_type="application/json",
            **{"HTTP_X_SIGNATURE": signature},
        )
        self.assertEqual(response.status_code, 429)
