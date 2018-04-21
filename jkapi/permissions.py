from rest_framework import permissions
from django.shortcuts import get_object_or_404

from tasks.models import Task

class IsTaskPickedByCurrentUser(permissions.BasePermission):
    """
    确定任务是否为当前用户所领取
    """

    def has_permission(self, request, view):
        task_id = view.kwargs['task_id']
        try:
            task = Task.objects.get(pk=task_id)
            if request.user.is_admin or task.picker == request.user:
                view.task = task
                return True
        except:
            pass
        return False

class IsTaskPickedByCurrentUserOrReadOnly(permissions.BasePermission):
    """
    如果任务为当前用户所领取，有可写权限；否则只读
    """

    def has_permission(self, request, view):
        task_id = view.kwargs['task_id']
        try:
            task = Task.objects.get(pk=task_id)
            if request.method in permissions.SAFE_METHODS:
                return True
            if request.user.is_admin or task.picker == request.user:
                view.task = task
                return True
        except:
            pass
        return False

class IsRoleOrReadOnly(permissions.BasePermission):
    """
    The request is authenticated as a user with a specific role, or is a read-only request.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        role_ids = [role.id for role in request.user.roles.all()]
        return self.role_id in role_ids

class CanProcessJudgeFeedback(IsRoleOrReadOnly):
    role_id = 3

