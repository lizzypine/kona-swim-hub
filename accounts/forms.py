from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from bootstrap_datepicker_plus.widgets import DatePickerInput
from django.forms import ModelForm
from accounts.models import CustomUser
from lessons.models import Learner

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm):
        model = CustomUser
        fields = UserCreationForm.Meta.fields + ('email', 'first_name', 'last_name')

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = UserChangeForm.Meta.fields

class LearnerAddForm(ModelForm):
  class Meta:
    model = Learner
    fields = ['birthday', 'first_name', 'last_name']
    exclude = ['enrolled_in_course', 'learner_on_waitlist', 'associated_with_user']
    widgets = {
      'birthday': DatePickerInput()
    }

  def send_email(self):
    # send email using the self.cleaned_data dictionary
    pass
