# Resend inbound forwarding

`POST https://konaswimhub.com/webhooks/resend/` forwards mail received at
`team@ilkaxle.resend.app` to the private address in `EMAIL_FORWARD_TO`. No DNS
changes are needed for that existing Resend receiving address.

The `inbound` Django app is independent of outgoing SMTP. Existing contact,
registration, course, and password-reset emails keep their current behavior.
No new Python dependencies are needed.

## Configuration

Settings follow the existing `os.getenv`/environs conventions. Docker Compose
loads `.env.docker`; Lightsail injects the container's environment variables.
Runtime environment values take precedence over local dotenv files. Environment
files are excluded from the image, so configure production in Lightsail, not in
source files. `.env.docker.example` contains blank placeholders, not credentials
or a personal destination address.

| Variable | Value to configure privately |
| --- | --- |
| `RESEND_API_KEY` | Resend API key with **Full access**, from the same account/team that receives the inbound messages. |
| `EMAIL_FORWARD_TO` | One Gmail email address, not a comma-separated list. No default is provided. |
| `RESEND_WEBHOOK_SECRET` | The `whsec_...` signing secret for this specific webhook endpoint. |
| `RESEND_INBOUND_ADDRESS` | Optional; defaults to the tested `team@ilkaxle.resend.app`. Only messages addressed to this inbox are forwarded. |
| `DEFAULT_FROM_EMAIL` | Existing setting, reused unchanged: `Kona Swim Hub <team@notifications.konaswimhub.com>`. It must use your verified sending domain. |

If `RESEND_API_KEY` is unset and `EMAIL_HOST=smtp.resend.com`, the app reuses
`EMAIL_HOST_PASSWORD` as the API key. A sending-only key cannot retrieve received
emails; in that case configure a separate Full access `RESEND_API_KEY` and leave
the existing SMTP credentials untouched. A webhook signing secret is different
from an API key. Do not paste either into chat, shell command arguments, or Git.

Missing or invalid forwarding configuration returns HTTP 503, rather than
disabling signature verification or guessing a destination. Signed unrelated
event types are acknowledged without requiring the API key/destination.

## How forwarding works

1. Verify the raw body using the documented Svix HMAC-SHA256 format and
   `svix-id`, `svix-timestamp`, and `svix-signature`. Signatures use constant-time
   comparison and a five-minute past/future timestamp tolerance. Only `v1`
   signatures are accepted; multiple signatures support signing-key rotation.
2. Accept `email.received` and a UUID received-email ID; ignore other events and
   recipients. Recheck the ID and recipient after retrieving the full message
   from `GET /emails/receiving/{id}?html_format=cid`.
3. Claim a two-minute database lease using an atomic conditional update. A
   concurrent delivery returns 503 so Resend can retry. API work has a 40-second
   budget and each HTTP call times out after at most eight seconds.
4. Send with the existing verified `DEFAULT_FROM_EMAIL`, a `Fwd:` subject, the
   original sender as Reply-To, and only the configured destination. Original
   display names are retained when their address matches the original sender.
   Sender details are explicitly labeled unverified. Original To/CC/BCC,
   Reply-To, authentication results, and other headers are never copied onto
   the outgoing message.
5. Prefer the original plain text. For HTML-only messages, BeautifulSoup removes
   scripts/styles and converts the content to plain text. HTML formatting and
   embedded layout are intentionally not retained, and remote images are not
   fetched. The app never renders an incoming email as a webpage.
6. Retrieve attachment metadata through the Receiving API, download bytes from
   the documented `https://inbound-cdn.resend.com` host, and send base64 content.
   API credentials are never sent to the download host and redirects are
   disabled. Refreshed signed download URLs are not included in outgoing payloads.
7. POST to `/emails` with `Idempotency-Key: kona-inbound/{received-email-id}`.
   Only after Resend returns an outgoing email ID is the row marked forwarded.
   This means **accepted by Resend**, not guaranteed delivered to Gmail.

Messages originating from the forwarding destination, our sending address, or
our receiving address are ignored. Gmail dot/plus/Googlemail aliases are treated
as the same mailbox for loop detection. Our own forwarding marker is also
ignored on inbound mail; outbound forwards add that marker and
`Auto-Submitted: auto-generated`. Do not configure Gmail to forward these
messages back to the receiving address.

## Reliability and limits

`InboundEmail` has a unique received-email ID and persistent processing status.
The lease prevents overlapping workers from sending the same message. A stale
lease can be reclaimed after two minutes without holding a database transaction
open across network calls. The view explicitly opts out of `ATOMIC_REQUESTS` so
the send boundary is committed before contacting Resend.

The first send-attempt timestamp and a SHA-256 digest of the exact outgoing
payload are saved before sending. API timeouts or a database failure after a
successful send can then retry the same key/payload. Sender and destination are
frozen in the row, so routing changes apply to new messages, not partially
processed ones. A changed payload requires manual review instead of sending
different content under the same key.

