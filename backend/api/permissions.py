from rest_framework import permissions

class IsBoardMember(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.column.board.members.filter(user=request.user).exists()