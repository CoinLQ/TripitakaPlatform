
from rest_framework import viewsets, generics, filters
from rest_framework import pagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from tdata.models import LQSutra
from tasks.models import LQReelText, LQPunct, DiffSegResult
from tdata.serializer import LQSutraSerializer

import json

class LQSutraResultsSetPagination(pagination.PageNumberPagination):
    page_size = 30

class LQSutraViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LQSutra.objects.all()
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
        else:
            punct_lst = []
        diffsegresult_pos_lst = []
        diffsegresults = list(DiffSegResult.objects.filter(task_id=lqreeltext.task.id).order_by('id'))
        base_pos = 0
        pos = 0
        for diffsegresult in diffsegresults:
            diffseg = diffsegresult.diffseg
            no_diff_length = diffseg.base_pos - base_pos
            pos += no_diff_length
            diffsegresult.position = pos
            selected_length = len(diffsegresult.selected_text)
            print(diffsegresult.selected_text, diffsegresult.id, pos, selected_length)
            diffsegresult_pos_lst.append({
                'diffsegresult_id': diffsegresult.id,
                'position': pos,
                'selected_length': selected_length,
            })
            base_pos = diffseg.base_pos + diffseg.base_length
            pos += selected_length
        response = {
            'text': lqreeltext.text,
            'punct_lst': punct_lst,
            'diffsegresult_pos_lst': diffsegresult_pos_lst,
        }
        return Response(response)
