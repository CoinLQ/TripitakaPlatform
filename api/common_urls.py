from django.conf.urls import url
from .views.common import CommonListAPIView, CommonHistoryAPIView

app_name = 'common_api'

urlpatterns = [
    url(r'(?P<app_name>\w+)/(?P<model_name>\w+)/(?P<pk>\d+)/obtain',
        CommonListAPIView.as_view(),
        name='common_obtain_api'),
    url(r'(?P<app_name>\w+)/(?P<model_name>\w+)/history',
        CommonHistoryAPIView.as_view(),
        name='common_history_api'),

    url(r'(?P<app_name>\w+)/(?P<model_name>\w+)/(?P<pk>\d+)/detail', CommonHistoryAPIView.as_view(),
        name='common_detail_api'),
    url(r'(?P<app_name>\w+)/(?P<model_name>\w+)',
        CommonListAPIView.as_view(),
        name='common_list_api'),
]
