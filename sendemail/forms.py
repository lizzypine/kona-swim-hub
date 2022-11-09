from django import forms

class ContactForm(forms.Form):
  from_email = forms.EmailField(max_length=50, required=True)
  subject = forms.CharField(max_length=100, required=True)
  message = forms.CharField(widget = forms.Textarea, max_length=2000, required=True)