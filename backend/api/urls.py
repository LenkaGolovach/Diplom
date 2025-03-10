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
    BoardMembersViewSet
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
# Add this to your BoardMembersViewSet router
router.register(r'boards/(?P<board_id>\d+)/members', BoardMembersViewSet, basename='board-members')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('tasks/', TaskViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('tasks/<int:pk>/', TaskViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'})),
]

# Добавляем URL для загрузки файлов
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)