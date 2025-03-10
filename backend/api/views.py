from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import Board, Column, Task
from .serializers import BoardSerializer, ColumnSerializer, TaskSerializer, UserSerializer, BoardMemberSerializer
from .models import CustomUser, FileAttachment, BoardMember
import logging
import json
from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, JSONParser
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import secrets
from django.shortcuts import get_object_or_404
from django.db import transaction
import uuid
from rest_framework.exceptions import PermissionDenied
from django.conf import settings
from django.db.models import Q

logger = logging.getLogger(__name__) 

# ViewSet для досок
class BoardViewSet(viewsets.ModelViewSet):
    serializer_class = BoardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        invite_token = self.request.query_params.get('invite_token', None)
        
        # If invite token is provided, return only that specific board
        if invite_token:
            return Board.objects.filter(invite_token=invite_token)
        
        # Otherwise return boards where user is either owner or member
        return Board.objects.filter(
            Q(owner=user) | Q(members__user=user)
        ).distinct()

    def perform_create(self, serializer):
        board = serializer.save(owner=self.request.user)
        board.create_default_columns()

        BoardMember.objects.create(
            user=self.request.user,
            board=board,
            role='owner'
        )

    @action(detail=True, methods=['post'])
    def generate_invite(self, request, pk=None):
        board = self.get_object()
        if board.owner != request.user:
            return Response(
                {'error': 'Только владелец может генерировать ссылки'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        with transaction.atomic():
            board.invite_token = uuid.uuid4()
            board.save()
            return Response({
                'invite_link': f'{settings.FRONTEND_URL}/invite/{board.invite_token}/'
            })

    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        board = get_object_or_404(Board, invite_token=request.data.get('token'))
        BoardMember.objects.get_or_create(
            user=request.user,
            board=board,
            defaults={'role': 'member'}
        )
        return Response(status=status.HTTP_200_OK)

class BoardMembersViewSet(viewsets.ModelViewSet):
    serializer_class = BoardMemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        board_id = self.kwargs.get('board_id')
        return BoardMember.objects.filter(board_id=board_id)

    def perform_destroy(self, instance):
        board = instance.board
        if instance.role == 'owner':
            raise PermissionDenied("Нельзя удалить владельца")
        # Check if the current user is the owner of the board
        if board.owner != self.request.user:
            raise PermissionDenied("Только владелец доски может удалять участников")
        instance.delete()

    @action(detail=False, methods=['get'])
    def get_by_email(self, request, board_id=None):
        email = request.query_params.get('email')
        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = CustomUser.objects.get(email=email)
            member = BoardMember.objects.get(board_id=board_id, user=user)
            serializer = self.get_serializer(member)
            return Response(serializer.data)
        except (CustomUser.DoesNotExist, BoardMember.DoesNotExist):
            return Response({"error": "Member not found"}, status=status.HTTP_404_NOT_FOUND)

# ViewSet для колонок
class ColumnViewSet(viewsets.ModelViewSet):
    serializer_class = ColumnSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Column.objects.filter(board__owner=self.request.user)

    def perform_create(self, serializer):
        # Автоматически связываем колонку с доской
        board_id = self.request.data.get('board')
        if board_id:
            serializer.save(board_id=board_id)
        else:
            serializer.save()

# ViewSet для задач
class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, JSONParser)

    def get_queryset(self):
        return Task.objects.filter(column__board__owner=self.request.user).prefetch_related('subtasks', 'attachments')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Handle deleted files
        deleted_files = request.data.get('deleted_files', [])
        if deleted_files:
            try:
                deleted_file_ids = [int(id) for id in deleted_files]
                FileAttachment.objects.filter(id__in=deleted_file_ids, task=instance).delete()
            except ValueError as e:
                logger.error(f"Error parsing deleted_files: {e}")
        
        return super().update(request, *args, **kwargs)

# Аутентификация
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        user = authenticate(request, email=email, password=password)  # Используем стандартную аутентификацию
        
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                "user": {
                    "id": user.id,
                    "email": user.email,
                },
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }, status=status.HTTP_200_OK)
            
        return Response(
            {"error": "Invalid credentials"}, 
            status=status.HTTP_401_UNAUTHORIZED
        )


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
            }, status=201)
        except Exception as e:
            logger.error(f'Error during registration: {str(e)}')  # Логируем исключение
            return Response({'error': 'Internal server error'}, status=500)

class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, JSONParser)

    def get_object(self):
        return self.request.user

    def get_queryset(self):
        return CustomUser.objects.filter(id=self.request.user.id)