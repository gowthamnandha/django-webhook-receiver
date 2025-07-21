from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

from .models import RawWebhookLog

@csrf_exempt
def webhook_receiver(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        data = {}

    # print("Webhook payload received:", data)

    # Save raw data to DB
    RawWebhookLog.objects.create(data=data)

    return JsonResponse({"status": "received"})
