from rest_framework import mixins, viewsets
from rect.serializers import CCTaskSerializer, DelTaskSerializer, ClassifyTaskSerializer, \
                PageTaskSerializer
from ccapi.serializer import RectSerializer, PageRectSerializer, DeletionCheckItemSerializer, \
                RectWriterSerializer
from rect.models import CCTask, ClassifyTask, PageTask, Rect, PageRect, OpStatus, \
                        DeletionCheckItem, DelTask, TaskStatus
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route
from ccapi.utils.task import retrieve_cctask, retrieve_classifytask, \
                           retrieve_pagetask, retrieve_deltask
from django.db import transaction
from rest_framework.permissions import AllowAny
from rest_framework.decorators import permission_classes
from functools import reduce

def ilen(iterable):
    return reduce(lambda sum, element: sum + 1, iterable, 0)


class RectBulkOpMixin(object):
    def task_done(self, rects, task):
        rectset = RectWriterSerializer(data=rects, many=True)
        rectset.is_valid()
        Rect.bulk_insert_or_replace(rectset.data)
        DeletionCheckItem.create_from_rect(rects, task)
        task.done()

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
        if isinstance(instance, CCTask) or isinstance(instance, ClassifyTask):
            return Response({"status": 0,
                        "rects": instance.rect_set,
                        "task_id": instance.pk})
        if isinstance(instance, PageTask):
            pagerect_ids = [page['id'] for page in instance.page_set]
            pages = PageRect.objects.filter(id__in=pagerect_ids).select_related('page')
            page_id = pages[0].page_id
            _rects = Rect.objects.filter(page_code=page_id).all()
            rects = RectSerializer(data=_rects, many=True)
            rects.is_valid()
            return Response({"status": 0,
                            "rects": rects.data,
                            "page_id": page_id,
                            "task_id": instance.pk})
        return Response(serializer.data)

    @list_route( methods=['get'], url_path='history')
    def history(self, request):
        queryset = self.queryset.filter(owner=request.user, status=TaskStatus.COMPLETED)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class CCTaskViewSet(RectBulkOpMixin,
                    mixins.RetrieveModelMixin,
                    viewsets.GenericViewSet):
    queryset = CCTask.objects.all()
    serializer_class = CCTaskSerializer

    @detail_route(methods=['post'], url_path='done')
    @transaction.atomic
    def tobe_done(self, request, pk):
        task = CCTask.objects.get(pk=pk)

        if (task.owner != request.user):
            return Response({"status": -1,
                             "msg": "No Permission!"})
        ids = [x['id'] for x in  task.rect_set]
        req_ids = [x['id'] for x in  request.data['rects']]
        if ilen(filter(lambda x: x not in ids, req_ids)) != 0:
            return Response({"status": -1,
                             "msg": u"有些字块不属于你的任务!"})
        rects = request.data['rects']
        task.rect_set = request.data['rects']
        self.task_done(rects, task)
        return Response({"status": 0,
                            "task_id": pk })


    @detail_route(methods=['post'], url_path='emergen')
    def emergen(self, request, pk):
        task = CCTask.objects.get(pk=pk)
        if (task.owner != request.user):
            return Response({"status": -1,
                             "msg": "No Permission!"})
        task.emergen()
        return Response({
            "status": 0,
            "task_id": pk
        })

    @list_route( methods=['get'], url_path='obtain')
    def obtain(self, request):
        staff = request.user
        task = retrieve_cctask(staff)
        if not task:
            return Response({"status": -1,
                             "msg": "All tasks has been done!"})
        return Response({"status": 0,
                        "rects": task.rect_set,
                        "task_id": task.pk})


class ClassifyTaskViewSet(RectBulkOpMixin,
                          mixins.RetrieveModelMixin,
                          viewsets.GenericViewSet):
    queryset = ClassifyTask.objects.all()
    serializer_class = ClassifyTaskSerializer

    @detail_route(methods=['post'], url_path='done')
    @transaction.atomic
    def tobe_done(self, request, pk):
        task = ClassifyTask.objects.get(pk=pk)

        if (task.owner != request.user):
            return Response({"status": -1,
                             "msg": "No Permission!"})
        ids = [x['id'] for x in  task.rect_set]
        req_ids = [x['id'] for x in  request.data['rects']]
        if ilen(filter(lambda x: x not in ids, req_ids)) != 0:
            return Response({"status": -1,
                             "msg": u"有些字块不属于你的任务!"})
        rects = request.data['rects']
        task.rect_set = request.data['rects']
        self.task_done(rects, task)
        return Response({"status": 0,
                            "task_id": pk })



    @detail_route(methods=['post'], url_path='emergen')
    def emergen(self, request, pk):
        task = ClassifyTask.objects.get(pk=pk)
        if (task.owner != request.user):
            return Response({"status": -1,
                             "msg": "No Permission!"})
        task.emergen()
        return Response({
            "status": 0,
            "task_id": pk
        })

    @list_route(methods=['get'], url_path='obtain')
    def obtain(self, request):
        staff = request.user
        task = retrieve_classifytask(staff)
        if not task:
            return Response({"status": -1,
                             "msg": "All tasks has been done!"})
        return Response({"status": 0,
                        "rects": task.rect_set,
                        "char_set": task.char_set,
                        "task_id": task.pk})


