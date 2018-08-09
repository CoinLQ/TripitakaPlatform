from django.conf.urls import url
from dmXadmin.data_api import *
from dmXadmin.lqdata_api import *
urlpatterns = [
    url(r'^import_tripitaka_from_excel$', ImportTripiFromExcel.as_view()),
    url(r'^import_lqsutra_from_excel$', ImportLQSutraFromExcel.as_view()),
    url(r'^import_volume_from_excel$', ImportVolFromExcel.as_view()),
]
