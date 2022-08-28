import datetime

# from django.contrib.auth.forms import forms
from django.forms import ModelForm
from .models import Course

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


# class CourseCreationForm(forms.Form):
class CourseCreationForm(ModelForm):
  class Meta:
    model = Course
    # fields = ['course_age_range', 'course_location', 'course_start_date']
    fields = '__all__'
    # course_name = forms.CharField(label="Course name", MAX_LENGTH=100)
    # course_title = forms.CharField(label="Course title", max_length=100)
    # course_age_range = forms.CharField(label="Age range")
    # course_start_date = forms.DateField(help_text="Enter the date this course begins.")

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