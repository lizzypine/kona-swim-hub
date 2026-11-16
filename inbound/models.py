from django.db import models


class InboundEmail(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending retry"
        PROCESSING = "processing", "Processing"
        FORWARDED = "forwarded", "Accepted by Resend"
        IGNORED = "ignored", "Ignored"
        NEEDS_REVIEW = "needs_review", "Needs manual review"

    email_id = models.UUIDField(primary_key=True, editable=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    # Freeze routing across retries, without storing the original message body.
    forward_to = models.EmailField()
    forward_from = models.CharField(max_length=320)
    attempts = models.PositiveIntegerField(default=0)
    lease_id = models.UUIDField(null=True, editable=False)
    lease_until = models.DateTimeField(null=True, editable=False)
    first_send_at = models.DateTimeField(null=True, editable=False)
    payload_sha256 = models.CharField(max_length=64, blank=True, editable=False)
    forwarded_id = models.UUIDField(null=True, editable=False)
    forwarded_at = models.DateTimeField(null=True, editable=False)
    error_code = models.CharField(max_length=64, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.email_id)
