import json
from django.shortcuts import get_list_or_404
from rest_framework import viewsets, generics, filters
from rest_framework import pagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from tdata.models import Sutra,ReelOCRText,Reel,Tripitaka
from tasks.models import ReelCorrectText, Punct, Page, CorrectFeedback
from tdata.serializer import SutraSerializer,TripitakaSerializer, TripitakaPageSerializer,TripitakaPageListSerializer
from tdata.lib.image_name_encipher import get_image_url
from tasks.common import clean_separators, extract_line_separators
from rect.models import *
from jkapi.serializers import CorrectFeedbackSerializer
from jkapi.permissions import CanSubmitFeedbackOrReadOnly
import math

import json, re

class SutraResultsSetPagination(pagination.PageNumberPagination):
    page_size = 30

class SutraViewSet(viewsets.ReadOnlyModelViewSet):
    #http://api.lqdzj.cn/api/sutra/?page=1&search=大方廣佛華嚴經&tcode=YB
    queryset = Sutra.objects.all()
    serializer_class = SutraSerializer
    pagination_class = SutraResultsSetPagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name', )

    def get_queryset(self):
        queryset = Sutra.objects.all()
        tcode = self.request.query_params.get('tcode', None)
        if tcode is not None:
            queryset =queryset.filter(tripitaka__code=tcode)
        return queryset

class TripitakaResultsSetPagination(pagination.PageNumberPagination):
    page_size = 30

class TripitakaViewSet(viewsets.ReadOnlyModelViewSet):
    #http://api.lqdzj.cn/api/tripitaka/
    queryset = Tripitaka.objects.all()
    serializer_class = TripitakaSerializer
    pagination_class = TripitakaResultsSetPagination

    def get_queryset(self):
        queryset = Tripitaka.objects.all()
        tcode = self.request.query_params.get('code', None)
        if tcode is not None:
            queryset =queryset.filter(code=tcode)
        return queryset

#TODO 下面的函数需要优化返回值  page
class SutraText(APIView):
    # test http://api.lqdzj.cn/api/sutra_text/231/
    def get(self, request, s_id, format=None):
        #根据卷ID 获得页号 和页数
        reel = Reel.objects.get(id = s_id)
        reelPages = Page.objects.filter(reel = reel).order_by("reel_page_no")
        strURLRet=''
        cut_Info_list=[]

        for p in reelPages:
            image_url = get_image_url(reel, p.reel_page_no)
            cut_Info_list.append(p.cut_info)
            strURLRet= image_url+'|'
        reel_ocr_text=None
        reelcorrectid=-1
        try:
            reel_ocr_text = ReelCorrectText.objects.get(reel_id=int(s_id))
            reelcorrectid = reel_ocr_text.id
            text = reel_ocr_text.text
        except:
            reel_ocr_text = ReelOCRText.objects.get(reel_id=int(s_id))
            text = reel_ocr_text.text

        response = {
            'sutra': text,
            'pageurls':strURLRet,
            'cut_Info_list':cut_Info_list,
            'sutra_name': str(reel.sutra.name),
            'reelcorrectid': reelcorrectid,
            #'punct_lst': punctuation,
        }
        return Response(response)


class RedoPageRect(APIView):

    # test http://api.lqdzj.cn/api/redo_pagerect/231/
    def post(self, request, s_id, format=None):
        # 审定任务已开始，提交将失效
        reel = Reel.objects.get(id = s_id)
        reelPages = Page.objects.filter(reel = reel).order_by("reel_page_no").all()
        pagerect= PageRect.objects.filter(page_id=reelPages[request.data['page_no']-1].pk).first()
        pagetasks = PageTask.objects.filter(pagerect=pagerect).all()
        for task in pagetasks:
            if task.status < TaskStatus.COMPLETED:
                task.priority = PriorityLevel.HIGH
                task.save(update_fields=['priority'])
                return Response({'status': 'level up'})

        if len(pagetasks) > 0:
            pagetasks[0].roll_new_task()
            return Response({'status': 'ok'})
        else:
            pass
            # Schedule.create_reels_pptasks(reel)

        return Response({'status': 'null'})

class CorrectFeedbackViewset(generics.ListAPIView):
    queryset = CorrectFeedback.objects.all()
    serializer_class = CorrectFeedbackSerializer
    permission_classes = (CanSubmitFeedbackOrReadOnly,)

    def post(self, request, format=None):
        correct_text = request.data['correct_text']
        if correct_text != -1:
            data = dict(request.data)
            serializer = CorrectFeedbackSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response({'errors': "未校对，不能反馈！"})

