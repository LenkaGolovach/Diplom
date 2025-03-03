from rest_framework import serializers
from .models import Board, Column, Task, SubTask, FileAttachment

class SubTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubTask
        fields = ['id', 'name', 'completed', 'created_at', 'updated_at']

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
    attachments = FileAttachmentSerializer(many=True, required=False, read_only=True)

    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def create(self, validated_data):
        # Автоматически устанавливаем порядок
        validated_data['order'] = Task.objects.filter(
            column=validated_data['column']
        ).count()
        
        subtasks_data = validated_data.pop('subtasks', [])
        task = Task.objects.create(**validated_data)
        
        # Создаем подзадачи
        for subtask_data in subtasks_data:
            SubTask.objects.create(task=task, **subtask_data)
            
        return task

    def update(self, instance, validated_data):
        subtasks_data = validated_data.pop('subtasks', [])
        
        # Обновляем основную задачу
        instance = super().update(instance, validated_data)
        
        # Обновляем подзадачи
        instance.subtasks.all().delete()
        for subtask_data in subtasks_data:
            SubTask.objects.create(task=instance, **subtask_data)
            
        return instance

class ColumnSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Column
        fields = ['id', 'name', 'color', 'board', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class BoardSerializer(serializers.ModelSerializer):
    columns = ColumnSerializer(many=True, read_only=True)
    owner = serializers.ReadOnlyField(source='owner.email')

    class Meta:
        model = Board
        fields = '__all__'
        #read_only_fields = ['owner']
