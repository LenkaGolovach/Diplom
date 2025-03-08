from rest_framework import serializers
from .models import Board, Column, Task, SubTask, FileAttachment, CustomUser
import logging

logger = logging.getLogger(__name__)

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

class TaskSerializer(serializers.ModelSerializer):
    subtasks = SubTaskSerializer(many=True, required=False)
    attachments = FileAttachmentSerializer(many=True, read_only=True)
    deleted_files = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True
    )

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
            FileAttachment.objects.filter(id__in=deleted_files, task=instance).delete()

        # Обрабатываем JSON-строку подзадач
        if request and 'subtasks' in request.data:
            if isinstance(request.data['subtasks'], str):
                try:
                    import json
                    subtasks_data = json.loads(request.data['subtasks'])
                except json.JSONDecodeError:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to parse subtasks JSON: {request.data['subtasks']}")
        
        # Обновляем основные данные задачи
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Обрабатываем подзадачи
        existing_subtasks = {s.id: s for s in instance.subtasks.all()}
        
        subtasks_to_keep = []
        
        # Обновление/создание подзадач
        for subtask_data in subtasks_data:
            subtask_id = subtask_data.get('id')
            if subtask_id and subtask_id in existing_subtasks:
                # Обновляем существующую подзадачу
                subtask = existing_subtasks[subtask_id]
                subtask.name = subtask_data.get('name', subtask.name)
                subtask.completed = subtask_data.get('completed', subtask.completed)
                subtask.save()
                subtasks_to_keep.append(subtask.id)
            else:
                # Создаем новую подзадачу
                new_subtask = SubTask.objects.create(
                    task=instance,
                    name=subtask_data.get('name', ''),
                    completed=subtask_data.get('completed', False)
                )
                subtasks_to_keep.append(new_subtask.id)
        
        # Удаляем подзадачи, которые не в списке сохраняемых
        for subtask_id, subtask in existing_subtasks.items():
            if subtask_id not in subtasks_to_keep:
                subtask.delete()
        
        # Обрабатываем файлы вложений
        files = request.FILES.getlist('attachments') if request else []
        for file in files:
            FileAttachment.objects.create(
                task=instance,
                file=file,
                name=file.name
            )
    
        return instance
        
class ColumnSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = Column
        fields = ['id', 'name', 'color', 'board', 'tasks', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class BoardSerializer(serializers.ModelSerializer):
    columns = ColumnSerializer(many=True, read_only=True)
    owner = serializers.ReadOnlyField(source='owner.email')

    class Meta:
        model = Board
        fields = '__all__'
        read_only_fields = ['owner']

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)

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
