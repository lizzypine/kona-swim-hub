from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import DetailView, DeleteView, TemplateView
from accounts.models import CustomUser, Learner
from lessons.models import Course
from accounts.forms import CustomUserCreationForm, LearnerAddForm, ContactForm, ContactInstructorForm, ContactLearnersForm, ContactWaitlistForm
from django.http import HttpResponseRedirect, HttpResponse
from django.template.response import TemplateResponse
from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import EmailMessage
from django.core.mail import send_mail, BadHeaderError
import django.dispatch

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
    rosters_and_waitlists = dict.fromkeys(courses)
    # Get the roster of learners for each course.
    for course in courses:
        course.roster = Learner.objects.filter(learners=course).values('first_name', 'last_name')
        course.waitlist = Learner.objects.filter(waitlisted=course).values('first_name', 'last_name')
        rosters_and_waitlists[course] = {'roster': course.roster, 'waitlist': course.waitlist}

    learners = Learner.objects.filter(associated_with_user=request.user)

    # Create a dictionary where the key is the learner id and the value is the list of courses this learner is enrolled in.
    learner_courses_and_waitlists = dict.fromkeys(learners)

    # Get the list of courses that each learner is enrolled in.
    for learner in learners:
        learner.enrolled = Course.objects.filter(learner_on_roster=learner).values('id', 'course_title', 'course_instructor_id__first_name', 'course_instructor_id__last_name', 'course_instructor_id__pk', 'course_instructor_id__email', 'course_description', 
        'course_age_range_min', 'course_age_range_max', 'course_location', 'course_start_date', 'course_end_date', 'course_day_of_week', 'course_start_time', 'course_end_time')
        learner.on_waitlist = Course.objects.filter(learner_on_waitlist=learner).values('id', 'course_title', 'course_instructor_id__first_name', 'course_instructor_id__last_name', 'course_instructor_id__pk', 'course_instructor_id__email', 'course_description', 
        'course_age_range_min', 'course_age_range_max', 'course_location', 'course_start_date', 'course_end_date', 'course_day_of_week', 'course_start_time', 'course_end_time')
        learner_courses_and_waitlists[learner] = {'enrolled': learner.enrolled, 'waitlisted': learner.on_waitlist}

    context = {
        'learners': learners,
        'rosters_and_waitlists': rosters_and_waitlists,
        'learner_courses_and_waitlists': learner_courses_and_waitlists,
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

    obj = get_object_or_404(Learner, pk=pk)

    form = LearnerAddForm(request.POST or None, instance = obj)

    # Check if the form is valid:
    if form.is_valid():

        # Commit the data and redirect to the 'my learners' page. 
        form.save()
        return HttpResponseRedirect('../my-account')
    
    # Add form dictionary to context
    context['form'] = form

    return TemplateResponse(request, 'learner-update.html', context)

# Delete a learner
def learner_delete(request, id):
    context = {}
    learner = get_object_or_404(Learner, id=id)

    # Look up list of rosters this learner is on.
    rosters = Course.objects.all().filter(learner_on_roster=learner)
    
    context = {
        'learner': learner,
        'rosters': rosters,
    }

    if request.method == 'POST':
        for roster in rosters:   
            if roster.num_spots_available < 1: 
                # email the instructor that a spot has opened up.
                html_template = 'emails/course_registration_learner_dropped.html'
                html_message = render_to_string(html_template, {'instructor': roster.course_instructor.first_name, 'learner': learner, 'course': roster.course_title})
                subject = 'Kona Swim Hub | A learner dropped out of your course'
                email_from = settings.DEFAULT_FROM_EMAIL
                recipient_list = [(roster.course_instructor.email)]
                send_mail(subject, html_message, email_from, recipient_list, fail_silently=False)
            # else, just add a spot back to the course.
            else: 
                # roster.course_update(roster.num_spots_available += 1)
                # roster_space_update = django.dispatch.signal()
                # roster_space_update.send(sender=self.__Learner__)
                print("add a space")
                # roster_add_space.send(sender=self.__Learner__, instance=roster)
                roster.num_spots_available = roster.num_spots_available + 1
                roster.save()
                # model = profiles.models.UserProfile.objects.filter(user_id=instance.user.id).update(joined=joined)
        learner.delete()
        return HttpResponseRedirect('/accounts/my-account')
    return render(request, 'learner_confirm_delete.html', context)

# Contact - send a message to the site admin
def contactView(request):
    if request.method == 'GET':
        form = ContactForm()
    else:
        form = ContactForm(request.POST)
        if form.is_valid():
            # from_email = form.cleaned_data['from_email']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            try:
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [('lehuaweb@gmail.com')], fail_silently=False)
            except BadHeaderError:
                return HttpResponse('Invalid header found.')
            return redirect('contact_thanks/')
    return render(request, 'contact.html', {'form': form})

