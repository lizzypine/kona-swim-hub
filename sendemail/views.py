from django.shortcuts import render
from django.core.mail import send_mail, BadHeaderError
from django.http import HttpResponse
# from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.conf import settings
from sendemail.forms import ContactForm
from django.views.generic import TemplateView

def contactView(request):
    if request.method == 'GET':
        form = ContactForm()
    else:
        form = ContactForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            from_email = form.cleaned_data['from_email']
            message = form.cleaned_data['message']
            try:
                send_mail(subject, message, settings.CONTACT_EMAIL, [settings.DEFAULT_FROM_EMAIL])
                # send_mail(subject, message, 'lizzy@lehuaweb.com', [settings.DEFAULT_FROM_EMAIL])
            except BadHeaderError:
                return HttpResponse('Invalid header found.')
            # return HttpResponseRedirect('contact_thanks/')
            return redirect('contact_thanks/')
    return render(request, 'contact.html', {'form': form})

class ContactThanksPageView(TemplateView):
    template_name = 'contact_thanks.html'
