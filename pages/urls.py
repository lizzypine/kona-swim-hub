from django.urls import path
from pages.views import HomePageView, AboutPageView, health_check
from accounts import views

urlpatterns = [
    path("healthz/", health_check, name="health_check"),
    path("about/", AboutPageView.as_view(), name="about"),
    # path("signup/", views.user_register, name="signup"),
    path("", HomePageView.as_view(), name="home"),
]