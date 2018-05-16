# -*- coding: UTF-8 -*-
from django.conf.urls import url, include
from django.urls import include, path
from rest_framework import routers

from tdata.views import PageViewSet
from ccapi.views.rects import PageRectViewSet, RectViewSet, \
                        ScheduleViewSet
from ccapi.views.tasks import CCTaskViewSet, ClassifyTaskViewSet, \
                         PageTaskViewSet, DelTaskViewSet
from jkapi.views.correct import CorrectTaskDetail, \
CorrectSegList, CorrectSegUpdate, \
FinishCorrectTask, ReturnCorrectTask, DoubtSegViewSet
from jkapi.views.judge import DiffSegResultList, DiffSegResultDetail, get_judge_result_marked, \
JudgeTaskDetail, FinishJudgeTask, MergeList, DiffSegResultAllSelected, DiffSegDetail
from jkapi.views.punct import PunctTaskDetail
from jkapi.views.mark import MarkTaskDetail, FinishMarkTask
from jkapi.views.lqtripitaka import LQSutraViewSet, LQReelTextDetail
from jkapi.views.tripitaka import SutraViewSet,SutraText,TripitakaViewSet
from jkapi.views.punct_feedback import LQPunctFeedbackList, LQPunctFeedbackDetail, LQPunctFeedbackTask
from jkapi.views.volumn import VolumeViewSet
from jkapi.views.judge_feedback import JudgeFeedbackList, JudgeFeedbackDetail, JudgeFeedbackTask

router = routers.DefaultRouter()
router.register(r'pagerect', PageRectViewSet)
router.register(r'rect', RectViewSet)
router.register(r'schedule', ScheduleViewSet)

router.register(r'cctask', CCTaskViewSet)
router.register(r'classifytask', ClassifyTaskViewSet)
router.register(r'pagetask', PageTaskViewSet)
router.register(r'deltask', DelTaskViewSet)

router.register(r'page', PageViewSet)

router.register(r'lqsutra', LQSutraViewSet)

router.register(r'sutra', SutraViewSet) 
router.register(r'tripitaka', TripitakaViewSet) 
router.register(r'volume', VolumeViewSet) 

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^doubt_seg/(?P<task_id>[0-9]+)/list/$', DoubtSegViewSet.as_view({'get': 'list'})),
    url(r'^doubt_seg/(?P<task_id>[0-9]+)/$', DoubtSegViewSet.as_view({'post': 'create'})),
    url(r'^doubt_seg/(?P<task_id>[0-9]+)/(?P<pk>[0-9]+)/$', DoubtSegViewSet.as_view({'put': 'update'})),
    url(r'^doubt_seg/(?P<task_id>[0-9]+)/(?P<pk>[0-9]+)/delete/$', DoubtSegViewSet.as_view({'delete': 'destroy'})),
    url(r'^correct/(?P<task_id>[0-9]+)/$', CorrectTaskDetail.as_view()),
    url(r'^correct/(?P<task_id>[0-9]+)/correctsegs/$', CorrectSegList.as_view()),
    url(r'^correct/(?P<task_id>[0-9]+)/correctsegs/(?P<pk>[0-9]+)/$', CorrectSegUpdate.as_view()),
    url(r'^correct/(?P<task_id>[0-9]+)/finish/$', FinishCorrectTask.as_view()),
    url(r'^correct/(?P<task_id>[0-9]+)/return/$', ReturnCorrectTask.as_view()),
    url(r'^judge/(?P<task_id>[0-9]+)/$', JudgeTaskDetail.as_view()),
    url(r'^judge/(?P<task_id>[0-9]+)/finish/$', FinishJudgeTask.as_view()),
    url(r'^judge/(?P<task_id>[0-9]+)/allselected/$', DiffSegResultAllSelected.as_view()),
    url(r'^judge/(?P<task_id>[0-9]+)/diffsegresults/$', DiffSegResultList.as_view()),
    url(r'^get_judge/(?P<task_id>[0-9]+)/diffsegresults/$', get_judge_result_marked, name='get_judge_result_marked'),
    url(r'^judge/(?P<task_id>[0-9]+)/diffsegresults/(?P<pk>[0-9]+)/$', DiffSegResultDetail.as_view()),
    url(r'^judge/(?P<task_id>[0-9]+)/diffsegresults/(?P<diffsegresult_id>[0-9]+)/mergelist/$', MergeList.as_view()),
    url(r'^judge/(?P<task_id>[0-9]+)/diffsegs/(?P<pk>[0-9]+)/$', DiffSegDetail.as_view()),
    url(r'^punct/(?P<task_id>[0-9]+)/$', PunctTaskDetail.as_view()),
    url(r'^mark/(?P<task_id>[0-9]+)/$', MarkTaskDetail.as_view()),
    url(r'^mark/(?P<task_id>[0-9]+)/finish/$', FinishMarkTask.as_view()),
    url(r'^lqreeltext/$', LQReelTextDetail.as_view()),
    url(r'^judgefeedback/$', JudgeFeedbackList.as_view()),
    url(r'^judgefeedback/(?P<pk>[0-9]+)/$', JudgeFeedbackDetail.as_view()),
    url(r'^judgefeedback/(?P<pk>[0-9]+)/process/$', JudgeFeedbackTask.as_view()),
    url(r'^sutra_text/(?P<s_id>[0-9]+)/$', SutraText.as_view()),
    url(r'^lqpunctfeedback/$', LQPunctFeedbackList.as_view()),
    url(r'^lqpunctfeedback/(?P<pk>[0-9]+)/$', LQPunctFeedbackDetail.as_view()),
    url(r'^lqpunctfeedback/(?P<pk>[0-9]+)/process/$', LQPunctFeedbackTask.as_view()),
]
