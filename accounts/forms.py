import logging

from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from bootstrap_datepicker_plus.widgets import DatePickerInput
from django import forms
from django.forms import ModelForm
from accounts.models import CustomUser
from lessons.models import Learner
from turnstile.fields import TurnstileField


logger = logging.getLogger(__name__)


class ResilientTurnstileField(TurnstileField):
    def validate(self, value):
        try:
            super().validate(value)
        except (OSError, ValueError) as exc:
            logger.exception("Turnstile verification request failed")
            raise forms.ValidationError(
                "Anti-spam verification is temporarily unavailable. Please try again.",
                code="turnstile_unavailable",
            ) from exc


class CustomUserCreationForm(UserCreationForm):
    is_instructor = forms.BooleanField(
        label=("Check if would you like to register as a swim instructor."),
        required=False,
    )

    class Meta:
        model = CustomUser
        fields = UserCreationForm.Meta.fields + (
            "first_name",
            "last_name",
            "email",
            "is_instructor",
        )


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = UserChangeForm.Meta.fields


class LearnerAddForm(ModelForm):
    class Meta:
        model = Learner
        fields = ["birthday", "first_name", "last_name"]
        exclude = ["enrolled_in_course", "learner_on_waitlist", "associated_with_user"]
        widgets = {"birthday": DatePickerInput(options={"format": "MM/DD/YYYY"})}


class ContactForm(forms.Form):
    from_email = forms.EmailField(max_length=50, required=True)
    subject = forms.CharField(max_length=100, required=True)
    message = forms.CharField(widget=forms.Textarea, max_length=2000, required=True)
    turnstile = ResilientTurnstileField()


class ContactInstructorForm(forms.Form):
    subject = forms.CharField(max_length=100, required=True)
    message = forms.CharField(widget=forms.Textarea, max_length=2000, required=True)


class ContactLearnersForm(forms.Form):
    def __init__(self, *args, **kwargs):
        course = kwargs.pop("course")
        super(ContactLearnersForm, self).__init__(*args, **kwargs)
        self.fields["recipient_list"].queryset = Learner.objects.filter(learners=course)

    recipient_list = forms.ModelMultipleChoiceField(
        label=("Who would you like to receive this message?"),
        queryset=None,
        widget=forms.CheckboxSelectMultiple,
        required=True,
        error_messages={"required": "You must select a recipient."},
    )
    subject = forms.CharField(max_length=100, required=True)
    message = forms.CharField(widget=forms.Textarea, max_length=2000, required=True)


class ContactWaitlistForm(forms.Form):
    def __init__(self, *args, **kwargs):
        course = kwargs.pop("course")
        super(ContactWaitlistForm, self).__init__(*args, **kwargs)
        self.fields["recipient_list"].queryset = Learner.objects.filter(
            waitlisted=course
        )

    recipient_list = forms.ModelMultipleChoiceField(
        label=("Who would you like to receive this message?"),
        queryset=None,
        widget=forms.CheckboxSelectMultiple,
        required=True,
        error_messages={"required": "You must select a recipient."},
    )
    subject = forms.CharField(max_length=100, required=True)
    message = forms.CharField(widget=forms.Textarea, max_length=2000, required=True)
