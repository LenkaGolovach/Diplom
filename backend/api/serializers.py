from rest_framework import serializers
from .models import Board, Column, Task, SubTask, FileAttachment, CustomUser, BoardMember, TaskMember, Message, MessageAttachment
from django.contrib.auth import get_user_model
from django.utils import timezone
import logging
from django.core.files.base import ContentFile
from django.conf import settings
import os
import uuid # Для генерации уникальных имен файлов

logger = logging.getLogger(__name__)

class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(required=False, allow_null=True, use_url=True)
    avatar_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'avatar', 'avatar_url']
        read_only_fields = ['id', 'avatar_url']

    def get_avatar_url(self, obj):
        request = self.context.get('request')
        if obj.avatar and hasattr(obj.avatar, 'url'):
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None

    def update(self, instance, validated_data):
        logger.info(f"UserSerializer update for user: {instance.email}. Validated_data keys: {list(validated_data.keys())}")

        if 'avatar' in validated_data:
            new_avatar_uploaded_file = validated_data.pop('avatar')

            if new_avatar_uploaded_file is None:
                logger.info("Avatar explicitly set to null. Clearing avatar.")
                if instance.avatar: 
                    instance.avatar.delete(save=False) # Удаляем старый файл из хранилища
                instance.avatar = None # Очищаем поле в модели
            else:
                logger.info(f"New avatar uploaded: {new_avatar_uploaded_file.name}. Manually saving to media.")
                
                # Определяем путь для сохранения
                # Создаем уникальное имя файла, чтобы избежать коллизий
                ext = os.path.splitext(new_avatar_uploaded_file.name)[1]
                filename = f"{uuid.uuid4()}{ext}"
                avatar_dir = os.path.join(settings.MEDIA_ROOT, 'avatars')
                os.makedirs(avatar_dir, exist_ok=True) # Убедимся, что директория существует
                filepath = os.path.join(avatar_dir, filename)
                
                logger.info(f"Attempting to save avatar to: {filepath}")
                
                try:
                    # Сохраняем файл вручную
                    with open(filepath, 'wb+') as destination:
                        for chunk in new_avatar_uploaded_file.chunks():
                            destination.write(chunk)
                    logger.info(f"Avatar saved manually to {filepath}")
                    
                    # Удаляем старый аватар, если он был
                    if instance.avatar:
                        instance.avatar.delete(save=False)
                        
                    # Присваиваем относительный путь к полю avatar
                    # Путь должен быть относительно MEDIA_ROOT
                    instance.avatar = os.path.join('avatars', filename)
                    logger.info(f"Assigned path to instance.avatar: {instance.avatar.name}")
                    
                except Exception as e:
                    logger.error(f"Error manually saving avatar ({new_avatar_uploaded_file.name}) to {filepath}: {str(e)}", exc_info=True)
                    # Если произошла ошибка, пытаемся удалить частично записанный файл, если он есть
                    if os.path.exists(filepath):
                        try:
                            os.remove(filepath)
                        except Exception as rm_err:
                            logger.error(f"Could not remove partially saved file {filepath}: {rm_err}")
                    raise serializers.ValidationError({'avatar': f'Could not save uploaded file: {str(e)}'})
        
        # Обновить другие поля
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        try:
            instance.save()
            logger.info(f"User instance saved: {instance.id}, Avatar field value: {instance.avatar.name if instance.avatar else 'None'}")
            return instance
        except Exception as e:
            logger.error(f"Error saving user model instance {instance.email}: {str(e)}", exc_info=True)
            raise serializers.ValidationError({'detail': f'An error occurred while saving user data: {str(e)}'})

class SubTaskSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    
    class Meta:
        model = SubTask
        fields = ['id', 'name', 'completed']

class FileAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileAttachment
        fields = ['id', 'name', 'file', 'uploaded_at']
        extra_kwargs = {
            'file': {'required': False},  # Разрешаем отсутствие файла при создании
            'name': {'required': False}
        }

    def create(self, validated_data):
        # Автоматически устанавливаем имя файла если не указано
        if not validated_data.get('name'):
            validated_data['name'] = validated_data['file'].name
        return super().create(validated_data)

class TaskMemberSerializer(serializers.ModelSerializer):
    id     = serializers.IntegerField(source='user.id', read_only=True)
    email = serializers.EmailField(source='user.email')
    avatar = serializers.ImageField(source='user.avatar')
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name  = serializers.CharField(source='user.last_name', read_only=True)

    class Meta:
        model = TaskMember
        fields = ['id', 'email', 'first_name', 'last_name', 'avatar', 'joined_at']