Resend retains idempotency keys for 24 hours. Unresolved attempts stop sending
after **23 hours**, before that protection expires, and enter `needs_review`.
Inspect the Resend send history before an operator changes such a row. Never
blindly clear `first_send_at`, delete processing records, or generate a new key
to retry an ambiguous send. Database loss, manual resets, or independent external
forwarders can still cause duplicates; this is not an absolute exactly-once
delivery guarantee. Keep the records as deduplication tombstones and back them
up with the application database.

Limits: 256 KiB webhook body, 2 MiB JSON API response, ten attachments, 5 MiB per
attachment, 10 MiB total downloaded attachment content, and 20 MiB outgoing JSON.
Oversized messages, unsafe attachment URLs, changed payloads, and invalid
received data enter `needs_review` without sending a partial message. Resend may
also reject attachment types under its own policy. CDN host changes require a
reviewed allowlist update; arbitrary attachment hosts are not allowed.

| Response | Meaning |
| --- | --- |
| 200 | Forward accepted, previously completed, or intentionally ignored. |
| 400 | Invalid/missing signature, expired signature, or malformed event. |
| 405 | Request method is not POST. |
| 413 | Webhook body exceeds the size limit. |
| 503 + `Retry-After: 30` | Configuration/database/API failure, another worker processing the ID, or manual review needed. |

Temporary failures are retried by Resend. Persistent failures/manual-review rows
need operator attention; repeated failures can cause Resend to disable a webhook.
Once fixed, re-enable it and replay the affected message in Resend. A replay of a
forwarded/ignored ID is a no-op. A `needs_review` row deliberately remains stopped.

Logs contain IDs and fixed result/error codes, not email bodies, subjects,
addresses, API errors, download URLs, or credentials. The read-only Django admin
view shows status, attempt counts, reason codes, and outgoing IDs. The database
also retains the configured sender/destination for reliable retries, but does
not store original message bodies or attachments. There is no background queue;
a webhook timeout may occur while processing attachments, but database leases
and the send key protect the subsequent delivery attempt.

## Lightsail deployment (manual)

No production resource, DNS record, credential, webhook, or database has been
changed by this implementation. The following commands are for the operator.

1. Build from the repository directory (Docker Desktop running):

   ```sh
   export DOCKER_HOST=unix:///Users/elizabethpine/.docker/run/docker.sock
   docker build --platform linux/amd64 -t kona-swim-hub:inbound .
   ```

2. Apply the new `inbound.0001_initial` migration to the **same shared database
   used by Lightsail**, before deploying the new application image. It adds one
   independent table; existing application tables are unchanged. Use the current
   production `DATABASE_URL` copied privately from its existing configuration.
   This one-off command prompts for it without saving it in shell history:

   ```sh
   docker run --rm -it --platform linux/amd64 kona-swim-hub:inbound python -c '
   import os
   from getpass import getpass
   os.environ["DATABASE_URL"] = getpass("Production DATABASE_URL: ")
   os.environ["SECRET_KEY"] = "inbound-migration-only"
   os.environ["DEBUG"] = "False"
   os.environ["PYTHON_DOTENV_DISABLED"] = "1"
   os.environ["DJANGO_SETTINGS_MODULE"] = "kona-swim-hub.settings"
   import django
   django.setup()
   from django.core.management import call_command
   call_command("migrate", "inbound", interactive=False)
   call_command("showmigrations", "inbound")
   '
   ```

   Expect `[X] 0001_initial`. Container startup does not run migrations. Use the
   shared production PostgreSQL database, not a container-local SQLite file.
   Ongoing deduplication requires the same durable database across deployments.

3. Push the image:

   ```sh
   aws lightsail push-container-image \
     --region us-west-2 --service-name kona-swim-hub --profile eb-cli \
     --label inbound --image kona-swim-hub:inbound
   ```

4. In Lightsail → Containers → `kona-swim-hub` → Deployments → Create deployment,
   copy the active deployment's settings. Replace `web`'s image with the **exact
   image reference printed by the push command**. Preserve SMTP, Turnstile,
   database, host, port, and health settings. Add `RESEND_API_KEY` and your private
   `EMAIL_FORWARD_TO`. Keep `RESEND_INBOUND_ADDRESS` at its default unless needed.
   Keep `/healthz/`, `web:8000`, interval 30, timeout 5, and success `200-299`.
   Save/deploy and wait for Active. Do not use the stale CDK deployment template.

5. If the webhook does not yet exist, leave `RESEND_WEBHOOK_SECRET` unset during
   that initial deployment. Forwarding returns 503 until the real secret is
   configured; existing outgoing email and health checks still work. Configure
   the webhook as below, then create another Lightsail deployment of the **same
   image**, adding `RESEND_WEBHOOK_SECRET` while preserving the other variables.
   An existing webhook can keep its current signing secret across image updates.

## Create the webhook in Resend

1. In the Resend account/team receiving `team@ilkaxle.resend.app`, open
   **Webhooks → Add Webhook**.
2. Set the endpoint to **`https://konaswimhub.com/webhooks/resend/`**, including
   the trailing slash. Choose only the **`email.received`** event and click Add.
3. Open that webhook's details and copy its signing secret (`whsec_...`) directly
   into the Lightsail `RESEND_WEBHOOK_SECRET` variable as described above.
