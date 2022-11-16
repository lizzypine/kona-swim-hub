from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import DetailView, DeleteView, TemplateView
from accounts.models import CustomUser, Learner
from lessons.models import Course
from accounts.forms import CustomUserCreationForm, LearnerAddForm, ContactForm, ContactInstructorForm, ContactLearnersForm
from django.http import HttpResponseRedirect, HttpResponse
from django.template.response import TemplateResponse
from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import EmailMessage
from django.core.mail import send_mail, BadHeaderError

def user_register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        email = request.POST['email']
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']

        if CustomUser.objects.filter(email=email).exists():
            messages.info(request, 'An account with this email already exists.')
        else:
            user = CustomUser.objects.create_user(
                username=email, email=email, first_name=first_name, last_name=last_name)
            mydict = {'email': email}
            user.save()
            html_template = 'registration/register_success_email.html'
            html_message = render_to_string(html_template, context=mydict)
            subject = 'You created an account with Kona Swim Hub'
            email_from = settings.DEFAULT_FROM_EMAIL
            recipient_list = [email]
            message = EmailMessage(
                subject, 
                html_message, 
                email_from, 
                recipient_list)
            message.content_subtype = 'html'
            message.fail_silently = False
            message.send()
            return HttpResponseRedirect('../register_thanks')
    
    else:
        form = CustomUserCreationForm() 
    
    return TemplateResponse(request, 'registration/register.html', {'form': form})

class RegisterThanksPageView(TemplateView):
    template_name = 'registration/register_thanks.html'

class ProfileUpdateView(LoginRequiredMixin, DetailView):
    model = Learner
    template_name = 'course_detail.html'
    context_object_name = 'course'

# class UserPageView(LoginRequiredMixin, ListView):
#     template_name = 'users.html'
#     model = CustomUser

# class UserChangeView(LoginRequiredMixin, CreateView):
#     form_class = CustomUserChangeForm
#     success_url = reverse_lazy('profile')
#     template_name = 'profile.html'

# My Account Page
@login_required
def my_account_view (request):

    courses = Course.objects.filter(course_instructor=request.user)

    # Create a dictionary where the key is the course id and the value is the list of names on the roster for that course.
    rosters = dict.fromkeys(courses)

    # Get the roster of learners for each course.
    for course in courses:
        roster = Learner.objects.filter(learners=course).values('first_name', 'last_name')
        rosters[course] = roster

    learners = Learner.objects.filter(associated_with_user=request.user)

    # Create a dictionary where the key is the learner id and the value is the list of courses this learner is enrolled in.
    learner_courses = dict.fromkeys(learners)

    # Get the list of courses that each learner is enrolled in.
    for learner in learners:
        course_list = Course.objects.filter(learner_on_roster=learner).values('course_title', 'course_instructor_id__first_name', 'course_instructor_id__last_name', 'course_instructor_id__pk', 'course_instructor_id__email', 'course_description', 
        'course_age_range_min', 'course_age_range_max', 'course_location', 'course_start_date', 'course_end_date', 'course_start_time', 'course_end_time')
        
        learner_courses[learner] = course_list

    context = {
        'learners': learners,
        'learner_courses': learner_courses,
        'courses': courses,
        'rosters': rosters
    }

    return render(request, 'my-account.html', context)

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
    if request.method == 'POST':

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

    return TemplateResponse(request, 'learner-add.html', {'form': form})

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

    return TemplateResponse(request, 'learner-update.html', context)

# Delete a learner
class LearnerDeleteView(LoginRequiredMixin, DeleteView):
    model = Learner
    template_name = 'learner-confirm-delete.html'
    success_url = '../../my-account'

# Contact - send a message to the site admin
def contactView(request):
    if request.method == 'GET':
        form = ContactForm()
    else:
        form = ContactForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            try:
                send_mail(subject, message, settings.CONTACT_EMAIL, [settings.DEFAULT_FROM_EMAIL])
            except BadHeaderError:
                return HttpResponse('Invalid header found.')
            return redirect('contact_thanks/')
    return render(request, 'contact.html', {'form': form})

class ContactThanksPageView(LoginRequiredMixin, TemplateView):
    template_name = 'contact_thanks.html'

# Contact - send a message to the course instructor
def contact_instructor(request, pk):

    instructor = CustomUser.objects.get(id=pk)
    recipient_list = instructor.email

    if request.method == 'GET':
        form = ContactInstructorForm()
    else:
        form = ContactInstructorForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            try:
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [(recipient_list)], fail_silently=False)
            except BadHeaderError:
                return HttpResponse('Invalid header found.')
            return redirect('contact_instructor_thanks')
    return render(request, 'contact_instructor.html', {'form': form, 'instructor': instructor})

class ContactInstructorThanks(LoginRequiredMixin, TemplateView):
    template_name = 'contact_instructor_thanks.html'

# Contact - instructors can send a message to a learner or the entire roster for a course.
def contact_learners(request, pk):

    course = Course.objects.get(id=pk)
    roster = Learner.objects.filter(learners=course).values('first_name', 'last_name')

    if request.method == 'POST':
        kwargs = {'roster': roster, 'course': course}
        form = ContactLearnersForm(request.POST, **kwargs)

        if form.is_valid():
        #     subject = form.cleaned_data['subject']
        #     message = form.cleaned_data['message']
        #     try:
        #         send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [(recipient_list)], fail_silently=False)
        #     except BadHeaderError:
        #         return HttpResponse('Invalid header found.')
            return redirect('contact_instructor_thanks')
    else:
        kwargs = {'roster': roster, 'course': course}
        form = ContactLearnersForm(request.POST, **kwargs)

    return render(request, 'contact_learners.html', {'form': form, 'course': course})