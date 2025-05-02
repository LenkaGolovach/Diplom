from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import Board, Column, Task, CustomUser, BoardMember
from .serializers import (
    BoardSerializer, ColumnSerializer, TaskSerializer, UserSerializer,
    BoardMemberSerializer, TaskMemberSerializer, ProjectReportSerializer,
    TaskReportSerializer, MemberReportSerializer
)
from .models import FileAttachment
from .filters import TaskFilter
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
from .permissions import IsBoardMember
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated

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
    filter_backends = [DjangoFilterBackend]
    filterset_class = TaskFilter

    def get_queryset(self):
        queryset = Task.objects.filter(
            column__board__members__user=self.request.user
        ).prefetch_related('subtasks', 'attachments')
        
        # Применяем фильтры
        queryset = self.filter_queryset(queryset)
        
        return queryset

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

class ReportsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            report_type = request.query_params.get('report_type')
            board_id = request.query_params.get('board_id')
            task_id = request.query_params.get('task_id')

            logger.info(f"Generating report: type={report_type}, board_id={board_id}, task_id={task_id}")

            if not report_type:
                logger.error("Report type is required")
                return Response({'error': 'Report type is required'}, status=400)

            if report_type == 'tasks':
                if not task_id:
                    logger.error("Task ID is required for task report")
                    return Response({'error': 'Task ID is required'}, status=400)
                
                try:
                    task = Task.objects.get(id=task_id)
                    logger.info(f"Found task: {task.id} - {task.name}")
                    data = TaskReportSerializer(task).data
                    logger.info(f"Task report data: {data}")
                    return Response(data)
                except Task.DoesNotExist:
                    logger.error(f"Task not found: {task_id}")
                    return Response({'error': 'Task not found'}, status=404)
                except Exception as e:
                    logger.error(f"Error generating task report: {str(e)}", exc_info=True)
                    return Response({'error': str(e)}, status=500)

            elif report_type == 'projects':
                if not board_id:
                    logger.error("Board ID is required for project report")
                    return Response({'error': 'Board ID is required'}, status=400)
                
                try:
                    board = Board.objects.get(id=board_id)
                    logger.info(f"Found board: {board.id} - {board.name}")
                    
                    # Получаем статистику
                    total_tasks = Task.objects.filter(column__board=board).count()
                    completed_tasks = Task.objects.filter(column__board=board, column__name='Готово').count()
                    in_progress_tasks = Task.objects.filter(column__board=board, column__name='В процессе').count()
                    
                    logger.info(f"Board statistics: total={total_tasks}, completed={completed_tasks}, in_progress={in_progress_tasks}")
                    
                    data = {
                        'projects': [ProjectReportSerializer(board).data],
                        'statistics': {
                            'total_projects': 1,
                            'active_projects': 1 if in_progress_tasks > 0 else 0,
                            'completed_projects': 1 if completed_tasks == total_tasks and total_tasks > 0 else 0
                        }
                    }
                    logger.info(f"Project report data: {data}")
                    return Response(data)
                except Board.DoesNotExist:
                    logger.error(f"Board not found: {board_id}")
                    return Response({'error': 'Board not found'}, status=404)
                except Exception as e:
                    logger.error(f"Error generating project report: {str(e)}", exc_info=True)
                    return Response({'error': str(e)}, status=500)

            elif report_type == 'members':
                if not board_id:
                    logger.error("Board ID is required for member report")
                    return Response({'error': 'Board ID is required'}, status=400)
                
                try:
                    board = Board.objects.get(id=board_id)
                    logger.info(f"Found board: {board.id} - {board.name}")
                    
                    members = board.members.all()
                    logger.info(f"Found {members.count()} members")
                    
                    data = {
                        'members': [MemberReportSerializer(member.user).data for member in members],
                        'statistics': {
                            'total_members': members.count(),
                            'active_members': members.filter(user__task__column__board=board).distinct().count()
                        }
                    }
                    logger.info(f"Member report data: {data}")
                    return Response(data)
                except Board.DoesNotExist:
                    logger.error(f"Board not found: {board_id}")
                    return Response({'error': 'Board not found'}, status=404)
                except Exception as e:
                    logger.error(f"Error generating member report: {str(e)}", exc_info=True)
                    return Response({'error': str(e)}, status=500)

            else:
                logger.error(f"Invalid report type: {report_type}")
                return Response({'error': 'Invalid report type'}, status=400)

        except Exception as e:
            logger.error(f"Unexpected error in report generation: {str(e)}", exc_info=True)
            return Response({'error': str(e)}, status=500)