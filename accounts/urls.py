from django.urls import path
from .views import SignUpView, UserPageView

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("users/", UserPageView.as_view(), name="users")
]