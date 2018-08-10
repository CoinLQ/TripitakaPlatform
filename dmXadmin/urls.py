from django.conf.urls import url
from dmXadmin.data_api import *
urlpatterns = [
    url(r'^import_tripitaka_from_excel$', ImportTripiFromExcel.as_view()),
    url(r'^import_sutra_from_excel$', ImportSutraFromExcel.as_view()),
    url(r'^import_volume_from_excel$', ImportVolFromExcel.as_view()),
]
