import base64
import hashlib
import logging
from datetime import timedelta
from email.utils import getaddresses
from uuid import UUID, uuid4

from bs4 import BeautifulSoup
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.validators import validate_email
from django.db.models import F, Q
from django.utils import timezone

from .client import ForwardingError, ResendClient, encode_payload
from .models import InboundEmail


logger = logging.getLogger(__name__)
RETRY_WINDOW = timedelta(hours=23)  # Stay inside Resend's 24-hour idempotency TTL.
LEASE_DURATION = timedelta(minutes=2)  # Longer than the 40-second client budget.
MAX_TOTAL_ATTACHMENT_BYTES = 10 * 1024 * 1024


def mailbox(value):
    if not isinstance(value, str) or any(ord(char) < 32 for char in value):
        raise ValueError
    parsed = getaddresses([value])
    if len(parsed) != 1:
        raise ValueError
    name, address = parsed[0]
    try:
        validate_email(address)
    except ValidationError:
        raise ValueError from None
    return name, address


def configuration():
    try:
        _, destination = mailbox(settings.EMAIL_FORWARD_TO)
        mailbox(settings.DEFAULT_FROM_EMAIL)
        _, inbound_address = mailbox(settings.RESEND_INBOUND_ADDRESS)
        if not settings.RESEND_API_KEY or len(settings.DEFAULT_FROM_EMAIL) > 320:
            raise ValueError
    except (ValueError, AttributeError):
        raise ImproperlyConfigured("Inbound email forwarding is not configured") from None
    return destination, settings.DEFAULT_FROM_EMAIL, inbound_address


def mailbox_key(address):
    local, domain = address.casefold().rsplit("@", 1)
    if domain in ("gmail.com", "googlemail.com"):
        return local.split("+", 1)[0].replace(".", "") + "@gmail.com"
    return address.casefold()


def recipients(message):
    result = set()
    for key in ("to", "cc", "bcc"):
        values = message.get(key, [])
        if not isinstance(values, list):
            raise ValueError
        for value in values:
            _, address = mailbox(value)
            result.add(address.casefold())
    return result


def clean_line(value, limit=900):
    if not isinstance(value, str):
        raise ValueError
    value = "".join(char if ord(char) >= 32 and ord(char) != 127 else " " for char in value)
    return " ".join(value.split())[:limit]


def build_payload(email, row, inbound_address, client):
    if str(UUID(email["id"])) != str(row.email_id):
        raise ValueError
    if inbound_address.casefold() not in recipients(email):
        return None, "unmatched_recipient"
    _, original_address = mailbox(email["from"])
    _, forward_address = mailbox(row.forward_from)
    if mailbox_key(original_address) in {
        mailbox_key(row.forward_to), mailbox_key(forward_address), mailbox_key(inbound_address)
    }:
        return None, "loop_sender"
    headers = email.get("headers") or {}
    if not isinstance(headers, dict):
        raise ValueError
    headers = {key.lower(): value for key, value in headers.items()}
    if headers.get("x-kona-swim-hub-forwarded") == "1":
        return None, "loop_marker"

    original_from = email["from"]
    # Recover a display name only if the header refers to the same sender.
    try:
        header_from = headers.get("from", original_from)
        if mailbox(header_from)[1].casefold() == original_address.casefold():
            original_from = header_from
    except ValueError:
        pass
    subject = clean_line(email.get("subject") or "(no subject)")
    text = email.get("text")
    if text is None or text == "":
        html = email.get("html") or ""
        if not isinstance(html, str):
            raise ValueError
        soup = BeautifulSoup(html, "html.parser")
        for element in soup(["script", "style", "head", "template"]):
            element.decompose()
        text = soup.get_text("\n", strip=True)
    if not isinstance(text, str):
        raise ValueError
    payload = {
        "from": row.forward_from,
        "to": [row.forward_to],
        "reply_to": original_address,
        "subject": subject if subject.lower().startswith("fwd:") else f"Fwd: {subject}",
        "text": (
            "Forwarded message. Original sender information is unverified.\n"
            f"From: {clean_line(original_from)}\nSubject: {subject}\n\n{text}"
        ),
        "headers": {"X-Kona-Swim-Hub-Forwarded": "1", "Auto-Submitted": "auto-generated"},
    }
    attachments = email.get("attachments") or []
    if not isinstance(attachments, list):
        raise ValueError
    if len(attachments) > 10:
        raise ForwardingError("attachment_count_limit", needs_review=True)
    total_size = 0
    forwarded_attachments = []
    for attachment in sorted(attachments, key=lambda item: item["id"]):
        attachment_id = UUID(attachment["id"])
        details = client.get_attachment(row.email_id, attachment_id)
        if UUID(details["id"]) != attachment_id:
            raise ValueError
        size = details.get("size")
        if not isinstance(size, int) or size < 0:
            raise ValueError
        if size > 5 * 1024 * 1024 or total_size + size > MAX_TOTAL_ATTACHMENT_BYTES:
            raise ForwardingError("attachment_size_limit", needs_review=True)
        content = client.download_attachment(details["download_url"])
        total_size += len(content)
        if total_size > MAX_TOTAL_ATTACHMENT_BYTES:
            raise ForwardingError("attachment_size_limit", needs_review=True)
        filename = clean_line(details.get("filename") or "attachment.bin", 255)
        filename = filename.replace("\\", "/").rsplit("/", 1)[-1] or "attachment.bin"
        forwarded_attachments.append({
            "filename": filename, "content": base64.b64encode(content).decode(),
        })
    if forwarded_attachments:
        payload["attachments"] = forwarded_attachments
    if len(encode_payload(payload)) > 20 * 1024 * 1024:
        raise ForwardingError("message_size_limit", needs_review=True)
    return payload, ""


