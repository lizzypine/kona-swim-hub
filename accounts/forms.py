import json
import logging
from urllib.parse import urlencode
from urllib.request import build_opener, ProxyHandler, Request

from django.conf import settings
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from bootstrap_datepicker_plus.widgets import DatePickerInput
from django import forms
from django.forms import ModelForm
from accounts.models import CustomUser
from lessons.models import Learner
from turnstile.fields import TurnstileField
from turnstile import settings as turnstile_settings


logger = logging.getLogger(__name__)


class ResilientTurnstileField(TurnstileField):
    def validate(self, value):
        if not getattr(settings, "TURNSTILE_ENABLE", turnstile_settings.ENABLE):
            return
        forms.Field.validate(self, value)
        secret = settings.TURNSTILE_SECRET
        payload = {"secret": secret, "response": value}
        # Cloudflare expects an IP address when this optional parameter is sent.
        if self.remote_ip:
            payload["remoteip"] = self.remote_ip
        request = Request(
            getattr(settings, "TURNSTILE_VERIFY_URL", turnstile_settings.VERIFY_URL),
            urlencode(payload).encode(),
        )
        try:
            opener = build_opener(ProxyHandler(
                getattr(settings, "TURNSTILE_PROXIES", turnstile_settings.PROXIES)
            ))
            with opener.open(
                request,
                timeout=getattr(settings, "TURNSTILE_TIMEOUT", turnstile_settings.TIMEOUT),
            ) as response:
                result = json.loads(response.read().decode("utf-8"))
            if not isinstance(result, dict) or not isinstance(result.get("success"), bool):
                raise ValueError
        except (OSError, ValueError) as exc:
            # Exception text/tracebacks may include request data or credentials.
            logger.warning(
                "Turnstile verification unavailable (%s error)",
                "transport" if isinstance(exc, OSError) else "response",
            )
            raise forms.ValidationError(
                "Anti-spam verification is temporarily unavailable. Please try again.",
                code="turnstile_unavailable",
            ) from None

        def safe_metadata(value, limit):
            if not isinstance(value, str):
                return ""
            for sensitive in (secret, payload["response"]):
                if sensitive:
                    value = value.replace(sensitive, "[redacted]")
            return value[:limit]

        codes = result.get("error-codes", [])
        codes = codes if isinstance(codes, list) else []
        metadata = {
            "success": result["success"],
            "error-codes": [safe_metadata(code, 100) for code in codes[:10]],
            "hostname": safe_metadata(result.get("hostname", ""), 253),
        }
        log = logger.info if result["success"] else logger.warning
        log("Turnstile verification result: %s", json.dumps(metadata))
        if not result["success"]:
            raise forms.ValidationError(
                self.error_messages["invalid_turnstile"], code="invalid_turnstile"
            )


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
