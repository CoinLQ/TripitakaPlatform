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