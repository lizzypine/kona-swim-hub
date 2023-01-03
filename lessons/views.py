from django.http import HttpResponseRedirect
from django.views.generic import ListView, DetailView, TemplateView, UpdateView, DeleteView, CreateView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin, messages
from lessons.models import Course
from accounts.models import Learner
from lessons.forms import CourseCreationForm, CourseRegistrationForm, JoinWaitlistForm, MoveWaitlistedToRosterForm
from django.template.response import TemplateResponse
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.http import HttpResponseRedirect
from django.core.mail import send_mail, EmailMessage, BadHeaderError
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponseRedirect, HttpResponse

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

    return TemplateResponse(request, 'course_create.html', {'form': form})

class CourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'course_list.html'

    def get_course_list(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class CourseDetailView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = 'course_detail.html'
    context_object_name = 'course'

class RegisterLearner(LoginRequiredMixin, UpdateView):
    form_class = CourseRegistrationForm
    model = Course
    template_name = 'course_registration.html'
    success_url = '../../accounts/my-account'
    
    # Override get_form_kwargs method to pass the request object to the form class. 
    def get_form_kwargs(self):
        kwargs = super(RegisterLearner, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        instance = form.save(commit = False)

        # Save the many-to-many relationship.
        form.save_m2m()

        learner = form.cleaned_data.get('learner')
        learner_on_roster = learner.id
        # Update linking table by adding learner to this course's roster.
        instance.learner_on_roster.add(learner_on_roster)

        # Update the number of spots that will be available after this learner registers.
        instance.num_spots_available = instance.num_spots_available - 1

        # Send a confirmation email to user
        user = self.request.user.first_name
        course_title = instance.course_title
        instructor = instance.course_instructor
        subject = 'You signed up for swim lessons through Kona Swim Hub'
        html_template = 'emails/course_registration_success_email_family.html'
        html_message = render_to_string(html_template, {"user": user, "learner": learner, "course": course_title})
        email_from = 'Kona Swim Hub <team@konaswimhub.com>'
        recipient_list = [(self.request.user.email)]
        send_mail(subject, html_message, email_from, recipient_list, fail_silently=False)

        # Send a confirmation email to instructor
        html_template = 'emails/course_registration_success_email_instructor.html'
        html_message = render_to_string(html_template, {"instructor": instructor, "learner": learner, "course": course_title})
        subject = 'A student signed up for your course through Kona Swim Hub'

        email_from = settings.DEFAULT_FROM_EMAIL
        recipient_list = [(instance.course_instructor.email)]
        send_mail(subject, html_message, email_from, recipient_list, fail_silently=False)

        return super().form_valid(form)

class JoinWaitlist(LoginRequiredMixin, UpdateView):
    form_class = JoinWaitlistForm
    model = Course
    template_name = 'course_waitlist.html'
    success_url = '../../accounts/my-account'
    
    # Override get_form_kwargs method to pass the request object to the form class. 
    def get_form_kwargs(self):
        kwargs = super(JoinWaitlist, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        form.instance = form.save(commit=False)
        instance = form.save(commit = False)

        # Save the many-to-many relationship.
        form.save_m2m()

        learner = form.cleaned_data.get('learner')
        learner_on_waitlist = learner.id

        # Update linking table by adding learner to this course's roster.
        instance.learner_on_waitlist.add(learner_on_waitlist)

        return super().form_valid(form)

@ login_required
def waitlist_confirm_removal(request, pk1, pk2):

    context = {}
    course = get_object_or_404(Course, id=pk1)
    learner_on_waitlist = get_object_or_404(Learner, id=pk2)

    # Add form dictionary to context
    context['course'] = course
    context['learner'] = learner_on_waitlist

    # Check if the form is valid:
    if request.method == 'POST':

        # remove_learner_from_waitlist()
        course.learner_on_waitlist.remove(learner_on_waitlist.id)
         
        return HttpResponseRedirect('/../../../accounts/my-account')

    return TemplateResponse(request, 'waitlist_confirm_removal.html', context)

class MoveWaitlistedToRoster(LoginRequiredMixin, UpdateView):
    form_class = MoveWaitlistedToRosterForm
    model = Course
    template_name = 'move_waitlisted_to_roster.html'
    success_url = '/../../../accounts/my-account'

    def form_valid(self, form):
        instance = form.save(commit = False)
        form.save_m2m()
        learner = form.cleaned_data.get('learner')
        instance.learner_on_roster.add(learner.id)
        instance.learner_on_waitlist.remove(learner.id)
        instance.num_spots_available = instance.num_spots_available - 1

        # Send a confirmation email to user
        user = self.request.user.first_name
        course_title = instance.course_title
        instructor = instance.course_instructor
        subject = 'Kona Swim Hub | A swim instructor moved you off their waitlist!'
        html_template = 'emails/course_registration_success_email_family.html'
        html_message = render_to_string(html_template, {'user': user, 'learner': learner, 'course': course_title})
        email_from = settings.DEFAULT_FROM_EMAIL
        recipient_list = [(self.request.user.email)]
        send_mail(subject, html_message, email_from, recipient_list, fail_silently=False)

        # Send a confirmation email to instructor
        html_template = 'emails/course_registration_success_email_instructor.html'
        html_message = render_to_string(html_template, {'instructor': instructor, 'learner': learner, 'course': course_title})
        subject = 'Kona Swim Hub | You successfully moved a student from the waitlist to the roster'
        email_from = settings.DEFAULT_FROM_EMAIL
        recipient_list = [(instance.course_instructor.email)]
        send_mail(subject, html_message, email_from, recipient_list, fail_silently=False)

        return super().form_valid(form)

@ login_required
def course_update(request, pk):

    context = {}
    obj = get_object_or_404(Course, pk=pk)
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