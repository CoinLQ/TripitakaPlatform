
from django.urls import include, path
from django.conf.urls import url
from rest_framework import routers

from .views.judge import DiffSegResultList, DiffSegResultUpdate, JudgeTaskDetail, FinishJudgeTask, MergeList, DiffSegResultAllSelected

#router = routers.DefaultRouter()

urlpatterns = [
    #url(r'^', include(router.urls)),
    url(r'^judge/(?P<task_id>[0-9]+)/$', JudgeTaskDetail.as_view()),
    url(r'^judge/(?P<task_id>[0-9]+)/finish/$', FinishJudgeTask.as_view()),
    url(r'^judge/(?P<task_id>[0-9]+)/allselected/$', DiffSegResultAllSelected.as_view()),
    url(r'^judge/(?P<task_id>[0-9]+)/diffsegresults/$', DiffSegResultList.as_view()),
    url(r'^judge/(?P<task_id>.+)/diffsegresults/(?P<pk>.+)/$', DiffSegResultUpdate.as_view()),
    url(r'^judge/(?P<task_id>.+)/diffsegresults/(?P<diffsegresult_id>.+)/mergelist/$', MergeList.as_view()),
]