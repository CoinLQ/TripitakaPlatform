#from django.shortcuts import get_list_or_404
from rest_framework import viewsets, generics, filters
from rest_framework import pagination
from rest_framework.views import APIView
from rest_framework.response import Response
from tdata.models import Volume
#from tdata.models import Sutra,ReelOCRText,Reel,Tripitaka
#from tasks.models import ReelCorrectText,Punct,Page
from tdata.serializer import VolumeSerializer#SutraSerializer ,TripitakaSerializer
#from tdata.lib.image_name_encipher import get_image_url
#from tasks.common import clean_separators, extract_line_separators

import json, re
class VolumeResultsSetPagination(pagination.PageNumberPagination):
    page_size = 30

class VolumeViewSet(viewsets.ReadOnlyModelViewSet):
    #http://api.lqdzj.cn/api/volumn/?page=1&tcode=YB&vno=2
    queryset = Volume.objects.all()
    serializer_class = VolumeSerializer
    pagination_class = VolumeResultsSetPagination
    filter_backends = (filters.SearchFilter,)
