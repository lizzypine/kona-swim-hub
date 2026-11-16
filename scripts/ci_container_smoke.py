"""Check the built deployment image without network access or a real database."""

import os
from pathlib import Path
import subprocess
import sys


def main():
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    subprocess.run([sys.executable, "-m", "pip", "check"], check=True)
    assert not list(Path("/app").rglob(".env*")), "Environment file included in image"
    assert not Path("/app/.elasticbeanstalk").exists(), "Legacy deployment metadata included"

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kona-swim-hub.settings")
    import django
    django.setup()
    from django.test import Client

    client = Client()
    health = client.get("/healthz/", HTTP_HOST="172.26.5.162:8000")
    assert health.status_code == 200 and health.content == b"ok", "Health probe failed"

    stylesheet = client.get("/static/css/base.css", HTTP_HOST="localhost")
    assert stylesheet.status_code == 200, "Collected stylesheet was not served"
    assert stylesheet["Content-Type"].startswith("text/css"), "Incorrect stylesheet type"
    stylesheet.close()

    webhook = client.get("/webhooks/resend/", HTTP_HOST="localhost")
    assert webhook.status_code == 405, "Webhook route did not load with POST-only access"
    print("Container dependency, packaging, health, static-asset, and routing checks passed.")


if __name__ == "__main__":
    main()
