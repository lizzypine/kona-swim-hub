from django.urls import path
from accounts.views import SignUpView, LearnerDetailView, RegisterThanksPageView, contactView, ContactThanksPageView, ContactInstructorThanks
from accounts import views

urlpatterns = [
    path('register/', SignUpView.as_view(), name='register'),
    path('register_thanks/', RegisterThanksPageView.as_view(), name='register_thanks'),
    path('learner-add/', views.learner_add, name='learner-add'),
    path('learner-detail/<int:pk>', LearnerDetailView.as_view(), name='learner-detail'),
    path('learner-update/<int:pk>', views.learner_update, name='learner-update'),
    path('<int:id>/delete/', views.learner_delete, name='learner-delete'),
    path("my-account/", views.my_account_view, name="my-account"),
    path("contact/", contactView, name="contact"),
    path('contact/contact_thanks/', ContactThanksPageView.as_view(), name='contact_thanks'),
    path('contact_instructor/<int:pk>', views.contact_instructor, name='contact_instructor'),
    path('thanks/', ContactInstructorThanks.as_view(), name='contact_instructor_thanks'),
    path('contact_learners/<int:pk>', views.contact_learners, name='contact_learners'),
    path('contact_waitlist/<int:pk>', views.contact_waitlist, name='contact_waitlist'),
]