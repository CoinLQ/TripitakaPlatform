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
        base_text = re.compile('[pb]').sub("\n", self.task.reeltext.text)
        p_pos = self.task.reeltext.text.split('p')
        lf_postions = []
        for _n in p_pos:
            ahead = 0
            if lf_postions:
                ahead = lf_postions[len(lf_postions)-1]
            lf_postions.append(ahead + len(_n))
        image_urls = []
        for vol_page in range(self.task.reel.start_vol_page, self.task.reel.end_vol_page + 1):
            url = get_image_url(self.task.reel, vol_page)
            image_urls.append(url)
        marks = self.task.mark.markunit_set.all()
        serializer = MarkUnitSerializer(marks, many=True)
        response = {
            'task_id': task_id,
            'status': self.task.status,
            'base_text': base_text,
            'lf_postions': lf_postions,
            'marks': serializer.data,
            'image_urls': image_urls,
            }
        return Response(response)



class FinishMarkTask(APIView):
    permission_classes = (IsTaskPickedByCurrentUser, )

    def put(self, request, task_id, format=None):
        # 审定任务已开始，提交将失效
        task = self.task
        mark_verify_task = Task.objects.filter(reel=task.reel, batchtask=task.batchtask, typ=Task.TYPE_MARK_VERIFY).first()
        if mark_verify_task and task.typ != Task.TYPE_MARK_VERIFY and mark_verify_task.status > Task.STATUS_READY +1:
            return Response({'task_id': mark_verify_task.id, 'msg': '审定工作已开始！禁止提交。'}, status=status.HTTP_423_LOCKED)
    
        task.mark.markunit_set.all().delete()
        marks = request.data['marks']
        new_marks = []
        for mark in marks:
            new_marks.append(MarkUnit(mark=task.mark, typ=mark['typ'], mark_typ=mark['mark_typ'], start=mark['start'], end=mark['end']))
        MarkUnit.objects.bulk_create(new_marks)

        return Response({'task_id': task_id, 'status': task.status})

    def post(self, request, task_id, format=None):
        # 审定任务已开始，提交将失效
        task = self.task
        mark_verify_task = Task.objects.filter(reel=task.reel, batchtask=task.batchtask, typ=Task.TYPE_MARK_VERIFY).first()
        if mark_verify_task and task.typ != Task.TYPE_MARK_VERIFY and mark_verify_task.status > Task.STATUS_READY:
            return Response({'task_id': mark_verify_task.id, 'msg': '审定工作已开始！禁止提交。'}, status=status.HTTP_423_LOCKED)

        if task.typ == Task.TYPE_MARK_VERIFY:
            if task.status == Task.STATUS_FINISHED:
                if not request.user.is_admin:
                    return Response({'task_id': task.id, 'msg': '无权限重复提交审定工作！'}, status=status.HTTP_423_LOCKED)
                else:
                    task.mark.publisher = None
                    task.mark.save(update_fields=['publisher'])
        
        marks = request.data['marks']
        if len(list(filter(lambda x: x['typ'] ==2, marks))) > 0:
            return Response({'task_id': mark_verify_task.id, 'msg': '仍有存疑未处理！禁止提交。'}, status=status.HTTP_423_LOCKED)
        
        task.mark.markunit_set.all().delete()

        new_marks = []
        for mark in marks:
            new_marks.append(MarkUnit(mark=task.mark, typ=mark['typ'], mark_typ=mark['mark_typ'], start=mark['start'], end=mark['end']))
        MarkUnit.objects.bulk_create(new_marks)

        task.finished_at = timezone.now()
        task.status = Task.STATUS_FINISHED
        task.save(update_fields=['status', 'finished_at'])

        if task.typ == Task.TYPE_MARK:
            mark_submit_async(task_id)
        else:
            mark_verify_submit_async(task_id)

        return Response({'task_id': task_id, 'status': task.status})
       
