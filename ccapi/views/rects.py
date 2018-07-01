from rest_framework import mixins, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rect.serializers import ScheduleSerializer, CCTaskSerializer, \
                PageTaskSerializer
from ccapi.serializer import PageRectSerializer, RectSerializer
from rect.models import Page, PageRect, Rect, \
                        Schedule, CharClassifyPlan, CCTask, ClassifyTask, PageTask

from ccapi.pagination import StandardPagination
import math
from rest_framework.response import Response
from rest_framework.decorators import detail_route
from django.shortcuts import get_object_or_404
import re
from rect.lib import get_ocr_text
import urllib
from base64 import b64encode

class PageRectViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PageRect.objects.all()
    serializer_class = PageRectSerializer

class RectResultsSetPagination(StandardPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class RectViewSet(viewsets.ReadOnlyModelViewSet, mixins.ListModelMixin):
    queryset = Rect.objects.all()
    serializer_class = RectSerializer
    pagination_class = RectResultsSetPagination

    @list_route(methods=['get'], url_path='ccreview')
    def ccreview(self, request):
        schedule_id = self.request.query_params.get('schedule_id', None)
        cc = self.request.query_params.get('cc', 0.96)
        #page = self.request.query_params.get('page', 1)
        #page_size = self.request.query_params.get('page_size', 20)
        try:
            schedule = Schedule.objects.get(pk=schedule_id)
        except Schedule.DoesNotExist:
            return Response({"status": -1,
                             "msg": "not found schedule instance!"})

        reelRids = [reel.rid for reel in schedule.reels.all()]
        if len(reelRids) <= 0 :
            return Response({"status": -1,
                             "msg": "The schedule does not select reels!"})
        rects = Rect.objects.filter(reel__in=reelRids, cc__lte=cc).order_by("-cc")

        page = self.paginate_queryset(rects)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(rects, many=True)
        return Response(serializer.data)

    @list_route(methods=['get'], url_path='cpreview')
    def cpreview(self, request):
        ccpid = self.request.query_params.get('ccpid', None)
        wcc = self.request.query_params.get('wcc', None)
        #char = self.request.query_params.get('char', None)
        ccp = CharClassifyPlan.objects.get(id=ccpid)
        char = ccp.ch
        schedule_id = ccp.schedule_id

        try:
            schedule = Schedule.objects.get(pk=schedule_id)
        except Schedule.DoesNotExist:
            return Response({"status": -1,
                             "msg": "not found schedule instance!"})

        reelRids = [reel.rid for reel in schedule.reels.all()]
        if len(reelRids) <= 0 :
            return Response({"status": -1,
                             "msg": "The schedule does not select reels!"})
        rects = Rect.objects.filter(reel__in=reelRids, ch=char).order_by("-wcc")

        page = self.paginate_queryset(rects)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(rects, many=True)
        return Response(serializer.data)

    @list_route(methods=['get'], url_path='cp_wcc_count')
    def cp_wcc_count(self, request):
        ccpid = self.request.query_params.get('ccpid', None)
        wcc = self.request.query_params.get('wcc', None)
        if not wcc:
            return Response({"status": -1,
                             "msg": "pls provide param wcc."})

        ccp = CharClassifyPlan.objects.get(id=ccpid)
        char = ccp.ch
        schedule_id = ccp.schedule_id

        try:
            schedule = Schedule.objects.get(pk=schedule_id)
        except Schedule.DoesNotExist:
            return Response({"status": -1,
                             "msg": "not found schedule instance!"})

        reelRids = [reel.rid for reel in schedule.reels.all()]
        if len(reelRids) <= 0:
            return Response({"status": -1,
                             "msg": "The schedule does not select reels!"})
        count = Rect.objects.filter(reel__in=reelRids, ch=char, wcc__gte=wcc).order_by("-wcc").count()

        #page_size = self.paginator.get_page_size(request)
        #actual_page = math.ceil(count / page_size)
        return Response({'status': 0,
                         'msg': 'success',
                         'data': {
                             'count': count
                         }})

    def retrieve(self, request, *args, **kwargs):
        instance = get_object_or_404(Rect, cid=kwargs['pk'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @detail_route(methods=['get'], url_path='col_rects')
    def col_rects(self, request, pk):
        staff = request.user
        rect = get_object_or_404(Rect, cid=pk)
        col_id = rect.cid[:-3]
        pattern = re.compile(r'{}'.format(col_id))

        col_rects = list(filter(lambda x: pattern.search(x.cid) and pk != x.cid, Rect.objects.filter(page_pid=rect.page_pid).all()))
        rects = RectSerializer(data=col_rects, many=True)
        rects.is_valid()
        return Response({"status": 0,
                "rects": rects.data,
                "cid": pk})



    @list_route(methods=['post'], url_path='get_ocr_text')
    def getOCRText(self, request):

        class DefaultDict(dict):
            def __missing__(self, key):
                return None
        requestJson = DefaultDict(request.data)
        imgBase64 = requestJson['img_data']
        picPath = requestJson['img_url']
        _id = requestJson['id']

        if imgBase64:
            respData = get_ocr_text.testAPI(imgBase64)
            jsonData = {'status': respData['code'], 'msg': respData['message'],
                        'id': _id, 'rects': get_ocr_text.jsonToNewJson(respData)}
        elif picPath:
            image = urllib.request.urlopen(picPath).read()
            respData = get_ocr_text.testAPI(b64encode(image))
            if 'code' in respData:
                status = respData['code']
                if int(status) == 0:
                    status = 200 + abs(status)
                elif int(status) < 0:
                    status = 400 + abs(status)
                else:
                    status = 500 + abs(status)
            else:
                status = 404

            rects = get_ocr_text.jsonToNewJson(respData)

            jsonData = {'status': status, 'id': _id, 'msg': respData['message'], 'rects': rects}
        else:
            jsonData = {'status': -1, 'msg': 'parameters error!'}

        return Response(jsonData)


class ScheduleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
