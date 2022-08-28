from django.urls import path
from .views import CourseListView, CourseDetailView, ThanksPageView
# How is the line below different from the line above?
from . import views

urlpatterns = [
    path("course_list/", CourseListView.as_view(), name="course_list"),
    path("course_create/", views.course_create, name="course_create"),
    path("<int:pk>/", CourseDetailView.as_view(), name="course_detail"),
    path("course_create/thanks/", ThanksPageView.as_view(), name="thanks"),
]
