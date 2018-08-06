from django.conf.urls import url
from dmXadmin.data_api import *
urlpatterns = [
    url(r'^import_tripitaka_from_excel$', ImportTripiFromExcel.as_view()),
]
