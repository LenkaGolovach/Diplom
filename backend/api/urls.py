from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BoardViewSet,
    ColumnViewSet,
    TaskViewSet,
    LoginView,
    RegisterView,
    ColumnTasksUpdate,
)

router = DefaultRouter()
router.register(r'boards', BoardViewSet, basename='board')
router.register(r'columns', ColumnViewSet, basename='column')
router.register(r'tasks', TaskViewSet, basename='task')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('columns/<int:pk>/tasks/', ColumnTasksUpdate.as_view(), name='column-tasks'),
    path('tasks/<int:task_id>/upload/', FileUploadView.as_view(), name='file-upload'),
]