from django.http import HttpResponseRedirect
from django.views.generic import ListView, DetailView, TemplateView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from lessons.models import Course
from lessons.forms import CourseCreationForm
from django.template.response import TemplateResponse
# from filters import AgeFilter

# Instructor status required to create a course.
@login_required
@user_passes_test(lambda user: user.is_instructor)
def course_create(request):

    # If this is a POST request then process the Form data
    if request.method == "POST":
        
        # Create a form instance and populate it with data from the request (binding):
        form = CourseCreationForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # Hold the instance and attach the instructor to this course. 
            form.instance = form.save(commit=False)
            form.instance.course_instructor = request.user
            # Commit the data and redirect to the 'thanks' page. 
            form.instance.save()
            return HttpResponseRedirect('thanks/')

    else:
        form = CourseCreationForm()

    # return render(request, 'lessons/course_new.html', {'form': form})
    return TemplateResponse(request, 'course_create.html', {'form': form})

class CourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'course_list.html'
    # context_object_name = 'course' # what does this do?

    def get_course_list(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # age_filter = AgeFilter(request.GET)
        # return render(request, 'course_list.html', {'age_filter':age_filter})
        return context

# experiment with range filter
    # def index(request):
    #     all_courses = Course.objects.all()
    #     return render(request, 'course_list.html', {'all_course':all_courses})

class CourseDetailView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = 'course_detail.html'
    context_object_name = 'course' # what does this do?

# A function-based view showing course detail

# def view_course(request, course_id):
#     course = get_object_or_404(Course, id=course_id)
#     data = {
#         "course": course,
#     }

#     return render(request, "course_detail.html", data)

class ThanksPageView(LoginRequiredMixin, TemplateView):
    template_name = "thanks.html"

