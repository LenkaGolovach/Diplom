from rest_framework import serializers
from .models import Board, Column, Task, SubTask, FileAttachment, CustomUser, BoardMember, TaskMember, MessageAttachment, Message
import logging

logger = logging.getLogger(__name__)

class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'avatar']
        read_only_fields = ['id']

    def update(self, instance, validated_data):
        # Обрабатываем загрузку аватара
        avatar = validated_data.pop('avatar', None)
        if avatar:
            instance.avatar = avatar
        return super().update(instance, validated_data)

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
    email = serializers.EmailField(source='user.email')
    avatar = serializers.ImageField(source='user.avatar')

    class Meta:
        model = TaskMember
        fields = ['email', 'avatar', 'joined_at']

class TaskSerializer(serializers.ModelSerializer):
    subtasks = SubTaskSerializer(many=True, required=False)
    attachments = FileAttachmentSerializer(many=True, read_only=True)
    deleted_files = serializers.JSONField(
        required=False,
        write_only=True
    )
    members = TaskMemberSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

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
        subtasks_data = validated_data.pop('subtasks', [])
        request = self.context.get('request')
        
        # Обрабатываем JSON-строку подзадач
        if request and 'subtasks' in request.data:
            if isinstance(request.data['subtasks'], str):
                try:
                    import json
                    subtasks_data = json.loads(request.data['subtasks'])
                except json.JSONDecodeError:
                    pass
        
        task = Task.objects.create(**validated_data)
        
        # Создаем подзадачи
        for subtask_data in subtasks_data:
            SubTask.objects.create(
                task=task,
                name=subtask_data.get('name', ''),
                completed=subtask_data.get('completed', False)
            )
        
        # Добавляем файлы вложений
        files = request.FILES.getlist('attachments') if request else []
        for file in files:
            FileAttachment.objects.create(
                task=task,
                file=file,
                name=file.name
            )
        
        return task

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
        fields = ['id', 'name', 'color', 'board', 'tasks', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class BoardMemberSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email')
    avatar = serializers.ImageField(source='user.avatar')

    class Meta:
        model = BoardMember
        fields = ['email', 'avatar', 'role', 'joined_at']

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
            'attachments', 'created_at',
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