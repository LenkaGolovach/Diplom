from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import Board, Column, Task
from .serializers import BoardSerializer, ColumnSerializer, TaskSerializer
from .models import CustomUser 
import logging
from rest_framework.decorators import action

logger = logging.getLogger(__name__) 

# ViewSet для досок
class BoardViewSet(viewsets.ModelViewSet):
    serializer_class = BoardSerializer

    def get_queryset(self):
        return Board.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

# ViewSet для колонок
class ColumnViewSet(viewsets.ModelViewSet):
    serializer_class = ColumnSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Column.objects.filter(board__owner=self.request.user)

# ViewSet для задач
class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(column__board__owner=self.request.user)

# Аутентификация
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(email=email, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': {
                    'id': user.id,
                    'email': user.email,
                },
                'token': str(refresh.access_token),
            })
        return Response({'error': 'Invalid credentials'}, status=400)

# Регистрация
class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        logger.info(f'Attempting to register user with email: {email}')  # Логируем попытку регистрации
        
        if not email or not password:
            logger.error('Email and password are required')  # Логируем ошибку
            return Response({'error': 'Email and password are required'}, status=400)
        
        if CustomUser.objects.filter(email=email).exists():
            logger.error(f'User with email {email} already exists')  # Логируем ошибку
            return Response({'error': 'User already exists'}, status=400)
        
        try:
            user = CustomUser.objects.create_user(email=email, password=password)
            refresh = RefreshToken.for_user(user)
            logger.info(f'User {email} registered successfully')  # Логируем успешную регистрацию
            return Response({
                'user': {
                    'id': user.id,
                    'email': user.email,
                },
                'token': str(refresh.access_token),
            })
        except Exception as e:
            logger.error(f'Error during registration: {str(e)}')  # Логируем исключение
            return Response({'error': 'Internal server error'}, status=500)

class FileUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, task_id):
        task = get_object_or_404(Task, id=task_id)
        file = request.FILES.get('file')
        if file:
            attachment = FileAttachment.objects.create(
                task=task,
                file=file,
                name=file.name
            )
            return Response(FileAttachmentSerializer(attachment).data)
        return Response({'error': 'No file provided'}, status=400)