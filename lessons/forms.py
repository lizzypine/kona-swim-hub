import datetime
from bootstrap_datepicker_plus.widgets import DatePickerInput, TimePickerInput
from django import forms
from django.forms import ModelForm
# from django import ModelForm
from .models import Course

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

TIME_FORMAT = '%I:%M %p'

class CourseCreationForm(ModelForm):
  course_start_time = forms.TimeField(input_formats=[TIME_FORMAT], widget=TimePickerInput(format=TIME_FORMAT))
  course_end_time = forms.TimeField(input_formats=[TIME_FORMAT], widget=TimePickerInput(format=TIME_FORMAT))

  class Meta:
    model = Course
    fields = "__all__"
    exclude = ['course_day_of_week']
    labels = {
      "course_instructor": "Instructor",
      "course_age_range_min": "Minimum age for this course",
      "course_age_range_max": "Maximum age for this course",
      "course_start_date": "Start date",
      "course_end_date": "End date",
      "course_start_time": "Start time",
      "course_end_time": "End time",
      "num_spots_available": "Number of spots available"
    }

    widgets = {
      # 'course_start_date':DatePickerInput().start_of('course days'), # default date-format %m/%d/%Y will be used
      # 'course_end_date':DatePickerInput().end_of('course days'),
      'course_start_date':DatePickerInput(), # default date-format %m/%d/%Y will be used
      'course_end_date':DatePickerInput(),
      # 'course_start_time':TimePickerInput(format=TIME_FORMAT).start_of('lesson time'),
      'course_end_time':TimePickerInput(format=TIME_FORMAT),
      # 'course_end_time':TimePickerInput(format=TIME_FORMAT).end_of('lesson time'),
      # 'course_end_time':TimePickerInput(format='%I:%M'),
      # 'course_start_time': TimePickerInput(
      #   options={
      #     "showClear": False,
      #   }
      # ),
    }

  def clean_start_date(self):
    data = self.cleaned_data['course_start_date']

    # Check that start date is not in the past.
    if data < datetime.date.today():
      raise ValidationError(_('Invalid date - start date in the past'))

    return data

form = CourseCreationForm


#     

# LOOKING BACK AT THE COURSE MODEL WE CREATED. NEED TO CONSULT WHEN CREATING FORM FIELDS?
# class Course(models.Model):
#     # course_instructor = models.ForeignKey(CustomUser, on_delete=models.CASCADE) # When User is deleted, also delete the Course. 
#     course_age_range = models.CharField(max_length=100)
#     # course_age_range = IntegerRange() # Is this right?
#     course_location = models.CharField(max_length=100)
#     course_start_date = models.DateField()
#     course_end_date = models.DateField()
#     course_day_of_week = models.CharField(max_length=100) # Later: Select day of week (e.g., Monday, Tuesday) from checkboxes.
#     course_time = models.TimeField()
#     spots_available = models.CharField(max_length=100)
#     # spots_available = models.Boolean()
#     num_spots_available = models.IntegerField() # Do I need to do something else here?
#     # learner_on_roster = models.ForeignKey(Learner, on_delete=models.SET_NULL=True)



# class CustomUserChangeForm(UserChangeForm):
#     class Meta:
#         model = CustomUser
#         fields = UserChangeForm.Meta.fields