"""Svix's documented HMAC-SHA256 format, using standard-library primitives."""

import base64
import binascii
import hashlib
import hmac
import time

from django.core.exceptions import ImproperlyConfigured


class InvalidSignature(Exception):
    pass


def verify_signature(body, headers, secret):
    if not secret or not secret.startswith("whsec_"):
        raise ImproperlyConfigured("Webhook signing secret is not configured")
    try:
        key = base64.b64decode(secret[6:], validate=True)
    except (ValueError, binascii.Error):
        raise ImproperlyConfigured("Webhook signing secret is malformed") from None
    if not key:
        raise ImproperlyConfigured("Webhook signing secret is malformed")

    message_id = headers.get("svix-id", "")
    timestamp = headers.get("svix-timestamp", "")
    signatures = headers.get("svix-signature", "")
    if not message_id or not timestamp.isascii() or not timestamp.isdecimal():
        raise InvalidSignature
    if len(message_id) > 256 or len(timestamp) > 12 or len(signatures) > 4096:
        raise InvalidSignature
    if abs(time.time() - int(timestamp)) > 300:
        raise InvalidSignature
    signed = f"{message_id}.{timestamp}.".encode() + body
    expected = base64.b64encode(hmac.new(key, signed, hashlib.sha256).digest()).decode()
    for entry in signatures.split():
        version, separator, signature = entry.partition(",")
        if version == "v1" and separator and signature.isascii():
            if hmac.compare_digest(signature, expected):
                return
    raise InvalidSignature
