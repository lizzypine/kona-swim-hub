import json
import logging
from uuid import UUID

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, RequestDataTooBig
from django.db import DatabaseError, transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_POST

from .forwarding import configuration, process_email, recipients
from .signatures import InvalidSignature, verify_signature


logger = logging.getLogger(__name__)


def unavailable(status):
    response = JsonResponse({"status": status}, status=503)
    response["Retry-After"] = "30"
    return response


@csrf_exempt
@transaction.non_atomic_requests
@require_POST
@sensitive_post_parameters()
@sensitive_variables()
def resend_webhook(request):
    try:
        body = request.body
        if len(body) > 256 * 1024:
            return JsonResponse({"error": "Request too large"}, status=413)
        verify_signature(body, request.headers, settings.RESEND_WEBHOOK_SECRET)
    except RequestDataTooBig:
        return JsonResponse({"error": "Request too large"}, status=413)
    except ImproperlyConfigured:
        logger.error("Inbound webhook signing configuration unavailable")
        return unavailable("configuration_error")
    except InvalidSignature:
        logger.warning("Inbound webhook signature rejected")
        return JsonResponse({"error": "Invalid signature"}, status=400)
    try:
        event = json.loads(body)
        if not isinstance(event, dict) or not isinstance(event.get("type"), str):
            raise ValueError
        if event["type"] != "email.received":
            return JsonResponse({"status": "ignored"})
        data = event["data"]
        email_id = UUID(data["email_id"])
        event_recipients = recipients(data)
    except (ValueError, TypeError, KeyError, AttributeError):
        return JsonResponse({"error": "Invalid event"}, status=400)
    try:
        config = configuration()
    except ImproperlyConfigured:
        logger.error("Inbound forwarding configuration unavailable")
        return unavailable("configuration_error")
    if config[2].casefold() not in event_recipients:
        return JsonResponse({"status": "ignored"})
    try:
        result = process_email(email_id, config)
    except DatabaseError:
        # No traceback, SQL, message body, addresses, or exception text in logs.
        logger.error("Inbound forwarding database unavailable email_id=%s", email_id)
        return unavailable("database_error")
    if result in ("busy", "retry", "needs_review"):
        return unavailable(result)
    return JsonResponse({"status": result})