class PageTaskViewSet(RectBulkOpMixin,
                      mixins.RetrieveModelMixin,
                      viewsets.GenericViewSet):
    queryset = PageTask.objects.all()
    serializer_class = PageTaskSerializer

    @list_route(methods=['get'], url_path='obtain')
    def obtain(self, request):
        staff = request.user
        task = retrieve_pagetask(staff)
        if not task:
            return Response({"status": -1,
                             "msg": "All tasks has been done!"})
        pagerect_ids = [page['id'] for page in task.page_set]
        pages = PageRect.objects.filter(id__in=pagerect_ids).select_related('page')
        page_id = pages[0].page_id
        _rects = Rect.objects.filter(page_code=page_id).all()
        rects = RectSerializer(data=_rects, many=True)
        rects.is_valid()
        page = pages[0].page
        # TODO: test, check
        # TODO: s3_id改名成page_code        
        return Response({"status": 0,
                        "rects": rects.data,
                        "page_id": page_id,
                        "s3_id": page.page_code, 
                        "task_id": task.pk})


    @detail_route(methods=['post'], url_path='emergen')
    def emergen(self, request, pk):
        task = PageTask.objects.get(pk=pk)
        if (task.owner != request.user):
            return Response({"status": -1,
                             "msg": "No Permission!"})
        task.emergen()
        return Response({
            "status": 0,
            "task_id": pk
        })


    @detail_route(methods=['post'], url_path='done')
    @transaction.atomic
    def tobe_done(self, request, pk):
        task = PageTask.objects.get(pk=pk)
        if (task.owner != request.user):
            return Response({"status": -1,
                             "msg": "No Permission!"})
        rects = request.data['rects']
        self.task_done(rects, task)
        return Response({"status": 0,
                            "task_id": pk })



class DelTaskViewSet(RectBulkOpMixin,
                     mixins.RetrieveModelMixin,
                     viewsets.GenericViewSet):
    queryset = DelTask.objects.all()
    serializer_class = DelTaskSerializer

    @detail_route(methods=['post'], url_path='done')
    @transaction.atomic
    def tobe_done(self, request, pk):
        task = DelTask.objects.get(pk=pk)
        can_write_fields = getattr(DeletionCheckItemSerializer.Meta, 'can_write_fields', [])
        if (task.owner != request.user):
            return Response({"status": -1,
                             "msg": "No Permission!"})
        rects = request.data['rects']

        _items = [dict((k,v) for (k,v) in filter(lambda x: x[0] in can_write_fields, rect_del.items())) for rect_del in rects]

        del_items = [DeletionCheckItem(**_rect) for _rect in _items]
        for it in del_items:
            it.verifier = task.owner
        DeletionCheckItem.objects.bulk_update(del_items, update_fields=['result', 'verifier'])

        task.done()
        task.execute()
        return Response({"status": 0, "task_id": pk })


    @detail_route(methods=['post'], url_path='emergen')
    def emergen(self, request, pk):
        task = DelTask.objects.get(pk=pk)
        if (task.owner == request.user):
            return Response({"status": -1,
                             "msg": "Action Denied!"})
        task.emergen()
        return Response({
            "status": 0,
            "task_id": pk
        })

    @list_route( methods=['get'], url_path='obtain')
    def obtain(self, request):
        staff = request.user
        task = retrieve_deltask(staff)
        if not task:
            return Response({"status": -1,
                             "msg": "All tasks has been done!"})
        queryset = task.del_task_items.prefetch_related('modifier', 'verifier')

        items = DeletionCheckItemSerializer(data=queryset, many=True)
        items.is_valid()
        if not task:
            return Response({"status": -1,
                             "msg": "All tasks has been done!"})
        return Response({"status": 0,
                        "rects": items.data,
                        "task_id": task.pk})
