import json
from django.utils import timezone

from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from tasks.models import DiffSegResult, LQPunctFeedback, LQReelText, LQPunct
from tasks.common import extract_line_separators, clean_separators, compact_json_dumps

from jkapi.views.punct import merge_text_punct
from jkapi.serializers import LQPunctFeedbackSerializer
from jkapi.permissions import CanProcessLQPunctFeedback, CanSubmitFeedbackOrReadOnly

class LQPunctFeedbackList(generics.ListCreateAPIView):
    queryset = LQPunctFeedback.objects.all()
    serializer_class = LQPunctFeedbackSerializer
    permission_classes = (CanSubmitFeedbackOrReadOnly, )

class LQPunctFeedbackDetail(generics.RetrieveUpdateAPIView):
    queryset = LQPunctFeedback.objects
    serializer_class = LQPunctFeedbackSerializer
    permission_classes = (CanProcessLQPunctFeedback, )

class LQPunctFeedbackTask(APIView):
    def get(self, request, pk, format=None):
        try:
            lqpunctfeedback = LQPunctFeedback.objects.get(id=pk)
        except:
            return Response({'msg': '参数为非法值！'}, status=status.HTTP_400_BAD_REQUEST)
        if lqpunctfeedback.status == LQPunctFeedback.STATUS_READY:
            lqpunctfeedback.status = LQPunctFeedback.STATUS_PROCESSING
            lqpunctfeedback.processor = request.user
            lqpunctfeedback.processed_at = timezone.now()
            lqpunctfeedback.save(update_fields=['status', 'processor', 'processed_at'])
        else:
            if lqpunctfeedback.processor != request.user:
                return Response({'msg': '无权限'}, status=status.HTTP_400_BAD_REQUEST)
        lqpunct = lqpunctfeedback.lqpunct
        text = clean_separators(lqpunct.reeltext.text)
        puncts = []
        punctuation = json.loads(lqpunct.punctuation)
        puncts.append(punctuation)
        # 用来分割反馈标点的文本
        position_lst = []
        position_lst.append( [lqpunctfeedback.start, ''] )
        position_lst.append( [lqpunctfeedback.end, ''] )
        puncts.append(position_lst)
        # 构建punct_result
        punct_result = []
        fb_punctuation = json.loads(lqpunctfeedback.fb_punctuation)
        for p in fb_punctuation:
            p[0] += lqpunctfeedback.start
        fb_merged = False
        for p in punctuation:
            pos = p[0]
            if pos > lqpunctfeedback.start and pos <= lqpunctfeedback.end:
                if not fb_merged:
                    punct_result.extend(fb_punctuation)
                    fb_merged = True
            else:
                punct_result.append(p)
        punctseg_lst = merge_text_punct(text, puncts, punct_result)
        for punctseg in punctseg_lst:
            position = punctseg['position']
            if position >= lqpunctfeedback.start and position < lqpunctfeedback.end:
                punctseg['fb_range'] = 0
            elif position >= lqpunctfeedback.end:
                punctseg['fb_range'] = 1
            else:
                punctseg['fb_range'] = -1
        response = {
            'status': lqpunctfeedback.status,
            'punct_result': punct_result,
            'punctseg_lst': punctseg_lst,
        }
        return Response(response)

    def post(self, request, pk, format=None):
        try:
            lqpunctfeedback = LQPunctFeedback.objects.get(id=pk)
        except:
            return Response({'msg': '参数为非法值！'}, status=status.HTTP_400_BAD_REQUEST)
        if lqpunctfeedback.processor != request.user:
            return Response({'msg': '无权限'}, status=status.HTTP_400_BAD_REQUEST)
        if lqpunctfeedback.status != LQPunctFeedback.STATUS_PROCESSING:
            return Response({'status': lqpunctfeedback.status})
        if 'punct_result' not in request.data:
            return Response({'msg': '参数缺少！'}, status=status.HTTP_400_BAD_REQUEST)
        update_fields = []
        punct_json = compact_json_dumps(request.data['punct_result'])
        lqpunctfeedback.punctuation = punct_json
        update_fields.append('punctuation')
        if 'finished' in request.data:
            lqpunctfeedback.status = LQPunctFeedback.STATUS_FINISHED
            update_fields.append('status')
        lqpunctfeedback.save(update_fields=update_fields)
        return Response({'status': lqpunctfeedback.status})

    