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
from tasks.task_controller import punct_submit_result
from jkapi.serializers import *
from jkapi.permissions import *

import json

class PunctTaskDetail(APIView):
    permission_classes = (IsTaskPickedByCurrentUser, )
    
    def get(self, request, task_id, format=None):
        reeltext = self.task.reeltext
        text = SEPARATORS_PATTERN.sub('', reeltext.text)
        puncts = Punct.objects.filter(task=self.task).first()
        punct = json.loads(puncts.punctuation)
        response = {
            'task_id': task_id,
            'status': self.task.status,
            'reeltext': text,
            'punct': punct,
            'punct_result': json.loads(self.task.result),
            }
        return Response(response)

    def post(self, request, task_id, format=None):
        if 'punct_result' in request.data:
            punct_json = json.dumps(request.data['punct_result'],separators=(',', ':'))
            self.task.result = punct_json
            self.task.save(update_fields=['result'])
            Punct.objects.filter(task=self.task).update(punctuation=punct_json)
        if 'finished' in request.data:
            self.task.status = Task.STATUS_FINISHED
            self.task.save(update_fields=['result'])
            punct_submit_result(self.task)            
        response = {
            'task_id': task_id,
            'status': self.task.status,
            }
        return Response(response)