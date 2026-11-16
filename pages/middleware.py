from .views import health_check


class HealthCheckMiddleware:
    """Answer liveness probes before middleware validates their IP-based Host."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only this fixed, database-independent response bypasses host validation.
        # ELB health checks may use changing IP addresses rather than our domain.
        if request.path_info == "/healthz/" and request.method in ("GET", "HEAD"):
            return health_check(request)
        return self.get_response(request)
