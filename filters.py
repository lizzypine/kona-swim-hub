import django_filters
from lessons.models import Course

class AgeFilter(django_filters.FilterSet):
  age = django_filters.AllValuesFilter()

  class Meta:
    model = Course
    fields = ['age']