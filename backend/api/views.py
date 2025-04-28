from rest_framework import viewsets, permissions, mixins
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import Board, Column, Task
from .serializers import BoardSerializer, ColumnSerializer, TaskSerializer, UserSerializer, BoardMemberSerializer, TaskMemberSerializer, MessageSerializer, MessageAttachmentSerializer, MessageUpdateSerializer
from .models import CustomUser, FileAttachment, BoardMember, TaskMember, Message, MessageAttachment
import logging
import json
from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, JSONParser, FormParser
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import secrets
from django.shortcuts import get_object_or_404
from django.db import transaction
import uuid
from rest_framework.exceptions import PermissionDenied
from django.conf import settings
from django.db.models import Q
from .permissions import IsBoardMember
from .permissions import IsTaskMember
from django.db import IntegrityError
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from .tasks import generate_ai_response
import socketio
import eventlet

# создаём единственный клиент для эмита
sio = socketio.Client(reconnection=True, reconnection_attempts=5, reconnection_delay=1)

logger = logging.getLogger(__name__) 

# ViewSet для досок
class BoardViewSet(viewsets.ModelViewSet):
    lookup_url_kwarg = 'pk'
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

    @action(detail=False, methods=['get'])
    def check_invite(self, request):
        token = request.query_params.get('token')
        if not token:
            return Response({'error': 'Token required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            board = Board.objects.get(invite_token=token)
            is_member = BoardMember.objects.filter(
                user=request.user,
                board=board
            ).exists()
            
            return Response({
                'board': BoardSerializer(board, context={'request': request}).data,
                'is_member': is_member
            })
            
        except Board.DoesNotExist:
            return Response({'error': 'Invalid token'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['post'])
    def join(self, request):
        token = request.data.get('token')
        try:
            board = Board.objects.get(invite_token=token)
            member, created = BoardMember.objects.get_or_create(
                user=request.user,
                board=board,
                defaults={'role': 'member'}
            )
            return Response({
                'success': True,
                'is_new_member': created
            })
            
        except Board.DoesNotExist:
            return Response({'error': 'Invalid token'}, status=status.HTTP_404_NOT_FOUND)

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
    permission_classes = [permissions.IsAuthenticated, IsBoardMember]
    parser_classes = (MultiPartParser, JSONParser)

    def get_queryset(self):
        return Task.objects.filter(
            column__board__members__user=self.request.user  # Проверяем, что пользователь в списках участников доски
        ).prefetch_related('subtasks', 'attachments')

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

class TaskMemberViewSet(viewsets.ModelViewSet):
    serializer_class = TaskMemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TaskMember.objects.filter(task_id=self.kwargs['task_pk'])

    def create(self, request, *args, **kwargs):
        task = get_object_or_404(Task, id=self.kwargs['task_pk'])
        member, created = TaskMember.objects.get_or_create(
            task=task,
            user=request.user
        )
        return Response(self.get_serializer(member).data, 
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        task = get_object_or_404(Task, id=self.kwargs['task_pk'])
        member = get_object_or_404(TaskMember, task=task, user=request.user)
        member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

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

class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated, IsTaskMember]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    
    queryset = Message.objects.all()
    
    def get_queryset(self):
        return Message.objects.filter(
            task_id=self.kwargs['task_pk']
        ).select_related(
            'sender', 
            'reply_to__sender'
        ).prefetch_related(
            'attachments'
        ).order_by('created_at')
    
    def get_serializer_class(self):
        if self.action == 'partial_update':
            return MessageUpdateSerializer
        return MessageSerializer

    def perform_create(self, serializer):
        # 1) сохраняем сообщение
        task = get_object_or_404(Task, id=self.kwargs['task_pk'])
        msg = serializer.save(task=task, sender=self.request.user)
        # 2) готовим payload
        payload = MessageSerializer(msg, context={'request': self.request}).data
        # 3) эмитим событие в канал 'task:message-created' :contentReference[oaicite:8]{index=8}
        if not sio.connected:
            sio.connect('http://127.0.0.1:8000')
        sio.emit('task:message-created', payload, namespace='/')  # :contentReference[oaicite:9]{index=9}
        eventlet.sleep(0)  # даём eventlet-циклу время на отправку :contentReference[oaicite:10]{index=10}
        sio.disconnect()

    def perform_update(self, serializer):
        msg = serializer.save(is_edited=True)
        payload = MessageSerializer(msg, context={'request': self.request}).data
        if not sio.connected: sio.connect('http://127.0.0.1:8000')
        sio.emit('task:message-updated', payload, namespace='/')
        eventlet.sleep(0)
        sio.disconnect()

    def perform_destroy(self, instance):
        msg_id = instance.id
        instance.delete()
        if not sio.connected: sio.connect('http://127.0.0.1:8000')
        sio.emit('task:message-deleted', {'id': msg_id}, namespace='/')
        eventlet.sleep(0)
        sio.disconnect()

class NeuroChatViewSet(mixins.ListModelMixin,
                       mixins.CreateModelMixin,
                       viewsets.GenericViewSet):
    """
    ViewSet для нейрочата: список сообщений и создание нового сообщения пользователя,
    по которому запускается фоновые размышления ИИ.
    """
    queryset = Message.objects.filter(neuro_chat=True).order_by('created_at')
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        msg = serializer.save(sender=self.request.user, neuro_chat=True)
        payload = MessageSerializer(msg, context={'request': self.request}).data
        # эмитим событие нейрочата сразу :contentReference[oaicite:13]{index=13}
        if not sio.connected:
            sio.connect('http://127.0.0.1:8000')
        sio.emit('neuro-chat:message-created', payload, namespace='/')
        eventlet.sleep(0)
        sio.disconnect()
        generate_ai_response.delay(msg.id)