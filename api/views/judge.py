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

from sutradata.models import *
from tasks.models import *
from api.serializers import *
from api.permissions import *
from sutradata.common import judge_merge_text_punct, ReelText, extract_page_line_separators
from tasks.views.task_controller import judge_submit_result, publish_judge_result

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
            return queryset.filter(all_equal=all_equal).order_by('id')
        if 'diffseg_id' in self.request.GET:
            diffseg_id_lst = self.request.GET.get('diffseg_id').split(',')
            return queryset.filter(diffseg_id__in=diffseg_id_lst).order_by('id')
        return queryset.order_by('id')

class DiffSegResultUpdate(generics.UpdateAPIView):
    serializer_class = DiffSegResultSimpleSerializer
    permission_classes = (IsTaskPickedByCurrentUser, )

    def get_queryset(self):
        return DiffSegResult.objects.filter()

class JudgeTaskDetail(APIView):
    permission_classes = (IsTaskPickedByCurrentUser, )
    
    def get(self, request, task_id, format=None):
        base_text = self.task.reeldiff.base_text
        diffseg_pos_lst = self.task.reeldiff.diffseg_pos_lst
        base_reel = Reel.objects.get(sutra=self.task.reeldiff.base_sutra, reel_no=self.task.reeldiff.reel_no)
        puncts = base_reel.punct_set.all()[0:1]
        punct = puncts[0]
        response = {
            'task_id': task_id,
            'status': self.task.status,
            'base_text': base_text,
            'diffseg_pos_lst': json.loads(diffseg_pos_lst),
            'punct_lst': json.loads(punct.punctuation),
            'base_tripitaka_id': base_reel.sutra.tripitaka_id,
            }
        return Response(response)

class FinishJudgeTask(APIView):
    permission_classes = (IsTaskPickedByCurrentUser, )

    def post(self, request, task_id, format=None):
        objs = list(DiffSegResult.objects.filter(task_id=task_id, selected=0)[0:1])
        all_selected = (len(objs) == 0)
        if all_selected:
            Task.objects.filter(id=task_id).update(status=Task.STATUS_FINISHED)
            # TODO: changed to background job
            if self.task.typ == Task.TYPE_JUDGE:
                judge_submit_result(self.task)
            elif self.task.typ == Task.TYPE_JUDGE_VERIFY:
                publish_judge_result(self.task)
            return Response({'task_id': task_id})
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