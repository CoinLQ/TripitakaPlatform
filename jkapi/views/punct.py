from django.contrib.auth.decorators import login_required

from rest_framework import mixins, viewsets, generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from tdata.models import *
from tasks.models import *
from tasks.common import SEPARATORS_PATTERN
from tasks.task_controller import punct_submit_result, publish_punct_result
from jkapi.serializers import *
from jkapi.permissions import *

import json

class PunctTaskDetail(APIView):
    permission_classes = (IsTaskPickedByCurrentUser, )
    
    def get(self, request, task_id, format=None):
        if self.task.typ == Task.TYPE_PUNCT:
            reeltext = self.task.reeltext
            text = SEPARATORS_PATTERN.sub('', reeltext.text)
            puncts = []
            for punct in Punct.objects.filter(reel=self.task.reel)[0:1]:
                punctuation = json.loads(punct.punctuation)
                puncts.append(punctuation)
        elif self.task.typ == Task.TYPE_PUNCT_VERIFY:
            if self.task.status == Task.STATUS_NOT_READY:
                return Response({'msg': 'not ready'})
            punct_tasks = list(Task.objects.filter(batch_task=task.batchtask,
            typ=Task.TYPE_PUNCT, reel=task.reel))
            puncts = [json.loads(t.result) for t in punct_tasks]
        elif self.task.typ == Task.TYPE_LQPUNCT:
            lqreeltext = self.task.lqtext
            text = SEPARATORS_PATTERN.sub('', lqreeltext.text)
            puncts = []
            for punct in LQPunct.objects.filter(lqreel=self.task.lqreel)[0:1]:
                punctuation = json.loads(punct.punctuation)
                puncts.append(punctuation)
        elif self.task.typ == Task.TYPE_LQPUNCT_VERIFY:
            if self.task.status == Task.STATUS_NOT_READY:
                return Response({'msg': 'not ready'})
            punct_tasks = list(Task.objects.filter(batch_task=task.batchtask,
            typ=Task.TYPE_LQPUNCT, reel=task.lqreel))
            puncts = [json.loads(t.result) for t in punct_tasks]
        response = {
            'task_id': task_id,
            'status': self.task.status,
            'reeltext': text,
            'puncts': puncts,
            'punct_result': json.loads(self.task.result),
            }
        return Response(response)

    def post(self, request, task_id, format=None):
        update_fields = []
        if 'punct_result' in request.data:
            punct_json = json.dumps(request.data['punct_result'],separators=(',', ':'))
            self.task.result = punct_json
            update_fields.append('result')
        if 'finished' in request.data:
            self.task.status = Task.STATUS_FINISHED
            update_fields.append('status')
        if update_fields:
            self.task.save(update_fields=update_fields)
        if self.task.status == Task.STATUS_FINISHED:
            if self.task.typ == Task.TYPE_PUNCT:
                punct_submit_result(self.task)
            elif self.task.typ == Task.TYPE_PUNCT_VERIFY:
                publish_punct_result(self.task)
            elif self.task.typ == Task.TYPE_LQPUNCT:
                lqpunct_submit_result(self.task)
            elif self.task.typ == Task.TYPE_LQPUNCT_VERIFY:
                publish_lqpunct_result(self.task)
        response = {
            'task_id': task_id,
            'status': self.task.status,
            }
        return Response(response)