4. After the secret-bearing deployment becomes Active, leave/enable the webhook.
   Requests received between creating the webhook and configuring the secret
   return 503 and can be retried/replayed. Never enable an unsigned bypass.

## End-to-end test

1. From a **different mailbox than `EMAIL_FORWARD_TO`**, email
   **`team@ilkaxle.resend.app`** with a unique subject and a short body. Include a
   small attachment to exercise attachment forwarding. A message sent from the
   configured Gmail destination (including its aliases) is deliberately ignored
   as a loop; do not use that address as the test sender.
2. Confirm it appears in Resend's **Emails → Receiving** tab and note its ID.
3. In **Webhooks → your endpoint → message deliveries**, confirm a 200 response.
   The row should be `forwarded`; the container log has
   `Inbound email forwarded email_id=... forwarded_id=...`.
4. Check Resend's Sending activity and your configured Gmail inbox/spam folder.
   Confirm the verified app sender, `Fwd:` subject, original sender in the body,
   original sender as Reply-To, and attachment contents. Reply should target the
   original sender. No website or receiving-domain DNS changes are required.
5. Replay the same webhook message once. It should return 200 without creating
   another outgoing message. Try a separate message from the configured Gmail
   destination to confirm it is ignored.

An older received email does not automatically trigger this endpoint merely
because the webhook was added. Use its existing webhook delivery's Replay action
if available, or send a new test message after setup.

## Automated validation

### Diagnosing `Inbound forwarding database unavailable`

This log means a database operation failed after webhook authentication and
configuration validation. It does not distinguish a missing migration from a
connection/permission problem. `/healthz/` deliberately does not query the
database, so healthy probes do not establish database readiness.

From the repository directory, run this read-only diagnostic using the existing
project interpreter (no rebuild or production deployment needed):

```sh
./.venv/bin/python scripts/check_inbound_database.py
```

Paste the **current Lightsail `DATABASE_URL`** only into its hidden prompt. The
script uses a read-only PostgreSQL transaction to check migration history,
table existence, and SELECT/INSERT/UPDATE privileges without reading email
contents or changing data. Output contains status lines or a SQLSTATE code,
never connection strings or raw exception details. A successful check from your
Mac does not establish that Lightsail has identical network access.

If the migration and table are missing, apply `inbound.0001_initial` using step 2
of the deployment instructions above. If the migration is recorded but the
table is missing, or permissions are missing, review the database/schema/role
instead of faking or resetting migrations. After resolving the issue, open
Resend → Webhooks → this endpoint → the failed message and click Replay. The
original 503 delivery is retryable; do not create a different received-email ID.

### Running the suite

```sh
PYTHON_DOTENV_DISABLED=1 SECRET_KEY=local-test-only \
DATABASE_URL=sqlite:///:memory: DEBUG=False \
./.venv/bin/python manage.py test --noinput
```

All external API calls are mocked; these tests send no real messages. Tests cover
the official Svix signature vector, raw-body integrity, signature rotation and
timestamps, CSRF-exempt POST authentication, routing, successful forwarding,
duplicate IDs, simultaneous deliveries using separate database connections,
stale leases, ambiguous sends, loss of the final database update, API errors,
malformed input, missing configuration, safe text conversion, attachments,
limits, loop prevention, and unchanged outgoing email behavior. The concurrency
test runs on the selected test database; use a separate disposable PostgreSQL
test database if validating PostgreSQL locally, never the production database.

Validation result for this implementation: **90 tests passed** in the existing
Python 3.10 environment and in the Python 3.11 Linux/amd64 Docker image using
in-memory SQLite. Django system checks, migration consistency checks, and
whitespace checks passed. Container validation ran without network access and
verified that no `.env*` files were included. PostgreSQL integration and live
Resend/Gmail delivery were not exercised; perform the end-to-end test after your
manual deployment. At the user's request, the final `kona-swim-hub:inbound` image
was rebuilt, retested, and uploaded to Lightsail as **`:kona-swim-hub.inbound.8`**
(manifest digest `sha256:793c4e57699bdefd2181462372427f0fe1b7559c935b4296309b90a6ea3b4c84`).
It has not been deployed. The production migration, runtime variables, and
Resend webhook setup above still need to be completed by the operator.

## API references

- [Webhook verification](https://resend.com/docs/webhooks/verify-webhooks-requests)
- [Svix signature format](https://docs.svix.com/receiving/verifying-payloads/how-manual)
- [Received event](https://resend.com/docs/webhooks/emails/received)
- [Retrieve received email](https://resend.com/docs/api-reference/emails/retrieve-received-email)
- [Receiving attachments](https://resend.com/docs/dashboard/receiving/attachments)
- [Attachment metadata and CDN URL](https://resend.com/docs/api-reference/emails/retrieve-received-email-attachment)
- [Sending API](https://resend.com/docs/api-reference/emails/send-email)
- [24-hour idempotency window](https://resend.com/docs/dashboard/emails/idempotency-keys)
- [Webhook setup](https://resend.com/docs/dashboard/receiving/create-receiving-webhook)
- [Retries and manual replay](https://resend.com/docs/webhooks/retries-and-replays)
