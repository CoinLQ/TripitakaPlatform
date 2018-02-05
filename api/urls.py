# -*- coding: UTF-8 -*-
from django.conf.urls import url, include
from django.urls import include, path
from rest_framework import routers

from tdata.views import PageViewSet
from ccapi.views.rects import PageRectViewSet, RectViewSet, \
                        ScheduleViewSet
from ccapi.views.tasks import CCTaskViewSet, ClassifyTaskViewSet, \
                         PageTaskViewSet, DelTaskViewSet
from jkapi.views.judge import DiffSegResultList, DiffSegResultUpdate, JudgeTaskDetail, FinishJudgeTask, MergeList, DiffSegResultAllSelected


router = routers.DefaultRouter()
router.register(r'pagerect', PageRectViewSet)
router.register(r'rect', RectViewSet)
router.register(r'schedule', ScheduleViewSet)

router.register(r'cctask', CCTaskViewSet)
router.register(r'classifytask', ClassifyTaskViewSet)
router.register(r'pagetask', PageTaskViewSet)
router.register(r'deltask', DelTaskViewSet)

router.register(r'page', PageViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^judge/(?P<task_id>[0-9]+)/$', JudgeTaskDetail.as_view()),
    url(r'^judge/(?P<task_id>[0-9]+)/finish/$', FinishJudgeTask.as_view()),
    url(r'^judge/(?P<task_id>[0-9]+)/allselected/$', DiffSegResultAllSelected.as_view()),
    url(r'^judge/(?P<task_id>[0-9]+)/diffsegresults/$', DiffSegResultList.as_view()),
    url(r'^judge/(?P<task_id>[0-9]+)/diffsegresults/(?P<pk>[0-9]+)/$', DiffSegResultUpdate.as_view()),
    url(r'^judge/(?P<task_id>[0-9]+)/diffsegresults/(?P<diffsegresult_id>[0-9]+)/mergelist/$', MergeList.as_view()),
]