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
    priority = filters.CharFilter(field_name='priority', lookup_expr='exact')
    column_name = filters.CharFilter(method='filter_by_column_name')

    class Meta:
        model = Task
        fields = ['search', 'column', 'board', 'priority', 'column_name', 'created_after', 'created_before', 'updated_after', 'updated_before']

    def search_filter(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value) |
            Q(subtasks__name__icontains=value) |
            Q(column__board__name__icontains=value)
        ).distinct()

    def filter_by_column_name(self, queryset, name, value):
        standard_columns = ['Нужно сделать', 'В процессе', 'Готово']
        if value == '__other__':
            # Исключаем стандартные колонки (регистронезависимо)
            return queryset.exclude(column__name__iregex=r'^({})$'.format('|'.join(standard_columns)))
        elif value and value not in ['', '__other__']:
            # Фильтруем по точному имени (регистронезависимо)
            return queryset.filter(column__name__iexact=value)
        # Если value пустое или не соответствует ни одному условию, возвращаем исходный queryset
        return queryset 