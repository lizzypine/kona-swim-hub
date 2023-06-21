from django.urls import path
from lessons.views import (
    CourseListView,
    CourseDetailView,
    ThanksPageView,
    CourseDetailView,
    RegisterLearner,
    CourseDeleteView,
    JoinWaitlist,
    MoveWaitlistedToRoster,
)
from lessons import views

urlpatterns = [
    path("course_list/", CourseListView.as_view(), name="course_list"),
    path("course_create/", views.course_create, name="course_create"),
    path("<int:pk>/", CourseDetailView.as_view(), name="course_detail"),
    path("course_create/thanks/", ThanksPageView.as_view(), name="thanks"),
    path("course_detail/<int:pk>", CourseDetailView.as_view(), name="course_detail"),
    path("<int:pk>/course-edit", views.course_update, name="course-edit"),
    path("<pk>/course-delete", CourseDeleteView.as_view(), name="course-delete"),
    path(
        "course_registration/<pk>",
        RegisterLearner.as_view(),
        name="course_registration",
    ),
    path("course_waitlist/<pk>", JoinWaitlist.as_view(), name="waitlist"),
    path(
        "move_waitlisted_to_roster/<int:pk>/",
        MoveWaitlistedToRoster.as_view(),
        name="move_waitlisted_to_roster",
    ),
    path(
        "course/<int:pk1>/waitlist_confirm_removal/learner/<int:pk2>",
        views.waitlist_confirm_removal,
        name="waitlist_confirm_removal",
    ),
    # path('move_waitlisted_to_roster/<int:pk>/', MoveWaitlistedToRoster.as_view(), name='move_waitlisted_to_roster')
    # path('profile/', LearnerListView.as_view(), name='learner_create')
    # path('profile/', LearnerListView.as_view(), name='profile')
]
