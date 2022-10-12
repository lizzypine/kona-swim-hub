from django.urls import path
from accounts.views import SignUpView, UserPageView, LearnerDetailView
from accounts import views

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("users/", UserPageView.as_view(), name="users"),
    # path("profile/", UserChangeView.as_view(), name="profile")
    # path("profile/", LearnerListView.as_view(), name="profile")
    # path("profile/", views.learner_create, name="profile"),
    # path("profile/", views.learner_create, name="profile"),
    path("mylearners/", views.learners_list, name="mylearners"),
    path("learner-add/", views.learner_add, name="learner-add"),
    path("learner-detail/<int:pk>", LearnerDetailView.as_view(), name="learner-detail"),
    # path("course_detail/<int:pk>", CourseDetailView.as_view(), name="course_detail"),
    # path("course_create/thanks/", ThanksPageView.as_view(), name="thanks"),
]