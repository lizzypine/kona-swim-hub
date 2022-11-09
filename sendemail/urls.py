from django.urls import path

from sendemail.views import contactView, ContactThanksPageView

urlpatterns = [
    path("contact/", contactView, name="contact"),
    path('contact/contact_thanks/', ContactThanksPageView.as_view(), name='contact_thanks')
]