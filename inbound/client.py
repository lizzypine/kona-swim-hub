"""Small, bounded Resend HTTP client; never exposes response/error contents."""

import json
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


MAX_RESPONSE_BYTES = 2 * 1024 * 1024
MAX_ATTACHMENT_BYTES = 5 * 1024 * 1024


class ForwardingError(Exception):
    def __init__(self, code, *, needs_review=False):
        self.code = code
        self.needs_review = needs_review
        super().__init__(code)


def encode_payload(payload):
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


class ResendClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.deadline = time.monotonic() + 40
        self.opener = build_opener(NoRedirect())

    def _read(self, request, limit):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise ForwardingError("time_budget_exceeded")
        try:
            with self.opener.open(request, timeout=min(8, remaining)) as response:
                content = response.read(limit + 1)
        except HTTPError as exc:
            code = exc.code
            exc.close()
            raise ForwardingError(f"http_{code}") from None
        except (OSError, URLError, ValueError):
            raise ForwardingError("transport_error") from None
        if len(content) > limit:
            raise ForwardingError("size_limit_exceeded", needs_review=True)
        return content

    def _json(self, method, path, payload=None, idempotency_key=None):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "KonaSwimHub-Inbound/1.0",
        }
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        request = Request(
            "https://api.resend.com" + path,
            data=encode_payload(payload) if payload is not None else None,
            headers=headers, method=method,
        )
        try:
            result = json.loads(self._read(request, MAX_RESPONSE_BYTES))
        except (ValueError, UnicodeError):
            raise ForwardingError("invalid_api_response") from None
        if not isinstance(result, dict):
            raise ForwardingError("invalid_api_response")
        return result

    def get_received(self, email_id):
        return self._json("GET", f"/emails/receiving/{email_id}?html_format=cid")

    def get_attachment(self, email_id, attachment_id):
        return self._json("GET", f"/emails/receiving/{email_id}/attachments/{attachment_id}")

    def download_attachment(self, url):
        # Only Resend's documented receiving CDN, never a URL from message HTML.
        try:
            parts = urlsplit(url)
            allowed = (
                parts.scheme == "https" and parts.hostname == "inbound-cdn.resend.com"
                and parts.port in (None, 443) and not parts.username
                and not parts.password and not parts.fragment
            )
        except (TypeError, ValueError):
            allowed = False
        if not allowed:
            raise ForwardingError("unsafe_attachment_url", needs_review=True)
        # Deliberately omit API credentials; redirects are disabled.
        return self._read(Request(url), MAX_ATTACHMENT_BYTES)

    def send(self, payload, idempotency_key):
        return self._json("POST", "/emails", payload, idempotency_key)
