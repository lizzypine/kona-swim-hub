from django.test import SimpleTestCase, override_settings
from django.urls import reverse

class HomePageTests(SimpleTestCase):
    def test_url_exists_at_correct_location(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_url_available_by_name(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")

class AboutPageTests(SimpleTestCase):
    def test_url_exists_at_correct_location(self):
        response = self.client.get("/about/")
        self.assertEqual(response.status_code, 200)

    def test_url_available_by_name(self):
        response = self.client.get(reverse("about"))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("about"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "about.html")


class HealthCheckTests(SimpleTestCase):
    def test_lightsail_internal_health_probe_is_allowed(self):
        response = self.client.get(
            reverse("health_check"), HTTP_HOST="kona-swim-hub.service.local"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"ok")

    def test_ip_based_health_probe_is_allowed(self):
        for host in ("172.26.5.162:8000", "10.0.0.10:8000", "192.168.1.10"):
            with self.subTest(host=host):
                response = self.client.get(reverse("health_check"), HTTP_HOST=host)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.content, b"ok")

    def test_head_health_probe_is_allowed(self):
        response = self.client.head(reverse("health_check"), HTTP_HOST="172.26.5.162:8000")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"")

    @override_settings(SECURE_SSL_REDIRECT=True)
    def test_health_probe_does_not_require_https(self):
        response = self.client.get(reverse("health_check"), HTTP_HOST="172.26.5.162:8000")
        self.assertEqual(response.status_code, 200)

    def test_untrusted_host_is_rejected_outside_health_probe(self):
        for host in ("untrusted.example.com", "172.26.5.162:8000"):
            for path in ("/", "/accounts/login/", "/healthz/extra", "/healthz"):
                with self.subTest(host=host, path=path):
                    response = self.client.get(path, HTTP_HOST=host)
                    self.assertEqual(response.status_code, 400)

    def test_post_does_not_bypass_host_validation(self):
        response = self.client.post(reverse("health_check"), HTTP_HOST="172.26.5.162:8000")
        self.assertEqual(response.status_code, 400)

    def test_health_check_is_database_independent(self):
        response = self.client.get(reverse("health_check"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"ok")
