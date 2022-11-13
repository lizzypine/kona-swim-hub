from django.http import HttpResponseRedirect
from django.views.generic import ListView, DetailView, TemplateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from lessons.models import Course
from lessons.forms import CourseCreationForm, CourseRegistrationForm
from django.template.response import TemplateResponse
from django.shortcuts import get_object_or_404
# from django.urls import reverse
# from filters import AgeFilter

# Instructor status required to create a course.
@login_required
@user_passes_test(lambda user: user.is_instructor)
def course_create(request):

    # If this is a POST request then process the Form data
    if request.method == 'POST':
        
        # Create a form instance and populate it with data from the request (binding):
        form = CourseCreationForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # Hold the instance and attach the instructor to this course. 
            form.instance = form.save(commit=False)
            form.instance.course_instructor = request.user
            # Commit the data and redirect to the 'thanks' page. 
            form.instance.save()
            return HttpResponseRedirect('thanks/')

    else:
        form = CourseCreationForm() 

    # return render(request, 'lessons/course_new.html', {'form': form})
    return TemplateResponse(request, 'course_create.html', {'form': form})

class CourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'course_list.html'

    def get_course_list(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # age_filter = AgeFilter(request.GET)
        # return render(request, 'course_list.html', {'age_filter':age_filter})
        return context

class CourseDetailView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = 'course_detail.html'
    context_object_name = 'course'

@ login_required
def course_update(request, pk):

    context = {}

    obj = get_object_or_404(Course, pk = pk)

    form = CourseCreationForm(request.POST or None, instance = obj)

    # Check if the form is valid:
    if form.is_valid():

        # Commit the data and redirect to the 'my learners' page. 
        form.save()
        return HttpResponseRedirect('../../accounts/my-account')
    
    # Add form dictionary to context
    context['form'] = form

    return TemplateResponse(request, 'course-edit.html', context)

class CourseDeleteView(LoginRequiredMixin, DeleteView):
    model = Course
    template_name = 'course-delete.html'
    success_url = '../accounts/my-account'

class ThanksPageView(LoginRequiredMixin, TemplateView):
    template_name = 'thanks.html'

class RegisterLearner(LoginRequiredMixin, UpdateView):
    form_class = CourseRegistrationForm
    model = Course
    template_name = 'course_registration.html'
    success_url = '../../accounts/my-account'
    
    # Override get_form_kwargs method to pass the request object to the form class. 
    # This is necessary to display only the learners that are associated with the given user.
    def get_form_kwargs(self):
        kwargs = super(RegisterLearner, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


    def form_valid(self, form):
        instance = form.save(commit = False)
        learner = form.cleaned_data.get('learner')
        learner_on_roster = learner.id
        # Update linking table by adding learner to this course's roster.
        instance.learner_on_roster.add(learner_on_roster)

        # Update the number of spots that will be available after this learner registers.
        instance.num_spots_available = instance.num_spots_available - 1

        form.save_m2m()
        return super().form_valid(form)

    # Email the user a confirmation of this registration.
    # def send_email(self):
        # send email using the self.cleaned_data dictionary
        # pass





######CONSTRUCTION ZONE###########

# Revisit after creating functionality for instructors to create a waitlist.
# class JoinWaitlist(LoginRequiredMixin, UpdateView):
#     form_class = CourseRegistrationForm
#     model = Course
#     template_name = 'course_registration.html'
#     success_url = '../../accounts/my-account'
    
#     # Override get_form_kwargs method to pass the request object to the form class. 
#     # This is necessary to display only the learners that are associated with the given user.
#     def get_form_kwargs(self):
#         kwargs = super(RegisterLearner, self).get_form_kwargs()
#         kwargs['request'] = self.request
#         return kwargs

#     def form_valid(self, form):
#         instance = form.save(commit=False)

#         # Check that the learner is not already registered for this course.
#         # def clean_learner_data(self):
#         #   data = self.cleaned_data['learner']

#         #   if data == 
#         #   return data

#         # def save(self, commit=True):
#     #       inst = super(CourseRegistrationForm, self).save(commit=False)
#     #       inst.author = self._user
#     #       if commit:
#     #           inst.save()
#     #           self.save_m2m()
#         #       return inst

#   # def send_email(self):
#   #   # send email using the self.cleaned_data dictionary
#   #   pass

#         # Update linking table by adding learner to this course's roster.
#         learner=form.cleaned_data.get('learner')
#         learner_on_roster=learner.id
#         instance.learner_on_roster.add(learner_on_roster)

#         # Update the number of spots that will be available after this learner registers.
#         instance.num_spots_available = instance.num_spots_available - 1

        # form.save_m2m()
        # return super().form_valid(form)
