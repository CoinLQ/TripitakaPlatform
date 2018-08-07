# -*- coding: UTF-8 -*-
from django.conf.urls import url, include
from django.urls import include, path
from rest_framework import routers

from tdata.views import PageViewSet
from ccapi.views.rects import PageRectViewSet, RectViewSet, \
                        ScheduleViewSet
from ccapi.views.tasks import PageTaskViewSet, PageVerifyTaskViewSet
from pretask.views.prepage import PrePageColTaskViewSet, PrePageColVerifyTaskViewSet
from jkapi.views.correct import CorrectTaskDetail, \
CorrectSegList, CorrectSegUpdate, \
FinishCorrectTask, ReturnCorrectTask, DoubtSegViewSet
from jkapi.views.judge import DiffSegResultList, DiffSegResultDetail, get_judge_result_marked, \
JudgeTaskDetail, FinishJudgeTask, MergeList, DiffSegResultAllSelected, DiffSegDetail
from jkapi.views.punct import PunctTaskDetail
from jkapi.views.mark import MarkTaskDetail, FinishMarkTask
from jkapi.views.lqtripitaka import LQSutraViewSet, LQReelTextDetail
from jkapi.views.tripitaka import SutraViewSet, SutraText,TripitakaViewSet, RedoPageRect, TripitakaImageList
from jkapi.views.punct_feedback import LQPunctFeedbackList, MyLQPunctFeedbackList, LQPunctFeedbackDetail, LQPunctFeedbackTask
from jkapi.views.volumn import VolumeViewSet
from jkapi.views.judge_feedback import JudgeFeedbackList, MyJudgeFeedbackList, JudgeFeedbackDetail, JudgeFeedbackTask
from jkapi.views.tripitaka import CorrectFeedbackViewset, CorrectFeedbackDetailViewset, TripitakaPageData, TripitakaReelData, TripitakaVolumePage, TripitakaVolumeList, MyCorrectFeedbackList
from jkapi.views import s3manage
from testing.views import TestViewSet

router = routers.DefaultRouter()
router.register(r'pagerect', PageRectViewSet)
router.register(r'rect', RectViewSet)
router.register(r'schedule', ScheduleViewSet)
router.register(r'test', TestViewSet)

router.register(r'pagetask', PageTaskViewSet)
router.register(r'pageverifytask', PageVerifyTaskViewSet)
router.register(r'prepagecoltask', PrePageColTaskViewSet)
router.register(r'prepagecolverifytask', PrePageColVerifyTaskViewSet)
router.register(r'page', PageViewSet)

router.register(r'lqsutra', LQSutraViewSet)

router.register(r'sutra', SutraViewSet) 
router.register(r'tripitaka', TripitakaViewSet) 
router.register(r'tripitaka_page', TripitakaPageData)
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
    url(r'^judgefeedback/mine/$', MyJudgeFeedbackList.as_view()),
    url(r'^sutra_text/(?P<s_id>[0-9]+)/$', SutraText.as_view()),
    url(r'^tripitaka_volume/(?P<t_code>[\w]+)/$', TripitakaVolumeList.as_view()),
    url(r'^tripitaka_reel/(?P<rid>[0-9]+)/$', TripitakaReelData.as_view()),
    url(r'^tripitaka_volume_page/(?P<key>[\w]+)/$', TripitakaVolumePage.as_view()),
    url(r'^redo_pagerect/(?P<s_id>[0-9]+)/$', RedoPageRect.as_view()),
    url(r'^lqpunctfeedback/$', LQPunctFeedbackList.as_view()),
    url(r'^lqpunctfeedback/(?P<pk>[0-9]+)/$', LQPunctFeedbackDetail.as_view()),
    url(r'^lqpunctfeedback/(?P<pk>[0-9]+)/process/$', LQPunctFeedbackTask.as_view()),
    url(r'^lqpunctfeedback/mine/$', MyLQPunctFeedbackList.as_view()),
    url(r'^correctfeedback/mine/$', MyCorrectFeedbackList.as_view()),
    url(r'^correctfeedback/$', CorrectFeedbackViewset.as_view()),
    url(r'^correctfeedback/(?P<pk>[0-9]+)/$', CorrectFeedbackDetailViewset.as_view()),
    url(r'^s3manage/buckets/$', s3manage.BucketViewset.as_view()),
    url(r'^s3manage/buckets/(?P<name>[\w-]+)/$', s3manage.BucketDetail.as_view()),
    url(r'^s3manage/searchcode/(?P<code>[\w-]+)/$', s3manage.SourceSearch.as_view()),
    url(r'^s3manage/delsource/$', s3manage.DelSource.as_view()),
    url(r'^s3manage/replacesource/$', s3manage.RepSource.as_view()),
    url(r'^coverlist/$', TripitakaImageList.as_view()),
]
