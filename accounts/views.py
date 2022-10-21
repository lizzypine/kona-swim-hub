from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DetailView
from accounts.models import CustomUser, Learner
from lessons.models import Course
from accounts.forms import CustomUserCreationForm, CustomUserChangeForm, LearnerAddForm
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse

class ProfileUpdateView(DetailView):
    model = Learner
    template_name = 'course_detail.html'
    context_object_name = 'course'

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"

class UserPageView(ListView):
    template_name = "users.html"
    model = CustomUser # New

class UserChangeView(CreateView):
    form_class = CustomUserChangeForm
    success_url = reverse_lazy("profile")
    template_name = "profile.html"

# My Learners page
@login_required
def learners_list(request):

    learners = Learner.objects.filter(associated_with_user=request.user)

    context = {
        "learners": learners,
    }

    return render(request, "mylearners.html", context)

# Learner detail page
class LearnerDetailView(LoginRequiredMixin, DetailView):
    model = Learner
    template_name = 'learner-detail.html'
    context_object_name = 'learner'
    # queryset = Course.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Filters courses to where this learner is on the roster
        context['courselist'] = Course.objects.filter(learner_on_roster=self.kwargs['pk']).values('course_title')
        return context

@login_required
def learner_add(request):
    
    # If this is a POST request then process the Form data
    if request.method == "POST":

        # Create a form instance and populate it with data from the request (binding data to the form):
        form = LearnerAddForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # Hold the instance and attach the user to this learner.
            form.instance = form.save(commit=False)
            form.instance.associated_with_user = request.user

            # Commit the data and redirect to the 'my learners' page. 
            form.instance.save()

            return HttpResponseRedirect('../mylearners')
            
    else:
        form = LearnerAddForm()

    return TemplateResponse(request, "learner-add.html", {'form': form})


        # if 'preview' in request.POST:
        #     # do preview thing...
    
    # return TemplateResponse(request, "learner-add.html", {'form': form})


    #I want to import my LearnerAddForm into this LearnerListView
    # def learner_add(request):

    #     # If this is a POST request then process the Form data
    #     if request.method == "POST":
            
    #         # Create a form instance and populate it with data from the request (binding):
    #         form = LearnerAddForm(request.POST)

    #         # Check if the form is valid:
    #         if form.is_valid():
    #             # Process the data and redirect to the 'my learners' page. 
    #             form.save()
    #             return HttpResponseRedirect('/mylearners/')

    #         # Save a new learner object from the form's data.
    #         # KEEP THIS?
            
        
    #     # Else, this is a GET request (or any other method). Create the default form.
    #     else:
    #         form = LearnerAddForm()

    #     # return render(request, 'lessons/course_new.html', {'form': form})
    #     return render(request, 'mylearners.html', {'form': form})

class LearnerUpdateView(LoginRequiredMixin, CreateView):
    model = Learner
    template_name = 'learner-update.html'
    context_object_name = 'learner'
    form_class = LearnerAddForm
    # fields = '__all__'
    success_url = '../../accounts/mylearners'

# Create your views here.
# class SignUpView(CreateView):
#     form_class = UserCreationForm
#     success_url = reverse_lazy("login")
#     template_name = "registration/signup.html"

# class UserPageView(ListView):
#     template_name = "users.html"
#     model = CustomUser # New