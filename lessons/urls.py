from django.urls import path
from lessons.views import CourseListView, CourseDetailView, ThanksPageView, CourseDetailView, RegisterLearner
# How is the line below different from the line above?
from lessons import views

urlpatterns = [
    path("course_list/", CourseListView.as_view(), name="course_list"),
    path("course_create/", views.course_create, name="course_create"),
    path("<int:pk>/", CourseDetailView.as_view(), name="course_detail"),
    path("course_create/thanks/", ThanksPageView.as_view(), name="thanks"),
    path("course_detail/<int:pk>", CourseDetailView.as_view(), name="course_detail"),
    # path("course_registration/<int:pk>", views.course_registration, name="course_registration"),
    path("course_registration/<int:pk>", RegisterLearner.as_view(), name="course_registration"),
    # path("profile/", LearnerListView.as_view(), name="learner_create")
    # path("profile/", LearnerListView.as_view(), name="profile")
    # experiment
    # path("", index)
]
