# Kona Swim Hub agent instructions

## Project and layout

Kona Swim Hub is a Django app for families and swim instructors in Kona, Hawaii.
Deployment and CI use Python 3.11. Use `requirements.txt` and `Dockerfile` as the
sources of truth for runtime versions.

Work from the Git repository directory containing `manage.py`. Some local
workspaces have an outer directory with the same name; use this repository's
`.venv`, rather than an unrelated parent environment. Preserve existing local
changes and reuse the available environment before installing dependencies.

| Path | Purpose |
| --- | --- |
| `accounts/` | Custom user model, learners, authentication, contact and roster email forms. |
| `lessons/` | Courses, enrollment, waitlists, and instructor workflows. |
| `pages/` | Public pages and the database-independent health probe. |
| `inbound/` | Signed Resend webhooks and persistent forwarding state. |
| `kona-swim-hub/` | Django settings, root URLs, WSGI and ASGI entry points. |
| `templates/`, `static/` | Django/Bootstrap templates and application assets. |
| `.github/workflows/ci.yml` | Database tests, image checks, and the required merge check. |
| `infra/`, `docs/`, `scripts/` | Deployment reference, operational guides, and diagnostics. |

Follow existing Django patterns and keep changes scoped. Use `get_user_model()`
or the project's `CustomUser`, rather than assuming Django's default user model.
Create accounts through Django forms/managers so passwords are validated and
hashed; do not insert plaintext passwords directly into database rows. Logout
actions must use a CSRF-protected POST.

## Local validation

Run relevant regression tests for behavior changes, then the complete suite when
the change affects shared behavior. Documentation-only edits do not need a full
local test run. Use dummy settings and an isolated database:

```sh
(
  export PYTHON_DOTENV_DISABLED=1 SECRET_KEY=local-test-only DEBUG=False
  export DATABASE_URL=sqlite:///:memory:
  export EMAIL_BACKEND=django.core.mail.backends.locmem.EmailBackend
  ./.venv/bin/python manage.py check
  ./.venv/bin/python manage.py makemigrations --check --dry-run
  ./.venv/bin/python manage.py test --noinput
)
git diff --check
```

Use the same environment with test labels for focused checks, for example
`manage.py test accounts.test_logout inbound --noinput`. Tests must mock external
Resend and Turnstile calls; never use production databases or credentials for
tests. Include migrations for model changes and verify dependency changes in a
fresh image, since a local environment can hide missing or incompatible packages.
See [CI instructions](docs/ci.md) for image and PostgreSQL validation.

## Branches and CI

- Use topic branches for changes; normally target `develop` with feature PRs.
  Promote releases to `main` through a PR, following the user's requested scope.
- CI runs on PRs into `main` and `develop`, and on pushes to those branches. It
  tests SQLite and PostgreSQL and builds/smoke-tests a Linux/amd64 image.
- Keep the final check name **`Required CI`** stable. Protected `main` requires
  this check, an up-to-date PR, and enforcement for administrators. Do not bypass
  failing checks or weaken the final job's failure handling.
- Track every required source file, migration, template, and test. GitHub runners
  start from Git-tracked files; locally present untracked modules are unavailable.
- CI uses disposable services and dummy configuration. Keep production secrets
  and deployment credentials out of pull-request workflows.

## Runtime and deployment

The application runs on Lightsail Container Service `kona-swim-hub` in
`us-west-2`, using Neon PostgreSQL through `DATABASE_URL`. WhiteNoise serves
collected static files from the image. The existing AWS CLI profile is named
`eb-cli`; it is still used for Lightsail authentication. Legacy Beanstalk,
`RDS_*` fallback, and S3 runtime configuration have been removed.

- Build deployment images for **`linux/amd64`**. The public container is `web`,
  serving HTTP on port **8000** through Gunicorn.
- Preserve `/healthz/` as a fast, database-independent `ok` response. Its exact
  GET/HEAD path is handled before host validation because ELB probes use IP-based
  Host headers. Keep normal host validation on application routes.
- Health settings are path `/healthz/`, interval **30 seconds**, timeout **5
  seconds**, and success codes **`200-299`**. Do not count HTTP 400 as healthy.
  A healthy probe does not prove the database is reachable or migrated.
- Image startup does **not** run migrations. Apply required migrations separately
  against the same shared database used by Lightsail, within the user's authorized
  scope. A code change or image upload does not itself authorize production
  database writes, DNS/IAM changes, or a production deployment. Reuse existing
  task authorization rather than requesting it again.
- Copy the active deployment's runtime settings when creating a deployment. Use
  the exact image reference returned by the push command; uploading an image does
  not automatically select it for deployment.
- Runtime deployments are console-managed. `infra/kona_swim_hub_stack.py` is stale
  relative to production: do not run `cdk deploy` until it has been reconciled with
  the active image, environment, and public endpoint.

Use [the deployment guide](infra/README.md) for build/push commands and the local
Docker socket. Do not hardcode image version numbers into operational assumptions.

## Email and webhook invariants

- Outgoing SMTP and inbound forwarding are separate flows. Reuse the verified
  `DEFAULT_FROM_EMAIL` sending domain, `notifications.konaswimhub.com`, and keep
  `CONTACT_EMAIL` as the separate receiving inbox. An external sender must not
  become the outbound From address.
- Turnstile must pass before contact email is attempted. Log only safe verification
  metadata, never secrets or tokens. Password-reset confirmation alone does not
  prove a message was sent; use an active account with a usable password to test.
- `/webhooks/resend/` accepts POST events with a valid Svix signature over the raw
  body. Preserve timestamp checks, signature comparison, recipient filtering, and
  CSRF exemption only in combination with signature verification.
- Preserve database leases, the stable received-email idempotency key, frozen
  routing, and payload digest. Mark forwarded only after Resend accepts the send.
  Unresolved attempts stop after 23 hours, inside the provider's 24-hour key
  retention window. Reconcile provider history before resetting ambiguous state.
- Keep inbound HTML as safe plain text, retain attachment bounds, and never copy
  original authentication headers or fetch arbitrary URLs from message content.
- Loop protection ignores the configured destination and its Gmail dot/plus
  aliases, the app sender, the receiving address, and the forwarding marker. Use
  a separate mailbox and a new message for end-to-end tests; ignored IDs stay
  ignored on replay.

See [inbound forwarding operations](docs/resend-inbound-forwarding.md) for
configuration, migrations, webhook setup, limits, and troubleshooting.

## Secrets and diagnostics

Never commit or print API keys, passwords, database URLs, webhook secrets,
Turnstile tokens, or personal forwarding destinations. Use private runtime
configuration and hidden terminal prompts. Keep `.env*` and local deployment
metadata excluded from images and credentials out of Git.

For AWS inspection, use explicit `--query` projections for non-secret fields or
presence booleans. Never print full service/deployment JSON containing environment
values. Log identifiers and fixed error codes instead of email contents, request
headers, signed download URLs, or raw exceptions that may contain private data.

`scripts/check_inbound_database.py` checks schema and permissions using a read-only
transaction and a hidden database-URL prompt. Treat local handoff notes as
historical context; verify current code and sanitized runtime metadata before
assuming an old diagnosis or deployment is still current.
