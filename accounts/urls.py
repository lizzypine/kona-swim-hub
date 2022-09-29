from django.urls import path
from accounts.views import SignUpView, UserPageView
from accounts import views
# from .forms import LearnerAddForm

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("users/", UserPageView.as_view(), name="users"),
    # path("profile/", UserChangeView.as_view(), name="profile")
    # path("profile/", LearnerListView.as_view(), name="profile")
    # path("profile/", views.learner_create, name="profile"),
    # path("profile/", views.learner_create, name="profile"),
    path("mylearners/", views.learners_list, name="mylearners"),
    path("learner-add/", views.learner_add, name="learner-add"),
    # path("course_create/thanks/", ThanksPageView.as_view(), name="thanks"),
]