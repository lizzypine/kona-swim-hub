from pipes import Template
from django.shortcuts import render
from django.views.generic import TemplateView
from django.views.generic import ListView
from .models import User

# Create your views here.
class HomePageView(TemplateView):
    template_name = "home.html"

class AboutPageView(TemplateView):
    template_name = "about.html"

class UserPageView(ListView):
    model = User
    template_name = "users.html"