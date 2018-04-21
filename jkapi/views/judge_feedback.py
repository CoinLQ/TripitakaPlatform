import json
from django.utils import timezone

from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from tasks.models import DiffSegResult, JudgeFeedback, LQReelText, LQPunct
from tasks.common import extract_line_separators

from jkapi.serializers import JudgeFeedbackSerializer, JudgeFeedbackUpdateSerializer, DiffSegResultSerializer
from jkapi.permissions import CanProcessJudgeFeedback

class JudgeFeedbackList(generics.ListAPIView):
    queryset = JudgeFeedback.objects.all()
    serializer_class = JudgeFeedbackSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, )

    def post(self, request, format=None):
        request.data['fb_user'] = request.user.id
        diffsegresult_id = request.data['diffsegresult']
        try:
            diffsegresult = DiffSegResult.objects.get(id=diffsegresult_id)
        except:
            diffsegresult = None
        if diffsegresult:
            request.data['original_text'] = diffsegresult.selected_text
            serializer = JudgeFeedbackSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class JudgeFeedbackDetail(generics.RetrieveUpdateAPIView):
    queryset = JudgeFeedback.objects
    serializer_class = JudgeFeedbackUpdateSerializer
    permission_classes = (CanProcessJudgeFeedback, )

    def put(self, request, *args, **kwargs):
        request.data['processor'] = request.user.id
        request.data['processed_at'] = timezone.now()
        return self.update(request, *args, **kwargs)

class JudgeFeedbackTask(APIView):
    def get(self, request, pk, format=None):
        try:
            judgefeedback = JudgeFeedback.objects.get(id=pk)
        except:
            return Response({'msg': '参数为非法值！'}, status=status.HTTP_400_BAD_REQUEST)
        task = judgefeedback.diffsegresult.task
        lqreeltext = LQReelText.objects.filter(task=task).order_by('-id').first()
        if lqreeltext is None:
            return Response({'msg': '还未做完此卷的校勘判取审定！'}, status=status.HTTP_400_BAD_REQUEST)
        lqpunct = LQPunct.objects.filter(reeltext=lqreeltext).order_by('-id').first()
        if lqpunct:
            punct_lst = json.loads(lqpunct.punctuation)
        else:
            punct_lst = []
        orig_separators = extract_line_separators(task.reeldiff.base_text.body)
        diffsegresult_pos_lst = []
        diffsegresults = list(DiffSegResult.objects.filter(
            task_id=lqreeltext.task.id).order_by('id'))
        base_pos = 0
        pos = 0
        for diffsegresult in diffsegresults:
            diffseg = diffsegresult.diffseg
            no_diff_length = diffseg.base_pos - base_pos
            pos += no_diff_length
            diffsegresult.position = pos
            selected_length = len(diffsegresult.selected_text)
            if diffsegresult == judgefeedback.diffsegresult:
                diffsegresult_pos_lst.append({
                    'diffsegresult_id': diffsegresult.id,
                    'base_pos': pos,
                    'base_length': selected_length,
                })
            base_pos = diffseg.base_pos + diffseg.base_length
            pos += selected_length
        diffsegresult_serializer = DiffSegResultSerializer(judgefeedback.diffsegresult)
        response = {
            'task_id': lqreeltext.task_id,
            'text': lqreeltext.text,
            'punct_lst': punct_lst,
            'diffsegresult_pos_lst': diffsegresult_pos_lst,
            'orig_separators': orig_separators,
            'diffsegresult': diffsegresult_serializer.data,
        }
        return Response(response)