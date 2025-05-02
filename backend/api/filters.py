from django_filters import rest_framework as filters
from .models import Task
from django.db.models import Q

class TaskFilter(filters.FilterSet):
    search = filters.CharFilter(method='search_filter')
    column = filters.NumberFilter(field_name='column__id')
    board = filters.NumberFilter(field_name='column__board__id')
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    updated_after = filters.DateTimeFilter(field_name='updated_at', lookup_expr='gte')
    updated_before = filters.DateTimeFilter(field_name='updated_at', lookup_expr='lte')

    class Meta:
        model = Task
        fields = ['search', 'column', 'board', 'created_after', 'created_before', 'updated_after', 'updated_before']

    def search_filter(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value) |
            Q(subtasks__name__icontains=value) |
            Q(column__board__name__icontains=value)
        ).distinct() 