from bootstrap_datepicker_plus.widgets import DatePickerInput, TimePickerInput
from django.forms import ModelForm
from django import forms
from lessons.models import Course
from accounts.models import Learner
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

# from django.conf import settings
# from django.core.mail import send_mail
# from django.template.loader import render_to_string
# from django.db import transaction

AGE_CHOICES = [
    ("6 months old", "6 months old"),
    ("9 months old", "9 months old"),
    ("12 months old", "12 months old"),
    ("18 months old", "18 months old"),
    ("2 years old", "2 years old"),
    ("3 years old", "3 years old"),
    ("4 years old", "4 years old"),
    ("5 years old", "5 years old"),
    ("6 years old", "6 years old"),
    ("7 years old", "7 years old"),
    ("8 years old", "8 years old"),
    ("9 years old", "9 years old"),
    ("10 years old", "10 years old"),
    ("11 years old", "11 years old"),
    ("12 years old", "12 years old"),
    ("13 years old", "13 years old"),
    ("14 years old", "14 years old"),
    ("15 years old", "15 years old"),
    ("16 years old", "16 years old"),
    ("17 years old", "17 years old"),
    ("18 years old", "18 years old"),
]

DAY_CHOICES = [
    ("Monday", "Monday"),
    ("Tuesday", "Tuesday"),
    ("Wednesday", "Wednesday"),
    ("Thursday", "Thursday"),
    ("Friday", "Friday"),
    ("Saturday", "Saturday"),
    ("Sunday", "Sunday"),
]


class CourseCreationForm(ModelForm):
    course_age_range_min = forms.CharField(
        widget=forms.Select(choices=AGE_CHOICES),
    )

    course_age_range_max = forms.CharField(
        widget=forms.Select(choices=AGE_CHOICES),
    )

    course_day_of_week = forms.CharField(
        widget=forms.Select(choices=DAY_CHOICES),
    )

    class Meta:
        model = Course
        fields = "__all__"
        exclude = ["course_instructor", "learner_on_roster", "learner_on_waitlist"]
        labels = {
            "course_age_range_min": "Minimum age for this course",
            "course_age_range_max": "Maximum age for this course",
            "course_start_date": "Start date",
            "course_end_date": "End date",
            "course_start_time": "Start time",
            "course_end_time": "End time",
            "num_spots_available": "Number of spots available",
        }

        widgets = {
            "course_start_date": DatePickerInput(options={"format": "MM/DD/YYYY"}),
            "course_end_date": DatePickerInput(options={"format": "MM/DD/YYYY"}),
            "course_start_time": TimePickerInput(options={"format": "hh:mm a"}),
            "course_end_time": TimePickerInput(options={"format": "hh:mm a"}),
        }


form = CourseCreationForm


class CourseRegistrationForm(ModelForm):
    def __init__(self, *args, **kwargs):
        # Show learners of the current user
        self.request = kwargs.pop("request")
        super(CourseRegistrationForm, self).__init__(*args, **kwargs)
        self.fields["learner"].queryset = Learner.objects.filter(
            associated_with_user=self.request.user
        )

    class Meta:
        model = Course
        fields = ["id", "learner_on_roster"]
        exclude = [
            "course_instructor",
            "learner_on_roster",
            "course_title",
            "course_description",
            "course_age_range_min",
            "course_age_range_max",
            "course_location",
            "course_start_date",
            "course_end_date",
            "course_day_of_week",
            "course_start_time",
            "course_end_time",
        ]

    learner = forms.ModelChoiceField(
        label=mark_safe(
            'Select a Learner to register. Need to add one? Go to <a href="/../accounts/my-account" target="_blank">my account</a>.'
        ),
        queryset=Learner.objects.order_by("first_name"),
        widget=forms.RadioSelect,
        required=True,
        error_messages={"required": "Please Choose a Name"},
    )

    def clean_learner(self):
        from django.core.exceptions import ValidationError

        instance = form.save(self, commit=False)
        learner = self.cleaned_data.get("learner")
        # If the selected learner's name is already on the roster for this course, show an error message.
        course = Course.objects.filter(id=instance.id)
        roster = Learner.objects.filter(learners__in=course)
        if learner in roster:
            raise ValidationError("This learner is already registered for this course.")

        return learner


form = CourseRegistrationForm


class JoinWaitlistForm(ModelForm):
    def __init__(self, *args, **kwargs):
        # Show learners of the current user
        self.request = kwargs.pop("request")
        super(JoinWaitlistForm, self).__init__(*args, **kwargs)
        self.fields["learner"].queryset = Learner.objects.filter(
            associated_with_user=self.request.user
        )

    class Meta:
        model = Course
        fields = ["id", "learner_on_roster"]
        exclude = [
            "course_instructor",
            "learner_on_roster",
            "learner_on_waitlist",
            "course_title",
            "course_description",
            "course_age_range_min",
            "course_age_range_max",
            "course_location",
            "course_start_date",
            "course_end_date",
            "course_day_of_week",
            "course_start_time",
            "course_end_time",
        ]

    learner = forms.ModelChoiceField(
        label=mark_safe(
            'Select a Learner to join the waitlist. Need to add one? Go to <a href="/../accounts/my-account" target="_blank">my account</a>.'
        ),
        queryset=Learner.objects.order_by("first_name"),
        widget=forms.RadioSelect,
        required=True,
        error_messages={"required": "Please Enter your Name"},
    )

    def clean_learner(self):
        from django.core.exceptions import ValidationError

        instance = form.save(self, commit=False)
        learner = self.cleaned_data.get("learner")
        # If the selected learner's name is already on the roster or waitlist for this course, show an error message.
        course = Course.objects.filter(id=instance.id)
        roster = Learner.objects.filter(learners__in=course)
        waitlist = Learner.objects.filter(waitlisted__in=course)
        if learner in roster:
            raise ValidationError("This learner is already registered for this course.")
        if learner in waitlist:
            raise ValidationError(
                "This learner is already on the waitlist for this course."
            )

        return learner


form = JoinWaitlistForm


class MoveWaitlistedToRosterForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(MoveWaitlistedToRosterForm, self).__init__(*args, **kwargs)
        self.fields["learner"].queryset = Learner.objects.filter(
            waitlisted=self.instance
        )

    class Meta:
        model = Course
        fields = ["id"]
        exclude = [
            "course_instructor",
            "learner_on_roster",
            "course_title",
            "course_description",
            "course_age_range_min",
            "course_age_range_max",
            "course_location",
            "course_start_date",
            "course_end_date",
            "course_day_of_week",
            "course_start_time",
            "course_end_time",
        ]

    learner = forms.ModelChoiceField(
        label=mark_safe("Select a Learner to move from the waitlist to the roster."),
        queryset=Learner.objects.order_by("first_name"),
        widget=forms.RadioSelect,
        required=True,
        error_messages={"required": "Please Choose a Name"},
    )


form = MoveWaitlistedToRosterForm
