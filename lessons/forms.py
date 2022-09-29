import datetime
from bootstrap_datepicker_plus.widgets import DatePickerInput, TimePickerInput
from django import forms
from django.forms import ModelForm
# from django import ModelForm
from lessons.models import Course

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

TIME_FORMAT = '%I:%M %p'

class CourseCreationForm(ModelForm):
  course_start_time = forms.TimeField(input_formats=[TIME_FORMAT], widget=TimePickerInput(format=TIME_FORMAT))
  course_end_time = forms.TimeField(input_formats=[TIME_FORMAT], widget=TimePickerInput(format=TIME_FORMAT))

  class Meta:
    model = Course
    fields = "__all__"
    exclude = ['course_instructor', 'course_day_of_week', 'learner_on_roster']
    labels = {
      "course_age_range_min": "Minimum age for this course",
      "course_age_range_max": "Maximum age for this course",
      "course_start_date": "Start date",
      "course_end_date": "End date",
      "course_start_time": "Start time",
      "course_end_time": "End time",
      "num_spots_available": "Number of spots available"
    }

    widgets = {
      'course_start_date':DatePickerInput(), # default date-format %m/%d/%Y will be used
      'course_end_date':DatePickerInput(),
      'course_end_time':TimePickerInput(format=TIME_FORMAT),
    }

  def clean_start_date(self):
    data = self.cleaned_data['course_start_date']

    # Check that start date is not in the past.
    if data < datetime.date.today():
      raise ValidationError(_('Invalid date - start date in the past'))

    return data

form = CourseCreationForm

