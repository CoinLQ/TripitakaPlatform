
from rest_framework import viewsets, generics, filters
from rest_framework import pagination
from rest_framework.views import APIView
from rest_framework.response import Response
from tdata.models import Sutra,ReelOCRText,Reel
from tasks.models import ReelCorrectText,Punct,Page
from tdata.serializer import SutraSerializer 
from tdata.lib.image_name_encipher import get_image_url
from tasks.common import clean_separators, extract_line_separators


import json, re

class SutraResultsSetPagination(pagination.PageNumberPagination):
    page_size = 3

class SutraViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Sutra.objects.all()
    serializer_class = SutraSerializer
    pagination_class = SutraResultsSetPagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name', )


#TODO 下面的函数需要优化返回值  page 
class SutraText(APIView):
    # test http://api.lqdzj.cn/api/sutra_text/231/
    def get(self, request, s_id, format=None):
         
        print('=======================')
        #根据卷ID 获得页号 和页数
        reel = Reel.objects.get(id = s_id)
        reelPages = Page.objects.filter(reel = reel ).order_by("reel_page_no")          
        strURLRet=''
        cut_Info_list=[]
        for p in reelPages:   
            print (p)         
            image_url = get_image_url(reel, p.reel_page_no)
            cut_Info_list.append(p.cut_info)
            strURLRet += image_url+'|'
        print('=======================')    

        #根据卷ID获得经文
        reel_ocr_text=None         
        try:
            reel_ocr_text = ReelCorrectText.objects.get(reel_id = s_id).text
        except:
            reel_ocr_text = ReelOCRText.objects.get(reel_id = s_id).text
        #reel_ocr_text=clean_separators(reel_ocr_text)
        
        # punctuation=None
        # try :
        #     punct=Punct.objects.get(reel_id = s_id)
        #     punctuation = json.loads(punct.body_punctuation)
        # except:            
        #     punctuation='no data'

        #page
         
       

        response = {
            'sutra': reel_ocr_text,
            'pageurls':strURLRet,
            'cut_Info_list':cut_Info_list
            #'punct_lst': punctuation,            
        }
        return Response(response)    