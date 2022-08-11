from django.urls import path
from .views import HomePageView, AboutPageView

urlpatterns = [
    path("about/", AboutPageView.as_view(), name="about"),
    path("", HomePageView.as_view(), name="home"),
    # path("signup/", SignUpView.as_view(), name="signup"),
    # path("users/", UserPageView.as_view(), name="users"),
]