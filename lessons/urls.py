from django.urls import path
from .views import HomePageView, AboutPageView, UserPageView

urlpatterns = [
    path("about/", AboutPageView.as_view(), name="about"),
    path("", HomePageView.as_view(), name="home"),
    path("users/", UserPageView.as_view(), name="users"),
]