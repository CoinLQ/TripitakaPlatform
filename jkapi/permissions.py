from rest_framework import permissions
from django.shortcuts import get_object_or_404
from django.utils import timezone

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
        if self.role_id in role_ids:
            return True
        return False

class CanProcessFeedback(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        role_ids = [role.id for role in request.user.roles.all()]
        if self.role_id in role_ids:
            request.data['processor'] = request.user.id
            request.data['processed_at'] = timezone.now()
            return True
        return False

class CanProcessJudgeFeedback(CanProcessFeedback):
    role_id = 3

class CanProcessLQPunctFeedback(CanProcessFeedback):
    role_id = 17

class CanSubmitFeedbackOrReadOnly(permissions.BasePermission):
    """
    类似IsAuthenticatedOrReadOnly，对于通过用户认证的请求，增加fb_user参数
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user and request.user.is_authenticated:
            request.data['fb_user'] = request.user.id
            return True
        return False

class CanViewMyFeedback(permissions.BasePermission):
    """
    将当前用户保存到view.user
    """
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            view.user = request.user
            return True
        return False