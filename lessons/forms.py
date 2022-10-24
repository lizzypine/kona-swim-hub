from bootstrap_datepicker_plus.widgets import DatePickerInput, TimePickerInput
from django.forms import ModelForm
from django import forms
from lessons.models import Course
from accounts.models import Learner

from django.utils.translation import gettext_lazy as _

TIME_FORMAT = '%I:%M %p'

class CourseCreationForm(ModelForm):

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
        'course_start_date':DatePickerInput(),
        'course_end_date':DatePickerInput(),
        'course_start_time':TimePickerInput(format=TIME_FORMAT),
        'course_end_time':TimePickerInput(format=TIME_FORMAT),
        }

    def clean_start_date(self):
        data = self.cleaned_data['course_start_date']

        # # Check that start date is not in the past.
        # if data < datetime.date.today():
        #   raise ValidationError(_('Invalid date - start date in the past'))

        # return data

form = CourseCreationForm

class CourseRegistrationForm(forms.ModelForm):
    # Check that the learner is not already registered for this course.
    # def clean_learner_data(self):
    #   data = self.cleaned_data['learner']

    #   if data == 
    #   return data

    def __init__(self, *args, **kwargs):
        # Grants access to the request object so that only learners of the current user are available as options.
        self.request = kwargs.pop('request')
        super(CourseRegistrationForm, self).__init__(*args, **kwargs)
        self.fields['learner'].queryset = Learner.objects.filter(
        associated_with_user=self.request.user)

        # learner_choices = Learner.objects.filter(
        # associated_with_user=self.request.user)

    class Meta:
        model = Course
        # fields = ['id', 'num_spots_available']
        fields = ['id', 'learner_on_roster']
        exclude = ['course_instructor', 'learner_on_roster', 'course_title', 'course_description', 'course_age_range_min', 'course_age_range_max',
            'course_location', 'course_start_date', 'course_end_date', 'course_day_of_week', 'course_start_time', 'course_end_time']


    learner = forms.ModelChoiceField(
        label='Select a Learner',
        queryset=Learner.objects.order_by('first_name'),
        widget=forms.RadioSelect,
        required=True,
    )

  # def save(self, commit=True):
  #       inst = super(CourseRegistrationForm, self).save(commit=False)
  #       inst.author = self._user
  #       if commit:
  #           inst.save()
  #           self.save_m2m()
  #       return inst

  # def send_email(self):
  #   # send email using the self.cleaned_data dictionary
  #   pass

form = CourseRegistrationForm

# Go to payment.

# Thanks!