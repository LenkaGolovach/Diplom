from rest_framework import serializers
from .models import Board, Column, Task, SubTask, FileAttachment

class SubTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubTask
        fields = '__all__'

class FileAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileAttachment
        fields = '__all__'

class TaskSerializer(serializers.ModelSerializer):
    subtasks = SubTaskSerializer(many=True, required=False)
    files = FileAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = '__all__'

    def create(self, validated_data):
        subtasks_data = validated_data.pop('subtasks', [])
        task = Task.objects.create(**validated_data)
        for subtask_data in subtasks_data:
            SubTask.objects.create(task=task, **subtask_data)
        return task

    def update(self, instance, validated_data):
        subtasks_data = validated_data.pop('subtasks', [])
        instance = super().update(instance, validated_data)
        instance.subtasks.all().delete()
        for subtask_data in subtasks_data:
            SubTask.objects.create(task=instance, **subtask_data)
        return instance

class ColumnSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = Column
        fields = '__all__'

class BoardSerializer(serializers.ModelSerializer):
    columns = ColumnSerializer(many=True, read_only=True)

    class Meta:
        model = Board
        fields = '__all__'
        read_only_fields = ['owner']
