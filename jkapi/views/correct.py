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
from tasks.common import judge_merge_text_punct, ReelText, \
extract_page_line_separators, clean_separators

import json, re
from operator import attrgetter, itemgetter

class CorrectDiffSegList(mixins.ListModelMixin, generics.GenericAPIView):
    serializer_class = CorrectDiffSegSerializer
    permission_classes = (IsTaskPickedByCurrentUser, )

    def get_queryset(self):
        queryset = CorrectDiffSeg.objects.filter(
            result_diff=self.task.result_diff).order_by('id')
        return queryset

    def get(self, request, task_id, format=None):
        correctdiffsegs = CorrectDiffSeg.objects.filter(
            result_diff=self.task.result_diff).order_by('id')
        serializer = CorrectDiffSegSerializer(correctdiffsegs, many=True)
        return Response(serializer.data)

class CorrectDiffSegUpdate(mixins.UpdateModelMixin, generics.GenericAPIView):
    serializer_class = CorrectDiffSegSerializer
    permission_classes = (IsTaskPickedByCurrentUser, )

    def get_object(self, pk):
        try:
            return CorrectDiffSeg.objects.get(pk=pk)
        except CorrectDiffSeg.DoesNotExist:
            raise Http404

    def put(self, request, task_id, pk, format=None):
        correctdiffseg = self.get_object(pk)
        serializer = CorrectDiffSegSerializer(correctdiffseg, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CorrectVerifyTaskDetail(APIView):
    permission_classes = (IsTaskPickedByCurrentUser, )
    
    def get(self, request, task_id, format=None):
        response = {
            'task_id': task_id,
            'status': self.task.status,
            'result': self.task.result,
            'start_vol_page': self.task.reel.start_vol_page,
            'image_url_prefix': self.task.reel.url_prefix(),
            }
        return Response(response)

class FinishCorrectVerifyTask(APIView):
    permission_classes = (IsTaskPickedByCurrentUser, )

    def post(self, request, task_id, format=None):
        self.task.result = request.data['result']
        self.task.status = Task.STATUS_FINISHED
        self.task.save(update_fields=['result', 'status'])
        return Response({'task_id': task_id, 'status': self.task.status})
