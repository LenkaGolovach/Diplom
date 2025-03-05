from rest_framework import serializers
from .models import Board, Column, Task, SubTask, FileAttachment

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
    attachments = FileAttachmentSerializer(many=True, read_only=True)  # Только для чтения

    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def create(self, validated_data):
        subtasks_data = validated_data.pop('subtasks', [])
        task = super().create(validated_data)
        
        # Создаем подзадачи
        for subtask_data in subtasks_data:
            SubTask.objects.create(task=task, **subtask_data)
        
        # Обработка файлов
        if 'request' in self.context:
            files = self.context['request'].FILES.getlist('attachments')
            for file in files:
                FileAttachment.objects.create(
                    task=task,
                    file=file,
                    name=file.name
                )
        return task

    def update(self, instance, validated_data):
        subtasks_data = validated_data.pop('subtasks', [])
        instance = super().update(instance, validated_data)
        
        # Обновление подзадач
        existing_subtasks = {s.id: s for s in instance.subtasks.all()}
        
        # Обновляем или создаем подзадачи
        for subtask_data in subtasks_data:
            subtask_id = subtask_data.get('id')
            if subtask_id and subtask_id in existing_subtasks:
                subtask = existing_subtasks[subtask_id]
                subtask.name = subtask_data.get('name', subtask.name)
                subtask.completed = subtask_data.get('completed', subtask.completed)
                subtask.save()
                del existing_subtasks[subtask_id]
            else:
                SubTask.objects.create(task=instance, **subtask_data)
        
        # Удаляем оставшиеся подзадачи
        for subtask in existing_subtasks.values():
            subtask.delete()
        
        # Добавляем новые файлы
        if 'request' in self.context:
            files = self.context['request'].FILES.getlist('attachments')
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
        #read_only_fields = ['owner']
