from django.http import Http404
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
from tasks.task_controller import correct_submit_async, correct_verify_submit_async

import json, re
from operator import attrgetter, itemgetter

class CorrectTaskDetail(APIView):
    permission_classes = (IsTaskPickedByCurrentUser, )
    
    def get(self, request, task_id, format=None):
        response = {
            'task_id': task_id,
            'status': self.task.status,
            'result': self.task.result,
            'cur_focus': self.task.cur_focus,
            'start_vol_page': self.task.reel.start_vol_page,
            'image_url_prefix': self.task.reel.url_prefix(),
            }
        return Response(response)

class CorrectSegList(mixins.ListModelMixin, generics.GenericAPIView):
    serializer_class = CorrectSegSerializer
    permission_classes = (IsTaskPickedByCurrentUser, )

    def get_queryset(self):
        queryset = CorrectSeg.objects.filter(
            task=self.task).order_by('id')
        return queryset

    def get(self, request, task_id, format=None):
        serializer = CorrectSegSerializer(self.get_queryset(), many=True)
        return Response(serializer.data)

class CorrectSegUpdate(mixins.UpdateModelMixin, generics.GenericAPIView):
    serializer_class = CorrectSegSerializer
    permission_classes = (IsTaskPickedByCurrentUser, )

    def get_object(self, pk):
        try:
            return CorrectSeg.objects.get(pk=pk)
        except CorrectSeg.DoesNotExist:
            raise Http404

    def put(self, request, task_id, pk, format=None):
        correctseg = self.get_object(pk)
        serializer = CorrectSegSerializer(correctseg, data=request.data)
        if serializer.is_valid():
            serializer.save()
            self.task.cur_focus = pk
            self.task.save(update_fields=['cur_focus'])
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FinishCorrectTask(APIView):
    permission_classes = (IsTaskPickedByCurrentUser, )

    def post(self, request, task_id, format=None):
        self.task.status = Task.STATUS_FINISHED
        self.task.save(update_fields=['status'])
        # TODO: changed to background job
        if self.task.typ == Task.TYPE_CORRECT:
            correct_submit_async(task_id)
        elif self.task.typ == Task.TYPE_CORRECT_VERIFY:
            correct_verify_submit_async(task_id)
        return Response({'task_id': task_id, 'status': self.task.status})