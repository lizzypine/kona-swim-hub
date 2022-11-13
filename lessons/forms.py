from bootstrap_datepicker_plus.widgets import DatePickerInput, TimePickerInput
from django.forms import ModelForm
from django import forms
from lessons.models import Course
from accounts.models import Learner
from django.utils.safestring import mark_safe

from django.utils.translation import gettext_lazy as _

TIME_FORMAT = '%I:%M %p'

class CourseCreationForm(ModelForm):

    course_start_time = forms.TimeField(input_formats=[TIME_FORMAT],
        widget=TimePickerInput(format=TIME_FORMAT)
    )

    course_end_time = forms.TimeField(input_formats=[TIME_FORMAT],
        widget=TimePickerInput(format=TIME_FORMAT)
    )

    class Meta:
        model = Course
        fields = '__all__'
        exclude = ['course_instructor', 'course_day_of_week', 'learner_on_roster']
        labels = {
        'course_age_range_min': 'Minimum age for this course',
        'course_age_range_max': 'Maximum age for this course',
        'course_start_date': 'Start date',
        'course_end_date': 'End date',
        'course_start_time': 'Start time',
        'course_end_time': 'End time',
        'num_spots_available': 'Number of spots available'
        }

        widgets = {
        'course_start_date': DatePickerInput(),
        'course_end_date': DatePickerInput(),
        }

    # def clean_time(self):
    #     course_start_time = self.cleaned_data['course_start_time']

        # # Check that start date is not in the past.
        # if data < datetime.date.today():
        #   raise ValidationError(_('Invalid date - start date in the past'))

form = CourseCreationForm

class CourseRegistrationForm(ModelForm):

    def __init__(self, *args, **kwargs):
        # Grants access to the request object so that only learners of the current user are available as options.
        self.request = kwargs.pop('request')
        super(CourseRegistrationForm, self).__init__(*args, **kwargs)
        self.fields['learner'].queryset = Learner.objects.filter(
        associated_with_user=self.request.user)

    class Meta:
        model = Course
        fields = ['id', 'learner_on_roster']
        exclude = ['course_instructor', 'learner_on_roster', 'course_title', 'course_description', 'course_age_range_min', 'course_age_range_max',
            'course_location', 'course_start_date', 'course_end_date', 'course_day_of_week', 'course_start_time', 'course_end_time']

    learner = forms.ModelChoiceField(
        label=mark_safe('Select a Learner to register. Need to add one? Go to <a href="/../accounts/my-account" target="_blank">my account</a>.'),
        queryset=Learner.objects.order_by('first_name'),
        widget=forms.RadioSelect,
        required=True,
        error_messages = {
            'required':"Please Enter your Name"
            }
        )
    
    def clean_learner(self):
        from django.core.exceptions import ValidationError

        instance = form.save(self, commit=False)
        learner = self.cleaned_data.get('learner')

        # If the selected learner's name is already on the roster for this course, show an error message.
        course = Course.objects.filter(id=instance.id)
        roster = Learner.objects.filter(learners__in=course)
        if learner in roster:
            print("already here")
            raise ValidationError('This learner is already registered for this course.')
        
        return learner

form = CourseRegistrationForm