def process_email(email_id, config):
    destination, sender, inbound_address = config
    row, _ = InboundEmail.objects.get_or_create(
        email_id=email_id, defaults={"forward_to": destination, "forward_from": sender}
    )
    if row.status in (InboundEmail.Status.FORWARDED, InboundEmail.Status.IGNORED):
        return row.status
    if row.status == InboundEmail.Status.NEEDS_REVIEW:
        return "needs_review"
    now = timezone.now()
    lease_id = uuid4()
    claimed = InboundEmail.objects.filter(
        Q(lease_until__isnull=True) | Q(lease_until__lte=now),
        email_id=email_id,
        status__in=[InboundEmail.Status.PENDING, InboundEmail.Status.PROCESSING],
    ).update(
        status=InboundEmail.Status.PROCESSING, lease_id=lease_id,
        lease_until=now + LEASE_DURATION, attempts=F("attempts") + 1, updated_at=now,
    )
    if not claimed:
        return "busy"
    owned = InboundEmail.objects.filter(email_id=email_id, lease_id=lease_id)
    row.refresh_from_db()
    try:
        if row.first_send_at and now - row.first_send_at >= RETRY_WINDOW:
            raise ForwardingError("idempotency_window_expired", needs_review=True)
        client = ResendClient(settings.RESEND_API_KEY)
        email = client.get_received(email_id)
        payload, ignored_reason = build_payload(email, row, inbound_address, client)
        if payload is None:
            owned.update(
                status=InboundEmail.Status.IGNORED, error_code=ignored_reason,
                lease_id=None, lease_until=None, updated_at=timezone.now(),
            )
            logger.info("Inbound forwarding ignored email_id=%s reason=%s", email_id, ignored_reason)
            return "ignored"
        digest = hashlib.sha256(encode_payload(payload)).hexdigest()
        if row.payload_sha256 and row.payload_sha256 != digest:
            raise ForwardingError("payload_changed", needs_review=True)
        # Commit the ambiguity boundary before the external side effect.
        # A crash after send must reuse this exact key/payload, even without a response.
        if not owned.update(
            first_send_at=row.first_send_at or timezone.now(), payload_sha256=digest,
            updated_at=timezone.now(),
        ):
            return "busy"
        result = client.send(payload, f"kona-inbound/{email_id}")
        try:
            forwarded_id = UUID(result["id"])
        except (KeyError, TypeError, ValueError, AttributeError):
            # Sending may already have succeeded. Retry the same key and payload.
            raise ForwardingError("invalid_send_response") from None
        if not owned.update(
            status=InboundEmail.Status.FORWARDED, forwarded_id=forwarded_id,
            forwarded_at=timezone.now(), error_code="", lease_id=None,
            lease_until=None, updated_at=timezone.now(),
        ):
            return "busy"
        logger.info("Inbound email forwarded email_id=%s forwarded_id=%s", email_id, forwarded_id)
        return "forwarded"
    except (KeyError, TypeError, ValueError, AttributeError):
        error = ForwardingError("invalid_received_data", needs_review=True)
    except ForwardingError as exc:
        error = exc
    state = InboundEmail.Status.NEEDS_REVIEW if error.needs_review else InboundEmail.Status.PENDING
    owned.update(
        status=state, error_code=error.code, lease_id=None, lease_until=None,
        updated_at=timezone.now(),
    )
    logger.error("Inbound forwarding failed email_id=%s reason=%s", email_id, error.code)
    return "needs_review" if error.needs_review else "retry"
