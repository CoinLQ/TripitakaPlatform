from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.db.models import Q
from django.conf import settings

from rest_framework import mixins, viewsets, generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from tdata.models import *
from tasks.models import *
from jkapi.serializers import *
from jkapi.permissions import *
from tasks.task_controller import judge_submit_result_async, publish_judge_result_async
from tasks.common import clean_separators

import json, re
from operator import attrgetter, itemgetter

class JudgePagination(PageNumberPagination):
    page_size = 5

class DiffSegResultList(generics.ListAPIView):
    serializer_class = DiffSegResultSerializer
    pagination_class = JudgePagination
    permission_classes = (IsTaskPickedByCurrentUser, )

    def get_queryset(self):
        queryset = DiffSegResult.objects.filter(task_id=self.task.id)
        if 'all_equal' in self.request.GET:
            all_equal = self.request.GET.get('all_equal')
            return queryset.filter(all_equal=all_equal).order_by('diffseg__base_pos')
        if 'diffseg_id' in self.request.GET:
            diffseg_id_lst = self.request.GET.get('diffseg_id').split(',')
            return queryset.filter(diffseg_id__in=diffseg_id_lst).order_by('diffseg__base_pos')
        return queryset.order_by('id')

class DiffSegResultUpdate(generics.UpdateAPIView):
    serializer_class = DiffSegResultSimpleSerializer
    permission_classes = (IsTaskPickedByCurrentUser, )

    def get_queryset(self):
        return DiffSegResult.objects.filter()

class JudgeTaskDetail(APIView):
    permission_classes = (IsTaskPickedByCurrentUser, )
    
    def get(self, request, task_id, format=None):
        base_text = clean_separators(self.task.reeldiff.base_text.body)
        diffseg_pos_lst = self.task.reeldiff.diffseg_pos_lst
        base_reel = self.task.reeldiff.base_text.reel
        tripitaka_info = {}
        lqsutra = self.task.lqreel.lqsutra
        for sutra in lqsutra.sutra_set.all():
            try:
                reel = Reel.objects.get(sutra=sutra, reel_no=self.task.lqreel.reel_no)
                tripitaka_info[sutra.tripitaka_id] = {
                    'url_prefix': reel.url_prefix(),
                    'start_vol_page': reel.start_vol_page,
                }
            except:
                pass
        puncts = base_reel.punct_set.all()[0:1]
        punct = puncts[0]
        punctuation = json.loads(punct.punctuation)
        head_len = len(clean_separators(punct.reeltext.head))
        new_punctuation = []
        for p in punctuation:
            pos = p[0] - head_len
            if pos > 0:
                new_punctuation.append([pos, p[1]])
        response = {
            'task_id': task_id,
            'status': self.task.status,
            'is_verify': (self.task.typ == Task.TYPE_JUDGE_VERIFY),
            'base_text': base_text,
            'diffseg_pos_lst': json.loads(diffseg_pos_lst),
            'punct_lst': new_punctuation,
            'base_tripitaka_id': base_reel.sutra.tripitaka_id,
            'image_url_prefix': settings.IMAGE_URL_PREFIX,
            'tripitaka_info': tripitaka_info,
            }
        return Response(response)

class FinishJudgeTask(APIView):
    permission_classes = (IsTaskPickedByCurrentUser, )

    def post(self, request, task_id, format=None):
        objs = list(DiffSegResult.objects.filter(task_id=task_id, selected=0)[0:1])
        all_selected = (len(objs) == 0)
        if all_selected:
            self.task.status = Task.STATUS_FINISHED
            self.task.save(update_fields=['status'])
            if self.task.typ == Task.TYPE_JUDGE:
                judge_submit_result_async(task_id)
            elif self.task.typ == Task.TYPE_JUDGE_VERIFY:
                publish_judge_result_async(task_id)
            return Response({'task_id': task_id, 'status': self.task.status})
        return Response({'msg': 'not all selected'}, status=status.HTTP_400_BAD_REQUEST)

class DiffSegResultAllSelected(APIView):
    permission_classes = (IsTaskPickedByCurrentUser, )
    
    def get(self, request, task_id, format=None):
        objs = list(DiffSegResult.objects.filter(task_id=task_id, selected=0)[0:1])
        all_selected = (len(objs) == 0)
        response = {
            'task_id': task_id,
            'all_selected': all_selected,
            }
        return Response(response)

class MergeList(APIView):
    permission_classes = (IsTaskPickedByCurrentUser, )
    
    def get(self, request, task_id, diffsegresult_id, format=None):
        diffsegresults = list(reversed(DiffSegResult.objects.filter(task_id=task_id, id__lte=diffsegresult_id).order_by('-id')[0:3]))
        diffsegresults_next = list(DiffSegResult.objects.filter(task_id=task_id, id__gt=diffsegresult_id).order_by('id')[0:2])
        diffsegresults.extend(diffsegresults_next)
        serializer = DiffSegResultSerializer(diffsegresults, many=True)
        return Response(serializer.data)

class DiffSegDetail(APIView):
    def get(self, request, task_id, pk, format=None):
        instance = DiffSeg.objects.get(pk=pk)
        serializer = DiffSegSerializer(instance)
        return Response(serializer.data)