class ContactThanksPageView(LoginRequiredMixin, TemplateView):
    template_name = 'contact_thanks.html'

# Contact - parents/learners can send a message to the course instructor
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
            html_template = 'emails/message_user_to_instructor.html'
            html_message = render_to_string(html_template, {"instructor": instructor.first_name, "user": request.user.first_name, "message_content": message})
            try:
                send_mail(subject, html_message, settings.DEFAULT_FROM_EMAIL, [(recipient_list)], fail_silently=False)
            except BadHeaderError:
                return HttpResponse('Invalid header found.')
            return redirect('contact_instructor_thanks')
    return render(request, 'contact_instructor.html', {'form': form, 'instructor': instructor})

class ContactInstructorThanks(LoginRequiredMixin, TemplateView):
    template_name = 'contact_instructor_thanks.html'

# Contact - instructors can send a message to a learner or the entire roster for a course.
def contact_learners(request, pk):

    course = Course.objects.get(id=pk)

    if request.method == 'POST':
        kwargs = {'course': course}
        form = ContactLearnersForm(request.POST, **kwargs)

        if form.is_valid():
            # For each learner object, get the associated_with_user, then get the email of the parent user.
            recipient_list = form.cleaned_data['recipient_list']
            recipient_list_as_list = (list(recipient_list.all()))

            # Add each parent's email address to list of bcc email recipients
            bcc_recipient_list = []
            for learner in recipient_list_as_list:
                parent = learner.associated_with_user
                parent_name = CustomUser.objects.get(id=parent.id).first_name
                parent_email = CustomUser.objects.get(id=parent.id).email
                bcc_recipient_list.append(parent_email)
            
            html_template = 'emails/message_instructor_to_learners.html'
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            html_message = render_to_string(html_template, {"user": parent_name, "instructor": course.course_instructor, "course": course.course_title, "message_content": message})
            email_from = settings.DEFAULT_FROM_EMAIL
            email_to = [settings.DEFAULT_FROM_EMAIL]
            message = EmailMessage(
                subject, 
                html_message, 
                email_from, 
                email_to,
                bcc_recipient_list)
            message.fail_silently = False
            try:
                message.send()
            except BadHeaderError:
                return HttpResponse('Invalid header found.')
            return redirect('contact_instructor_thanks')
    
    else:
        kwargs = {'course': course}
        form = ContactLearnersForm(request.POST, **kwargs)

    return render(request, 'contact_learners.html', {'form': form, 'course': course})

def contact_waitlist(request, pk):

    course = Course.objects.get(id=pk)

    if request.method == 'POST':
        kwargs = {'course': course}
        form = ContactWaitlistForm(request.POST, **kwargs)

        if form.is_valid():
            # For each learner object, get the associated_with_user, then get the email of the parent user.
            recipient_list = form.cleaned_data['recipient_list']
            recipient_list_as_list = (list(recipient_list.all()))

            # Add each parent's email address to list of bcc email recipients
            bcc_recipient_list = []
            for learner in recipient_list_as_list:
                parent = learner.associated_with_user
                parent_name = CustomUser.objects.get(id=parent.id).first_name
                parent_email = CustomUser.objects.get(id=parent.id).email
                bcc_recipient_list.append(parent_email)
            
            html_template = 'emails/message_instructor_to_learners.html'
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            html_message = render_to_string(html_template, {"user": parent_name, "instructor": course.course_instructor, "course": course.course_title, "message_content": message})
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = [settings.DEFAULT_FROM_EMAIL]
            message = EmailMessage(
                subject, 
                html_message, 
                from_email, 
                to_email,
                bcc_recipient_list)
            message.fail_silently = False
            try:
                message.send()
            except BadHeaderError:
                return HttpResponse('Invalid header found.')
            return redirect('contact_instructor_thanks')
    
    else:
        kwargs = {'course': course}
        form = ContactWaitlistForm(request.POST, **kwargs)

    return render(request, 'contact_waitlist.html', {'form': form, 'course': course})