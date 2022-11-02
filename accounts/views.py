from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DetailView, DeleteView
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

# My Account Page
@login_required
def my_account_view (request):

    learners = Learner.objects.filter(associated_with_user=request.user)

    # Create a dictionary where the key is the learner id and the value is the list of courses this learner is enrolled in.
    learner_courses = dict.fromkeys(learners)

    # Get the list of courses that each learner is enrolled in.
    for learner in learners:
        course_list = Course.objects.filter(learner_on_roster=learner).values('course_title', 'course_instructor_id__first_name', 'course_description', 
        'course_age_range_min', 'course_age_range_max', 'course_location', 'course_start_date', 'course_end_date', 'course_start_time', 'course_end_time')
        learner_courses[learner] = course_list
        
    
    courses = Course.objects.filter(course_instructor=request.user)

    # Create a dictionary where the key is the course id and the value is the list of names on the roster for that course.
    rosters = dict.fromkeys(courses)

    # Get the roster of learners for each course.
    for course in courses:
        roster = Learner.objects.filter(learners=course).values('first_name', 'last_name')
        rosters[course] = roster

    context = {
        "learners": learners,
        "learner_courses": learner_courses,
        "courses": courses,
        "rosters": rosters
    }

    return render(request, "my-account.html", context)

# Learner detail page
class LearnerDetailView(LoginRequiredMixin, DetailView):
    model = Learner
    template_name = 'learner-detail.html'
    context_object_name = 'learner'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Filters courses to those that have this learner on the roster
        context['courselist'] = Course.objects.filter(learner_on_roster=self.kwargs['pk']).values('course_title')
        return context

# Add a learner page
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

            return HttpResponseRedirect('../my-account')
            
    else:
        form = LearnerAddForm()

    return TemplateResponse(request, "learner-add.html", {'form': form})

# Update a learner page
@ login_required
def learner_update(request, pk):

    context = {}

    obj = get_object_or_404(Learner, pk = pk)

    form = LearnerAddForm(request.POST or None, instance = obj)

    # Check if the form is valid:
    if form.is_valid():

        # Commit the data and redirect to the 'my learners' page. 
        form.save()
        return HttpResponseRedirect('../mylearners')
    
    # Add form dictionary to context
    context['form'] = form

    return TemplateResponse(request, "learner-update.html", context)

# Learner delete 
class LearnerDeleteView(LoginRequiredMixin, DeleteView):
    model = Learner
    template_name = 'learner_confirm_delete.html'
    success_url = '../../my-account'

# class LearnerUpdateView(LoginRequiredMixin, UpdateView):
#     model = Learner
#     template_name = 'learner-update.html'
#     context_object_name = 'learner'
#     # fields = ('first_name', 'last_name', 'birthday')
#     fields = '__all__'
#     exclude = ['associated_with_user']
#     form_class: LearnerAddForm
#     success_url = '../../accounts/mylearners'

    # widgets = {
    #   'birthday': DatePickerInput(),
    # }

# Create your views here.
# class SignUpView(CreateView):
#     form_class = UserCreationForm
#     success_url = reverse_lazy("login")
#     template_name = "registration/signup.html"

# class UserPageView(ListView):
#     template_name = "users.html"
#     model = CustomUser # New