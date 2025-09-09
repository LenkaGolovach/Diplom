from rest_framework import permissions
from rest_framework.permissions import BasePermission
from .models import BoardMember, Task

class IsBoardMember(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.column.board.members.filter(user=request.user).exists()

class IsTaskMember(BasePermission):
    def has_permission(self, request, view):
        try:
            task = Task.objects.get(id=view.kwargs.get('task_pk'))
            return task.column.board.members.filter(user=request.user).exists()
        except (Task.DoesNotExist, KeyError):
            return False