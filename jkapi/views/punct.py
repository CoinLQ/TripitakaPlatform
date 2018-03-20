from django.contrib.auth.decorators import login_required
from django.utils import timezone

from rest_framework import mixins, viewsets, generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from tdata.models import *
from tasks.models import *
from tasks.common import SEPARATORS_PATTERN
from tasks.task_controller import punct_submit_result_async, publish_punct_result_async,\
lqpunct_submit_result_async, publish_lqpunct_result_async
from jkapi.serializers import *
from jkapi.permissions import *

import json
from operator import itemgetter

def clean_linefeed(puncts):
    puncts_len = len(puncts)
    for i in range(puncts_len):
        puncts[i] = list(filter(lambda x: x[1] != '\n', puncts[i]))

def merge_text_punct(text, puncts, punct_result):
    TYPE_TEXT = 1
    TYPE_SEP = 2
    result_idx = 0
    result_len = len(punct_result)
    punctseg_lst = []
    indexs = []
    for i in range(len(puncts)):
        indexs.append(0)

    text_idx = 0
    text_len = len(text)
    while True:
        min_pos = text_len
        min_punct_index = -1
        for i in range(len(puncts)):
            index = indexs[i]
            if index < len(puncts[i]):
                punct_obj = puncts[i][index]
                if punct_obj[0] < min_pos:
                    min_pos = punct_obj[0]
                    min_punct_index = i
        if text_idx < min_pos:
            text_seg = text[text_idx:min_pos]
            user_puncts = []
            strs = []
            t_idx = 0
            while result_idx < result_len:
                cur_punct = punct_result[result_idx]
                if (cur_punct[0] < min_pos or (cur_punct[0] == min_pos and cur_punct[1] != '\n')):
                    pass
                else:
                    break
                if cur_punct[0] - text_idx > t_idx:
                    end_idx = cur_punct[0] - text_idx
                    s = text_seg[t_idx : end_idx]
                    strs.append(s)
                    t_idx = cur_punct[0] - text_idx
                strs.append(cur_punct[1])
                user_puncts.append(cur_punct)
                result_idx += 1
            if t_idx < len(text_seg):
                s = text_seg[t_idx:]
                strs.append(s)
            text_seg = ''.join(strs)
            punctseg = {
                'type': TYPE_TEXT,
                'position': text_idx,
                'text': text_seg,
                'cls': '',
                'user_puncts': user_puncts,
            }
            punctseg_lst.append(punctseg)
            text_idx = min_pos
        if min_punct_index != -1:
            index = indexs[min_punct_index]
            css_class = 'punct%d' % (min_punct_index + 1)
            punct_obj = puncts[min_punct_index][index]
            punct_ch = punct_obj[1]
            punctseg = {
                'type': TYPE_SEP,
                'position': text_idx,
                'text': punct_ch,
                'cls': css_class,
                'user_puncts': [],
            }
            punctseg_lst.append(punctseg)
            indexs[min_punct_index] += 1
        else:
            if text_idx == text_len:
                break
    return punctseg_lst

class PunctTaskDetail(APIView):
    permission_classes = (IsTaskPickedByCurrentUser, )
    
    def get(self, request, task_id, format=None):
        if self.task.typ == Task.TYPE_PUNCT:
            reeltext = self.task.reeltext
            text = SEPARATORS_PATTERN.sub('', reeltext.text)
            puncts = []
            for punct in Punct.objects.filter(reeltext=self.task.reeltext)[0:1]:
                punctuation = json.loads(punct.punctuation)
                puncts.append(punctuation)
        elif self.task.typ == Task.TYPE_PUNCT_VERIFY:
            if self.task.status == Task.STATUS_NOT_READY:
                return Response({'msg': 'not ready'})
            reeltext = self.task.reeltext
            text = SEPARATORS_PATTERN.sub('', reeltext.text)
            punct_tasks = list(Task.objects.filter(batchtask=self.task.batchtask,
            typ=Task.TYPE_PUNCT, reel=self.task.reel))
            puncts = [json.loads(t.result) for t in punct_tasks]
        elif self.task.typ == Task.TYPE_LQPUNCT:
            lqreeltext = self.task.lqtext
            text = SEPARATORS_PATTERN.sub('', lqreeltext.text)
            puncts = []
            for punct in LQPunct.objects.filter(lqreeltext=self.task.lqtext)[0:1]:
                punctuation = json.loads(punct.punctuation)
                puncts.append(punctuation)
        elif self.task.typ == Task.TYPE_LQPUNCT_VERIFY:
            if self.task.status == Task.STATUS_NOT_READY:
                return Response({'msg': 'not ready'})
            lqreeltext = self.task.lqtext
            text = SEPARATORS_PATTERN.sub('', lqreeltext.text)
            punct_tasks = list(Task.objects.filter(batchtask=self.task.batchtask,
            typ=Task.TYPE_LQPUNCT, reel=self.task.lqreel))
            puncts = [json.loads(t.result) for t in punct_tasks]
        clean_linefeed(puncts)
        punct_result = json.loads(self.task.result)
        punctseg_lst = merge_text_punct(text, puncts, punct_result)
        response = {
            'task_id': task_id,
            'status': self.task.status,
            'punct_result': punct_result,
            'punctseg_lst': punctseg_lst,
            }
        return Response(response)

    def post(self, request, task_id, format=None):
        if self.task.status >= Task.STATUS_FINISHED:
            return Response({'task_id': task_id, 'status': self.task.status})
        update_fields = []
        if 'punct_result' in request.data:
            punct_json = json.dumps(request.data['punct_result'],separators=(',', ':'))
            self.task.result = punct_json
            update_fields.append('result')
        if 'finished' in request.data:
            self.task.status = Task.STATUS_FINISHED
            self.task.finished_at = timezone.now()
            update_fields.append('status')
            update_fields.append('finished_at')
        if update_fields:
            self.task.save(update_fields=update_fields)
        if self.task.status == Task.STATUS_FINISHED:
            if self.task.typ == Task.TYPE_PUNCT:
                punct_submit_result_async(task_id)
            elif self.task.typ == Task.TYPE_PUNCT_VERIFY:
                publish_punct_result_async(task_id)
            elif self.task.typ == Task.TYPE_LQPUNCT:
                lqpunct_submit_result_async(task_id)
            elif self.task.typ == Task.TYPE_LQPUNCT_VERIFY:
                publish_lqpunct_result_async(task_id)
        response = {
            'task_id': task_id,
            'status': self.task.status,
            }
        return Response(response)