class TaskSerializer(serializers.ModelSerializer):
    subtasks = SubTaskSerializer(many=True, required=False)
    attachments = FileAttachmentSerializer(many=True, read_only=True)
    deleted_files = serializers.JSONField(
        required=False,
        write_only=True
    )
    members = TaskMemberSerializer(many=True, read_only=True)
    column_name = serializers.CharField(source='column.name', read_only=True)
    board_name = serializers.CharField(source='column.board.name', read_only=True)
    priority = serializers.ChoiceField(choices=Task.PRIORITY_CHOICES, required=False, default='medium')
    history = serializers.JSONField(read_only=True)

    class Meta:
        model = Task
        fields = ['id', 'name', 'description', 'column', 'column_name', 'board_name', 'history', 
                 'created_at', 'updated_at', 'subtasks', 'attachments', 'deleted_files', 'members', 'priority']
        read_only_fields = ['created_at', 'updated_at']
        extra_kwargs = {
            'description': {'required': False, 'allow_blank': True, 'allow_null': True},
            'column': {'required': True},
            'name': {'required': True},
            'order': {'required': False, 'default': 0, 'allow_null': True}
        }

    def validate(self, data):
        # Проверяем наличие обязательных полей
        if not data.get('name'):
            raise serializers.ValidationError({'name': 'Название задачи обязательно'})
        
        if not data.get('column'):
            raise serializers.ValidationError({'column': 'Колонка обязательна'})
        
        # Проверяем, что колонка существует и пользователь имеет к ней доступ
        try:
            column = Column.objects.get(id=data['column'].id if isinstance(data['column'], Column) else data['column'])
            if not column.board.members.filter(user=self.context['request'].user).exists():
                raise serializers.ValidationError({'column': 'У вас нет доступа к этой колонке'})
        except Column.DoesNotExist:
            raise serializers.ValidationError({'column': 'Колонка не найдена'})
        
        return data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Добавляем полные URL для файлов вложений
        request = self.context.get('request')
        if request and representation.get('attachments'):
            for attachment in representation['attachments']:
                if attachment.get('file'):
                    attachment['url'] = request.build_absolute_uri(attachment['file'])
        return representation

    def create(self, validated_data):
        try:
            subtasks_data = validated_data.pop('subtasks', [])
            request = self.context.get('request')
            
            # Обрабатываем JSON-строку подзадач
            if request and 'subtasks' in request.data:
                if isinstance(request.data['subtasks'], str):
                    try:
                        import json
                        subtasks_data = json.loads(request.data['subtasks'])
                    except json.JSONDecodeError:
                        raise serializers.ValidationError({'subtasks': 'Неверный формат подзадач'})
            
            task = Task.objects.create(**validated_data)
            
            # Создаем подзадачи, если они есть
            if subtasks_data:
                for subtask_data in subtasks_data:
                    SubTask.objects.create(
                        task=task,
                        name=subtask_data.get('name', ''),
                        completed=subtask_data.get('completed', False)
                    )
            
            # Добавляем файлы вложений, если они есть
            files = request.FILES.getlist('attachments') if request else []
            if files:
                for file in files:
                    FileAttachment.objects.create(
                        task=task,
                        file=file,
                        name=file.name
                    )
            
            return task
        except Exception as e:
            logger.error(f"Error creating task: {str(e)}")
            raise serializers.ValidationError({'error': str(e)})

    def update(self, instance, validated_data):
        subtasks_data = validated_data.pop('subtasks', [])
        request = self.context.get('request')
        deleted_files = validated_data.pop('deleted_files', [])
        if deleted_files:
            try:
                # Обработка удаленных файлов
                if isinstance(deleted_files, str):
                    import json
                    deleted_file_ids = json.loads(deleted_files)
                else:
                    deleted_file_ids = deleted_files
                    
                # Удаляем файлы
                if isinstance(deleted_file_ids, list):
                    logger.debug(f"Удаление файлов: {deleted_file_ids}")
                    FileAttachment.objects.filter(id__in=deleted_file_ids, task=instance).delete()
            except Exception as e:
                logger.error(f"Ошибка при удалении файлов: {str(e)}")

        # Обрабатываем JSON-строку подзадач
        try:
            if request and 'subtasks' in request.data:
                if isinstance(request.data['subtasks'], str):
                    import json
                    subtasks_data = json.loads(request.data['subtasks'])
                    logger.debug(f"Получены подзадачи: {subtasks_data}")
                else:
                    logger.debug(f"Подзадачи не в виде строки: {request.data['subtasks']}")
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка при разборе JSON подзадач: {e}")
            subtasks_data = []
        except Exception as e:
            logger.error(f"Неожиданная ошибка при обработке подзадач: {str(e)}")
            subtasks_data = []
        
        # Обновляем основные данные задачи
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        try:
            # Обрабатываем подзадачи
            existing_subtasks = {s.id: s for s in instance.subtasks.all()}
            logger.debug(f"Существующие подзадачи: {list(existing_subtasks.keys())}")
            
            subtasks_to_keep = []
            
            # Обновление/создание подзадач
            for subtask_data in subtasks_data:
                try:
                    subtask_id = subtask_data.get('id')
                    # Проверка на валидность id
                    if subtask_id and not isinstance(subtask_id, int):
                        try:
                            subtask_id = int(subtask_id)
                        except (ValueError, TypeError):
                            subtask_id = None
                            
                    if subtask_id and subtask_id in existing_subtasks:
                        # Обновляем существующую подзадачу
                        subtask = existing_subtasks[subtask_id]
                        subtask.name = subtask_data.get('name', subtask.name)
                        subtask.completed = subtask_data.get('completed', subtask.completed)
                        subtask.save()
                        subtasks_to_keep.append(subtask.id)
                    else:
                        # Создаем новую подзадачу
                        name = subtask_data.get('name', '').strip()
                        if name:  # Пропускаем пустые подзадачи
                            new_subtask = SubTask.objects.create(
                                task=instance,
                                name=name,
                                completed=bool(subtask_data.get('completed', False))
                            )
                            subtasks_to_keep.append(new_subtask.id)
                except Exception as e:
                    logger.error(f"Ошибка при обработке подзадачи {subtask_data}: {str(e)}")
            
            # Удаляем подзадачи, которые не в списке сохраняемых
            for subtask_id, subtask in existing_subtasks.items():
                if subtask_id not in subtasks_to_keep:
                    subtask.delete()
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении подзадач: {str(e)}")
        
        # Обрабатываем файлы вложений
        try:
            files = request.FILES.getlist('attachments') if request else []
            for file in files:
                FileAttachment.objects.create(
                    task=instance,
                    file=file,
                    name=file.name
                )
        except Exception as e:
            logger.error(f"Ошибка при добавлении файлов: {str(e)}")
    
        return instance

class ColumnSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = Column
        fields = ['id', 'name', 'color', 'board', 'tasks', 'created_at', 'updated_at', 'x_coord', 'y_coord', 'z_index']
        read_only_fields = ['created_at', 'updated_at']

class BoardMemberSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    email = serializers.EmailField(source='user.email')
    avatar = serializers.ImageField(source='user.avatar')
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name  = serializers.CharField(source='user.last_name', read_only=True)

    class Meta:
        model = BoardMember
        fields = ['user_id','email', 'first_name', 'last_name','avatar','role','joined_at']

class BoardSerializer(serializers.ModelSerializer):
    columns = ColumnSerializer(many=True, read_only=True)
    owner = UserSerializer(read_only=True)
    members = BoardMemberSerializer(many=True, read_only=True)

    class Meta:
        model = Board
        fields = '__all__'
        read_only_fields = ['owner']

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)
        
    def get_owner(self, obj):
        return {
            "id": obj.owner.id,
            "email": obj.owner.email,
            "avatar": obj.owner.avatar.url if obj.owner.avatar else None
        }

class MessageAttachmentSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    type = serializers.CharField(source='content_type') 

    class Meta:
        model = MessageAttachment
        fields = ['id', 'name', 'url', 'type', 'uploaded_at']

    def get_url(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.file.url)

class ReplyMessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'text', 'sender', 'created_at']

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    attachments = MessageAttachmentSerializer(many=True, read_only=True)
    reply_to = serializers.SerializerMethodField()
    reply_to_id = serializers.IntegerField(
        write_only=True,
        required=False,
        allow_null=True
    )
    is_deleted = serializers.BooleanField(read_only=True)
    is_edited = serializers.BooleanField(read_only=True)
    edited_at = serializers.DateTimeField(read_only=True)
    

    class Meta:
        model = Message
        fields = [
            'id', 'text', 'sender', 
            'reply_to', 'reply_to_id', 
            'attachments', 'created_at', 'session',
            'is_deleted', 'is_edited', 'edited_at'
        ]
        read_only_fields = ['id', 'created_at', 'sender', 'task']

    def create(self, validated_data):
        reply_to_id = validated_data.pop('reply_to_id', None)
        attachments_data = self.context['request'].FILES.getlist('attachments')

        # Создаем сообщение
        instance = Message.objects.create(**validated_data)

        # Добавляем вложения
        for file in attachments_data:
            MessageAttachment.objects.create(
                message=instance,
                file=file,
                name=file.name,
                content_type=file.content_type
            )

        if reply_to_id:
            instance.reply_to_id = reply_to_id
            instance.save()

        return instance

    def validate(self, data):
        if not data.get('text') and not self.context['request'].FILES:
            raise serializers.ValidationError("Сообщение не может быть пустым")
        return data

    def get_reply_to(self, obj):
        if obj.reply_to:
            return {
                "id": obj.reply_to.id,
                "text": obj.reply_to.text,
                "sender": {
                    "id": obj.reply_to.sender.id,
                    "name": obj.reply_to.sender.get_full_name(),
                    "email": obj.reply_to.sender.email
                }
            }
        return None

class MessageUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['text']
        extra_kwargs = {
            'text': {'required': True}
        }
class TaskReportSerializer(serializers.ModelSerializer):
    project = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    members = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = ['id', 'name', 'project', 'status', 'priority', 'created_at', 'updated_at', 'members']
    
    def get_project(self, obj):
        return obj.column.board.name if obj.column and obj.column.board else '-'
    
    def get_status(self, obj):
        try:
            if obj.column.name == 'Готово':
                return 'Выполнено'
            elif obj.column.name == 'В процессе':
                return 'В процессе'
            elif obj.subtasks.exists():
                completed_subtasks = obj.subtasks.filter(completed=True).count()
                total_subtasks = obj.subtasks.count()
                if completed_subtasks == 0:
                    return 'Не начато'
                elif completed_subtasks == total_subtasks:
                    return 'Выполнено'
                else:
                    return 'В процессе'
            else:
                return 'Не начато'
        except Exception as e:
            logger.error(f"Error getting task status: {str(e)}", exc_info=True)
            return 'Ошибка'
    
    def get_members(self, obj):
        try:
            return [member.email for member in obj.members.all()]
        except Exception as e:
            logger.error(f"Error getting task members: {str(e)}", exc_info=True)
            return []

class ProjectReportSerializer(serializers.ModelSerializer):
    totalTasks = serializers.SerializerMethodField()
    completedTasks = serializers.SerializerMethodField()
    inProgressTasks = serializers.SerializerMethodField()
    members = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = ['id', 'name', 'created_at', 'updated_at', 
                 'totalTasks', 'completedTasks', 'inProgressTasks', 'members', 'status']

    def get_totalTasks(self, obj):
        try:
            return Task.objects.filter(column__board=obj).count()
        except Exception as e:
            logger.error(f"Error getting total tasks: {str(e)}", exc_info=True)
            return 0

    def get_completedTasks(self, obj):
        try:
            # Считаем задачи в колонке "Готово" как завершенные
            return Task.objects.filter(column__board=obj, column__name='Готово').count()
        except Exception as e:
            logger.error(f"Error getting completed tasks: {str(e)}", exc_info=True)
            return 0

    def get_inProgressTasks(self, obj):
        try:
            # Считаем задачи в колонке "В процессе" как выполняющиеся
            return Task.objects.filter(column__board=obj, column__name='В процессе').count()
        except Exception as e:
            logger.error(f"Error getting in progress tasks: {str(e)}", exc_info=True)
            return 0

    def get_members(self, obj):
        try:
            return [{'id': member.user.id, 'username': member.user.email} for member in obj.members.all()]
        except Exception as e:
            logger.error(f"Error getting members: {str(e)}", exc_info=True)
            return []

    def get_status(self, obj):
        try:
            total_tasks = self.get_totalTasks(obj)
            completed_tasks = self.get_completedTasks(obj)
            
            if total_tasks == 0:
                return 'Нет задач'
            elif completed_tasks == total_tasks:
                return 'Завершён'
            else:
                return 'В процессе'
        except Exception as e:
            logger.error(f"Error getting status: {str(e)}", exc_info=True)
            return 'Ошибка'

class MemberReportSerializer(serializers.ModelSerializer):
    totalTasks = serializers.SerializerMethodField()
    completedTasks = serializers.SerializerMethodField()
    inProgressTasks = serializers.SerializerMethodField()
    projects = serializers.SerializerMethodField()
    lastActivity = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'totalTasks', 'completedTasks', 'inProgressTasks', 'projects', 'lastActivity']
    
    def get_totalTasks(self, obj):
        return Task.objects.filter(members=obj).count()
    
    def get_completedTasks(self, obj):
        return Task.objects.filter(members=obj, column__name='Готово').count()
    
    def get_inProgressTasks(self, obj):
        return Task.objects.filter(members=obj, column__name='В процессе').count()
    
    def get_projects(self, obj):
        return [board.name for board in Board.objects.filter(members__user=obj)]
    
    def get_lastActivity(self, obj):
        last_task = Task.objects.filter(members=obj).order_by('-updated_at').first()
        return last_task.updated_at if last_task else None

class HistoryEventSerializer(serializers.Serializer):
    user = serializers.EmailField()
    action = serializers.CharField()
    ts = serializers.IntegerField()