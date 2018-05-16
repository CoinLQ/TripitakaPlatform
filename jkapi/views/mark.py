from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse, Http404
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
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
from tasks.task_controller import *
import json, re




class MarkTaskDetail(APIView):
    permission_classes = (IsTaskPickedByCurrentUser, )
    
    def get(self, request, task_id, format=None):
        base_text = re.compile('[pb\n]').sub("\n", self.task.mark.reeltext.text)
        p_pos = self.task.mark.reeltext.text.split('p')
        lf_postions = []
        for _n in p_pos:
            ahead = 0
            if lf_postions:
                ahead = lf_postions[len(lf_postions)-1]
            lf_postions.append(ahead + len(_n)) 
        marks = self.task.mark.markunit_set.all()
        serializer = MarkUnitSerializer(marks, many=True)
        response = {
            'task_id': task_id,
            'status': self.task.status,
            'base_text': base_text,
            'lf_postions': lf_postions,
            'marks': serializer.data
            }
        return Response(response)



class FinishMarkTask(APIView):
    permission_classes = (IsTaskPickedByCurrentUser, )

    def post(self, request, task_id, format=None):
        # 审定任务已开始，提交将失效
        task = self.task
        mark_verify_task = Task.objects.filter(reel=task.reel, batchtask=task.batchtask, typ=Task.TYPE_MARK_VERIFY).first()
        if mark_verify_task and mark_verify_task.id != task_id and mark_verify_task.status > Task.STATUS_READY +1:
            return Response({'task_id': task_id, 'msg': '审定工作已开始！禁止提交。'}, status=status.HTTP_423_LOCKED)
    
        task.mark.markunit_set.all().delete()
        marks = request.data['marks']
        new_marks = []
        for mark in marks:
            new_marks.append(MarkUnit(mark=task.mark, typ=mark['typ'], mark_typ=mark['mark_typ'], start=mark['start'], end=mark['end']))
        MarkUnit.objects.bulk_create(new_marks)

        task.finished_at = timezone.now()
        task.status = Task.STATUS_FINISHED
        task.save(update_fields=['status', 'finished_at'])

        if task.typ == Task.TYPE_MARK:
            task = Task.objects.get(pk=task_id)
            mark_submit(task)
            #mark_submit_async(task_id)

        return Response({'task_id': task_id, 'status': task.status})
       
