from django.urls import path

from .views import resend_webhook


urlpatterns = [path("resend/", resend_webhook, name="resend_webhook")]
