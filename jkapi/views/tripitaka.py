from django.shortcuts import get_list_or_404
from rest_framework import viewsets, generics, filters
from rest_framework import pagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from tdata.models import Sutra,ReelOCRText,Reel,Tripitaka
from tasks.models import ReelCorrectText, Punct, Page, CorrectFeedback
from tdata.serializer import SutraSerializer ,TripitakaSerializer
from tdata.lib.image_name_encipher import get_image_url
from tasks.common import clean_separators, extract_line_separators
from rect.models import *
from jkapi.serializers import CorrectFeedbackSerializer
from jkapi.permissions import CanSubmitFeedbackOrReadOnly

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

#TODO 下面的函数需要优化返回值  page 
class SutraText(APIView):
    # test http://api.lqdzj.cn/api/sutra_text/231/
    def get(self, request, s_id, format=None):
        
        print('=======================')
        #根据卷ID 获得页号 和页数
        reel = Reel.objects.get(id = s_id)
        reelPages = Page.objects.filter(reel = reel).order_by("reel_page_no")          
        strURLRet=''
        cut_Info_list=[]
        
        for p in reelPages:   
            print (p)         
            image_url = get_image_url(reel, p.reel_page_no)
            cut_Info_list.append(p.cut_info)
            # cut_Info_list.append(json.dumps({'char_data': [rect.serialize_set for rect in Rect.objects.filter(page_pid=p.pk).order_by('-id')]},separators=(',', ':')))
            strURLRet= image_url+'|'
        print('=======================')    

        #根据卷ID获得经文
        reel_ocr_text=None
        reelcorrectid=-1
        try:
            reel_ocr_text = ReelCorrectText.objects.get(reel_id=int(s_id))
            reelcorrectid = reel_ocr_text.id
            text = reel_ocr_text.text
        except:
            reel_ocr_text = ReelOCRText.objects.get(reel_id=int(s_id))
            text = reel_ocr_text.text
        
        # punctuation=None
        # try :
        #     punct=Punct.objects.get(reel_id = s_id)
        #     punctuation = json.loads(punct.body_punctuation)
        # except:            
        #     punctuation='no data'

        #page
         
       

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
        return Response({'errors': "未校对，不能反馈！"}, status=status.HTTP_400_BAD_REQUEST)
