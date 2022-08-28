from django.http import HttpResponseRedirect
from django.shortcuts import render

from django.views.generic import ListView, DetailView, TemplateView
from .models import Course
from .forms import CourseCreationForm

# Instructor status required to create a form.
# @login_required
# @permission_required
def course_create(request):

    # If this is a POST request then process the Form data
    if request.method == "POST":
        
        # Create a form instance and populate it with data from the request (binding):
        form = CourseCreationForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # Process the data and redirect to the thank you page. 
            form.save()
            return HttpResponseRedirect('thanks/')

        # Save a new Course object from the form's data.
        # KEEP THIS?
        
    
    # Else, this is a GET request (or any other method). Create the default form.
    else:
        form = CourseCreationForm()

    # return render(request, 'lessons/course_new.html', {'form': form})
    return render(request, 'course_create.html', {'form': form})

class CourseListView(ListView):
    model = Course
    # template_name = 'lessons/course_list.html'
    template_name = 'course_list.html'
    context_object_name = 'course' # what does this do?

class CourseDetailView(DetailView):
    model = Course
    # template_name = 'lessons/course_detail.html'
    template_name = 'course_detail.html'
    context_object_name = 'course' # what does this do?

class ThanksPageView(TemplateView):
    template_name = "thanks.html"



# class CourseCreateView(CreateView):
# class CourseCreateView(FormView):
#     model = Course
#     # template_name = 'lessons/course_new.html'
#     template_name = 'course_new.html'
#     fields = ['course_age_range', 'course_location', 'course_start_date', 'course_end_date', 'course_day_of_week', 'course_time', 'num_spots_available']
#     success_url = '/lessons/'

  
# class SignUpView(CreateView):
#     form_class = CustomUserCreationForm
#     success_url = reverse_lazy("login")
#     template_name = "registration/signup.html"


