from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView
from pipes import Template
from django.shortcuts import render
from .models import CustomUser
from .forms import CustomUserCreationForm

# Create your views here.
class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"

class UserPageView(ListView):
    template_name = "users.html"
    model = CustomUser # New

# Create your views here.
# class SignUpView(CreateView):
#     form_class = UserCreationForm
#     success_url = reverse_lazy("login")
#     template_name = "registration/signup.html"

# class UserPageView(ListView):
#     template_name = "users.html"
#     model = CustomUser # New