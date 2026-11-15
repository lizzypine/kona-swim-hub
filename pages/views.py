from django.http import HttpResponse
from django.views.generic import TemplateView


def health_check(request):
    return HttpResponse("ok", content_type="text/plain")


class HomePageView(TemplateView):
    template_name = "home.html"

class AboutPageView(TemplateView):
    template_name = "about.html"

