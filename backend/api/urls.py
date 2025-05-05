from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from .views import (
    BoardViewSet,
    ColumnViewSet,
    TaskViewSet,
    LoginView,
    RegisterView,
    UserViewSet,
    BoardMembersViewSet,
    TaskMemberViewSet,
    MessageViewSet,
    NeuroChatViewSet,
    ReportsView
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'boards', BoardViewSet, basename='board')
router.register(r'columns', ColumnViewSet, basename='column')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'boards/(?P<board_id>\d+)/members', BoardMembersViewSet, basename='board-members')
router.register(r'tasks/(?P<task_pk>\d+)/members', TaskMemberViewSet, basename='taskmembers')
router.register(r'tasks/(?P<task_pk>\d+)/messages', MessageViewSet, basename='task-messages')
router.register(r'neuro-chat', NeuroChatViewSet, basename='neuro-chat')


urlpatterns = [
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('tasks/', TaskViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('tasks/<int:pk>/', TaskViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'})),
    path('api/boards/check_invite/', BoardViewSet.as_view({'get': 'check_invite'})),
    path('api/boards/join/', BoardViewSet.as_view({'post': 'join'})),
    path('', include(router.urls)),
    path('reports/', ReportsView.as_view(), name='reports'),
]

# Добавляем URL для загрузки файлов
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
