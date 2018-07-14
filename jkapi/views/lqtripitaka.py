import json

from django.http import Http404
from django.utils import timezone

from rest_framework import viewsets, generics, filters
from rest_framework import pagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from tdata.models import LQSutra
from tasks.models import LQReelText, LQPunct, DiffSegResult
from tdata.serializer import LQSutraSerializer
from tasks.common import clean_separators, extract_line_separators

class LQSutraResultsSetPagination(pagination.PageNumberPagination):
    page_size = 30

class LQSutraViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LQSutra.objects.order_by('id')
    serializer_class = LQSutraSerializer
    pagination_class = LQSutraResultsSetPagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name', )

class LQReelTextDetail(APIView):
    def get(self, request, format=None):
        if 'lqreel_id' not in request.GET:
            return Response({'msg': 'no lqreel_id'}, status=status.HTTP_400_BAD_REQUEST)
        lqreel_id = request.GET.get('lqreel_id')
        lqreeltext = LQReelText.objects.filter(lqreel_id=lqreel_id).order_by('-id').first()
        if lqreeltext is None:
            return Response({'msg': '还未做完此卷的校勘判取审定！'})
        lqpunct = LQPunct.objects.filter(reeltext=lqreeltext).order_by('-id').first()
        if lqpunct:
            punct_lst = json.loads(lqpunct.punctuation)
            lqpunct_id = lqpunct.id
        else:
            punct_lst = []
            lqpunct_id = 0
        orig_separators = extract_line_separators(lqreeltext.task.reeldiff.base_text.body)
        diffsegresult_pos_lst = []
        diffsegresults = list(DiffSegResult.objects.filter(
            task_id=lqreeltext.task.id).order_by('diffseg__base_pos'))
        base_pos = 0
        pos = 0
        for diffsegresult in diffsegresults:
            diffseg = diffsegresult.diffseg
            no_diff_length = diffseg.base_pos - base_pos
            pos += no_diff_length
            diffsegresult.position = pos
            selected_length = len(diffsegresult.selected_text)
            diffsegresult_pos_lst.append({
                'diffsegresult_id': diffsegresult.id,
                'base_pos': pos,
                'base_length': selected_length,
            })
            base_pos = diffseg.base_pos + diffseg.base_length
            pos += selected_length
        response = {
            'task_id': lqreeltext.task_id,
            'lqpunct_id': lqpunct_id,
            'text': lqreeltext.text,
            'punct_lst': punct_lst,
            'diffsegresult_pos_lst': diffsegresult_pos_lst,
            'orig_separators': orig_separators,
        }
        return Response(response)
