from rest_framework import mixins, viewsets
from tdata.lib.image_name_encipher import get_image_url
from pretask.serializers import PrePageColTaskSerializer, PrePageColVerifyTaskSerializer, ColRectSerializer, ColRectWriterSerializer
from pretask.models import PrePageColVerifyTask, ColRect, PrePageColTask
from rest_framework.response import Response
from rect.models import *
from rest_framework.decorators import detail_route, list_route
from ccapi.utils.task import retrieve_prepagecoltask, retrieve_prepagecolverifytask
from django.db import transaction
from rest_framework.decorators import permission_classes
from django.utils.timezone import localtime, now
from functools import reduce

def ilen(iterable):
    return reduce(lambda sum, element: sum + 1, iterable, 0)


class RectBulkOpMixin(object):
    """
    任务回顾
    """
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if (not request.user.is_admin):
            if (instance.owner != request.user):
                return Response({"status": -1,
                                 "msg": "No Permission!"})
        serializer = self.get_serializer(instance)
        if isinstance(instance, PrePageColTask):
            image_url = instance.page.image_url
            return Response({"status": instance.status,
                            "rects": instance.rect_set,
                            "image_url": image_url,
                            "page_info": instance.page.page_info,
                            "current_x": instance.current_x,
                            "current_y": instance.current_y,
                            "task_id": instance.pk})
        if isinstance(instance, PrePageColVerifyTask):
            image_url = instance.page.image_url
            return Response({"status": instance.status,
                            "rects": instance.rect_set,
                            "image_url": image_url,
                            "page_info": instance.page.page_info,
                            "current_x": instance.current_x,
                            "current_y": instance.current_y,
                            "task_id": instance.pk})
        return Response(serializer.data)

    @list_route( methods=['get'], url_path='history')
    def history(self, request):
        queryset = self.queryset.filter(owner=request.user).order_by('status', '-update_date')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)



class PrePageColTaskViewSet(RectBulkOpMixin,
                      mixins.RetrieveModelMixin,
                      viewsets.GenericViewSet):
    queryset = PrePageColTask.objects.all()
    serializer_class = PrePageColTaskSerializer

    @list_route(methods=['get'], url_path='obtain')
    def obtain(self, request):
        staff = request.user
        task = retrieve_prepagecoltask(staff)
        if not task:
            return Response({"status": -1,
                             "msg": "All tasks have been done!"})
        image_url = task.page.image_url
        return Response({"status": task.status,
                        "rects": task.rect_set,
                        "image_url": image_url,
                        "page_info": task.page.page_info,
                        "current_x": task.current_x,
                        "current_y": task.current_y,
                        "task_id": task.pk})


    @detail_route(methods=['post'], url_path='done')
    @transaction.atomic
    def tobe_done(self, request, pk):
        task = PrePageColTask.objects.get(pk=pk)
        if (task.owner != request.user):
            return Response({"status": -1,
                             "msg": "No Permission!"})
        if PrePageColVerifyTask.objects.filter(schedule=task.schedule, page=task.page, status__gte=TaskStatus.HANDLING).first():
            return Response({"status": -1,
                             "msg": "审定任务已开始，保存已屏蔽!"})
        if 'current_x' in request.data:
            task.current_x = request.data['current_x']
            task.current_y = request.data['current_y']
            task.save(update_fields=['current_x', 'current_y'])
        rects = request.data['rects']
        _rects = [rect for rect in filter(lambda x: x['op'] != 3, rects)]
        task.rect_set = _rects
        task.update_date = localtime(now()).date()
        task.status = TaskStatus.COMPLETED
        task.save(update_fields=["status", "update_date", 'rect_set'])
        task.create_new_prepagetask_verify()
        return Response({"status": 0, "task_id": pk})

    @detail_route(methods=['post'], url_path='save')
    @transaction.atomic
    def temp_save(self, request, pk):
        task = PrePageColTask.objects.get(pk=pk)
        if (task.owner != request.user):
            return Response({"status": -1,
                             "msg": "No Permission!"})
        if PrePageColVerifyTask.objects.filter(schedule=task.schedule, page=task.page, status__gte=TaskStatus.HANDLING).first():
            return Response({"status": -1, "msg": "审定任务已开始，保存已屏蔽!"})
        if 'current_x' in request.data:
            task.current_x = request.data['current_x']
            task.current_y = request.data['current_y']
            task.save(update_fields=['current_x', 'current_y'])
        rects = request.data['rects']
        _rects = [rect for rect in filter(lambda x: x['op'] != 3, rects)]
        task.rect_set = _rects
        task.save(update_fields=['rect_set'])
        return Response({"status": 0,
                            "task_id": pk })




class PrePageColVerifyTaskViewSet(RectBulkOpMixin,
                      mixins.RetrieveModelMixin,
                      viewsets.GenericViewSet):
    queryset = PrePageColVerifyTask.objects.all()
    serializer_class = PrePageColVerifyTaskSerializer

    @list_route(methods=['get'], url_path='obtain')
    def obtain(self, request):
        staff = request.user
        task = retrieve_prepagecolverifytask(staff)
        if not task:
            return Response({"status": -1,
                             "msg": "All tasks have been done!"})
        image_url = task.page.image_url
        return Response({"status": task.status,
                        "rects": task.rect_set,
                        "image_url": image_url,
                        "page_info": task.page.page_info,
                        "current_x": task.current_x,
                        "current_y": task.current_y,
                        "task_id": task.pk})




    @detail_route(methods=['post'], url_path='done')
    @transaction.atomic
    def tobe_done(self, request, pk):
        task = PrePageColVerifyTask.objects.get(pk=pk)
        if (task.owner != request.user):
            return Response({"status": -1,
                             "msg": "No Permission!"})
        if 'current_x' in request.data:
            task.current_x = request.data['current_x']
            task.current_y = request.data['current_y']
            task.save(update_fields=['current_x', 'current_y'])
        rects = request.data['rects']
        _rects = [rect for rect in filter(lambda x: x['op'] != 3, rects)]
        task.rect_set = _rects
        task.update_date = localtime(now()).date()
        task.status = TaskStatus.COMPLETED
        task.save(update_fields=["status", "update_date", 'rect_set'])

        return Response({"status": 0,
                            "task_id": pk })

    @detail_route(methods=['post'], url_path='redo')
    @transaction.atomic
    def task_redo(self, request, pk):
        task = PrePageColVerifyTask.objects.get(pk=pk)
        if (task.owner != request.user):
            return Response({"status": -1,
                             "msg": "No Permission!"})
        task.redo()
        return Response({"status": 0,
                            "task_id": pk })