class CorrectFeedbackDetailViewset(APIView):
    queryset = CorrectFeedback.objects.all()
    serializer_class = CorrectFeedbackSerializer

    def get(self, request, pk, format=None):
        correct_fb = CorrectFeedback.objects.get(id=pk)
        correct_text = correct_fb.correct_text
        text_list = []
        whole_text = correct_text.text
        page_txt_list = whole_text.split('p')
        for p_no, i in enumerate(page_txt_list):
            for line_no, k in enumerate(i.replace('b','').split('\n')):
                for char_no, l in enumerate(k):
                    text_list.append((p_no, 0, line_no, char_no, l))
        original_txt_info = text_list[correct_fb.position]
        p_no = original_txt_info[0]
        b_no = original_txt_info[1]
        line_no = original_txt_info[2]
        char_no = original_txt_info[3]
        reel = correct_text.reel
        page = reel.page_set.all()[p_no-1]
        image_url = get_image_url(reel, page.reel_page_no)
        cut_list = []
        cid = 'c{0}{1}{2:02d}n{3:02d}'.format(p_no, b_no, line_no, char_no+1)#切分信息中字符从1开始计数
        page_cuts = json.loads(page.cut_info)['char_data']
        for c_no, cut in enumerate(page_cuts):
            if cut['char_id'] == cid:
                cut_list = page_cuts[c_no: c_no+len(correct_fb.original_text)]
        page_lines = page_txt_list[p_no].split('\n')
        fb_line = page_lines[line_no]
        page_lines[line_no] = fb_line[:char_no] +'<span class="difftext confirmed">'+fb_line[char_no]+'</span>'+fb_line[char_no+1:]
        if correct_fb.processor:
            processor = correct_fb.processor
        else:
            processor = 0
        return Response({
            'fb_id': correct_fb.id,
            'origin_text': correct_fb.original_text,
            'fb_text': correct_fb.fb_text,
            'fb_comment': correct_fb.fb_comment,
            'cut_info': cut_list,
            'page_txt': page_lines,
            'image_url': image_url,
            'processor': processor.email,
            'response': correct_fb.get_response_display()
        })

    def patch(self, request, pk, format=None):
        correctfb = CorrectFeedback.objects.get(pk=pk)
        data = dict(request.data)
        data['correct_text'] = correctfb.correct_text.id
        data['fb_comment'] = correctfb.fb_comment
        data['processor'] = request.user.id
        data['processed_at'] = timezone.now()
        serializer = CorrectFeedbackSerializer(correctfb, data=data)
        if serializer.is_valid():
            if data['response'] == 2:
                correct_text = correctfb.correct_text
                ori_whole_txt = correct_text.text
                head_txt = ''
                tail_txt = ''
                pos = 0
                for t in ori_whole_txt:
                    if pos < correctfb.position:
                        head_txt += t
                    if t not in ['b','p','\n']:
                        pos += 1
                    if correctfb.position <= pos <= correctfb.position + len(correctfb.original_text) - 1:
                        pass
                    if pos > correctfb.position + len(correctfb.original_text):
                        tail_txt += t
                new_correct_text = ReelCorrectText(reel=correct_text.reel, publisher=request.user)
                new_correct_text.set_text(head_txt+correctfb.fb_text+tail_txt)
                new_correct_text.save()
            serializer.save()
            return Response('提交成功!')
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TripitakaReelData(viewsets.ReadOnlyModelViewSet):
    queryset = Page.objects.all()
    serializer_class = TripitakaPageListSerializer
    pagination_class = SutraResultsSetPagination

    def get_queryset(self):
        reel = Reel.objects.get(id=int(self.request.query_params.get('rid', None)))
        queryset = Page.filter(reel=reel).order_by('page_no')
        return queryset

class TripitakaVolumePage(viewsets.ReadOnlyModelViewSet):
    queryset = Page.objects.all()
    serializer_class = TripitakaPageListSerializer
    pagination_class = SutraResultsSetPagination

    def get_queryset(self):
        queryset = Page.objects.all()
        data = self.request.query_params
        key = data.get('key')
        queryset = queryset.filter(page_code__contains=key).order_by('page_no')
        return queryset

class TripitakaPageData(viewsets.ReadOnlyModelViewSet):
    queryset = Page.objects.all()
    serializer_class = TripitakaPageSerializer
    pagination_class = SutraResultsSetPagination

    def get_queryset(self):
        queryset = Page.objects.all()
        data = self.request.query_params
        pid = data.get('pid')
        queryset = queryset.filter(pid=pid)
        return queryset

def get_path_list(t_code):
    if t_code:
        path_list = Reel.objects.distinct('path1', 'path2', 'path3').exclude(path1='').filter(sutra__tripitaka__code=t_code).values('path1', 'path2', 'path3').all().order_by('path1', 'path2', 'path3', 'reel_no')
    else:
        path_list = Reel.objects.distinct('path1', 'path2', 'path3').exclude(path1='').values('path1', 'path2', 'path3').all().order_by('path1', 'path2', 'path3', 'reel_no')
    return path_list

def str_2_int(n):
    if n.isdigit():
        return int(n)
    else:
        return 0

def list_2_tree(path_list):
    path_list = list(path_list)
    for no, i in enumerate(path_list):
        path_list[no] = list(i.values())
    path_list = sorted(path_list, key=lambda X:[str_2_int(X[0]), str_2_int(X[1]), str_2_int(X[2])])
    return path_list

def gene_children(parent_key, lst):
    tree = {}
    for p in lst:
        p1 = p[0]
        p2 = p[1:]
        if p1 in tree.keys():
            if p2[0] is not '':
                tree[p1]['children'].append(p2)
        else:
            if p2[0] is not '':
                tree[p1] = {'label': p1, 'key': parent_key + '_' + p1, 'children': [p2]}
            else:
                tree[p1] = {'label': p1, 'key': parent_key + '_' + p1, 'children': []}
    tmp_result = list(tree.values())
    for no, p in enumerate(tmp_result):
        if p['children']:
            p_list = p['children']
            tmp_result[no]['children'] = gene_children(p['key'], p_list)
    return tmp_result

class TripitakaVolumeList(APIView):
    def get(self, request, t_code, format=None):
        page_no = int(request.query_params['page'])
        result = gene_children(t_code, list_2_tree(get_path_list(t_code)))
        count = len(result)
        max_page = math.ceil(count/30)
        if page_no > max_page:
            page_no = max_page
        elif page_no < 1:
            page_no = 1
        start = 30*(page_no - 1)
        if page_no*30 > count:
            end = count
        else:
            end = page_no*30
        return Response({
            'result': result[start:end],
            'count': count
        })
