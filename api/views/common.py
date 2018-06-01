# coding=utf-8
import sys
from rest_framework import filters
import django_filters
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework import viewsets
from ccapi.pagination import CommonPageNumberPagination
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from django.contrib.contenttypes.models import ContentType
from tdata.models import Configuration
from tasks.serializers import TaskSerializer
from tasks.models import Task, FeedbackBase, JudgeFeedback, LQPunctFeedback
from tasks.task_controller import revoke_overdue_task_async, revoke_overdue_pagetask_async
from ccapi.utils.task import redis_lock
from django.utils import timezone
from django.utils.timezone import localtime, now
from rect.models import PageTask, TaskStatus

TASK_MODELS = ('correct', 'verify_correct', 'judge', 'verify_judge', 'punct', 'verify_punct', 'lqpunct',
               'verify_lqpunct', 'correct_difficult', 'judge_difficult', 'mark', 'verify_mark')
RECT_TASK_MODELS = ('pagetask',)

def underscore_to_camelcase(word, lower_first=False):
    result = ''.join(char.capitalize() for char in word.split('_'))
    if lower_first:
        return result[0].lower() + result[1:]
    else:
        return result

def get_app_model_name(kwargs):
    app_name = kwargs.get('app_name').lower()
    model_name = kwargs.get('model_name').lower()
    return app_name, model_name


def get_model_content_type(app_name, model_name):
    if (app_name == 'tasks' and (model_name in TASK_MODELS)):
        return ContentType.objects.get(app_label=app_name, model='task')
    return ContentType.objects.get(app_label=app_name, model=model_name)


class CommonListAPIView(ListCreateAPIView, RetrieveUpdateAPIView):
    # pagination_class = CommonPageNumberPagination
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend)
    serializer_class = 'TaskSerializer'

    def query_set(self, model_name):
        model_type = get_model_content_type(self.app_name, self.model_name)
        self.model = model_type.model_class()
        model = self.model
        if (model_name in TASK_MODELS):
            if model_name == 'correct':
                return model.objects.filter(typ=model.TYPE_CORRECT, status=Task.STATUS_READY)
            elif model_name == 'verify_correct':
                return model.objects.filter(typ=model.TYPE_CORRECT_VERIFY, status=Task.STATUS_READY)
            elif model_name == 'mark':
                return model.objects.filter(typ=model.TYPE_MARK, status=Task.STATUS_READY)
            elif model_name == 'verify_mark':
                return model.objects.filter(typ=model.TYPE_MARK_VERIFY, status=Task.STATUS_READY)
            elif model_name == 'judge':
                return model.objects.filter(typ=model.TYPE_JUDGE, status=Task.STATUS_READY)
            elif model_name =='verify_judge':
                return model.objects.filter(typ=model.TYPE_JUDGE_VERIFY, status=Task.STATUS_READY)
            elif model_name == 'punct':
                return model.objects.filter(typ=model.TYPE_PUNCT, status=Task.STATUS_READY)
            elif model_name =='verify_punct':
                return model.objects.filter(typ=model.TYPE_PUNCT_VERIFY, status=Task.STATUS_READY)
            elif model_name == 'lqpunct':
                return model.objects.filter(typ=model.TYPE_LQPUNCT, status=Task.STATUS_READY)
            elif model_name =='verify_lqpunct':
                return model.objects.filter(typ=model.TYPE_LQPUNCT_VERIFY, status=Task.STATUS_READY)
            elif model_name =='correct_difficult':
                return model.objects.filter(typ=model.TYPE_CORRECT_DIFFICULT, status=Task.STATUS_READY)
            elif model_name =='judge_difficult':
                return model.objects.filter(typ=model.TYPE_JUDGE_DIFFICULT, status=Task.STATUS_READY)
        elif model_name == 'judgefeedback':
            return model.objects.filter(response=FeedbackBase.RESPONSE_UNPROCESSED)
        elif model_name == 'lqpunctfeedback':
            return model.objects.filter(status=Task.STATUS_READY)
        elif model_name == 'correctfeedback':
            return model.objects.filter(response=model.RESPONSE_UNPROCESSED, processor=None)
        elif model_name == 'pagetask':
            return PageTask.objects.filter(status__lt=TaskStatus.ABANDON)

    def get_serializer_class(self):
        model_type = get_model_content_type(self.app_name, self.model_name)
        self.model = model_type.model_class()
        serialize_name = self.model.__name__ + 'Serializer'
        if (self.model_name in TASK_MODELS):
            serialize_name = underscore_to_camelcase(self.model_name) + 'TaskSerializer'
        module_str = '%s.serializers' % self.app_name
        serializer_module = sys.modules[module_str]

        return getattr(serializer_module, serialize_name)

    def _search_fields(self):
        model_name = self.model_name
        if (model_name in TASK_MODELS):
            if model_name in ['correct', 'verify_correct', 'punct', 'verify_punct', 'correct_difficult', 'mark', 'verify_mark']:
                return ('reel__sutra__name', 'reel__sutra__tripitaka__name', 'reel__sutra__tripitaka__code', '=reel__reel_no')
            elif model_name in ['judge', 'verify_judge', 'lqpunct', 'verify_lqpunct', 'judge_difficult']:
                return ('lqreel__lqsutra__name', '=lqreel__reel_no')
        else:
            return getattr(self.model.Config, 'search_fields', ())

    def get(self, request, *args, **kwargs):
        self.app_name, self.model_name = get_app_model_name(kwargs)

        if self.model_name in TASK_MODELS:
            self.queryset = self.query_set(self.model_name).order_by('-priority', 'id')
        elif self.model_name == 'pagetask':
            self.queryset = self.query_set(self.model_name).order_by('number')
        else:
            self.queryset = self.query_set(self.model_name).order_by('id')
        self.filter_fields = getattr(self.model.Config, 'filter_fields', ())
        self.search_fields = self._search_fields()
        self.serializer_class = self.get_serializer_class()
        return super(CommonListAPIView, self).get(request, *args, **kwargs)


    def update(self, request, *args, **kwargs):
        self.app_name, self.model_name = get_app_model_name(kwargs)

        self.queryset = self.query_set(self.model_name)
        self.serializer_class = self.get_serializer_class()

        return self.obtain_task(request, kwargs.get('pk'))

    def get_queryset(self):
        q = super(CommonListAPIView, self).get_queryset()
        if hasattr(self.model.Config, 'filter_queryset'):
            q = self.model.Config.filter_queryset(self.request, q)
        return q

    def _exist_task_by_samepicker(self, task, picker):
        if task.typ in [Task.TYPE_JUDGE, Task.TYPE_LQPUNCT]:
            exist_task = Task.objects.filter(batchtask=task.batchtask, lqreel=task.lqreel, typ=task.typ, picker=picker).first()
        elif task.typ in [Task.TYPE_CORRECT, Task.TYPE_MARK, Task.TYPE_PUNCT]:
            exist_task = Task.objects.filter(batchtask=task.batchtask, reel=task.reel , typ=task.typ, picker=picker).first()
        else:
            return False
        return exist_task
        
    def obtain_task(self, request, pk):
        if self.model_name in TASK_MODELS:
            task = Task.objects.get(pk=pk)
            if self._exist_task_by_samepicker(task, request.user):
                if task.typ in [Task.TYPE_CORRECT, Task.TYPE_JUDGE]:
                    msg = "同一用户不能同时领取校一、校二"
                elif task.typ in [Task.TYPE_PUNCT, Task.TYPE_LQPUNCT, Task.TYPE_MARK]:
                    msg = "同一用户不能同时领取标一、标二"
                return Response({"status": -1, "task_id": pk, "msg": msg})
            count = Task.objects.filter(pk=pk, status=Task.STATUS_READY, picker=None)\
            .update(
                picker=request.user,
                picked_at=timezone.now(),
                status=Task.STATUS_PROCESSING)
            if count == 1:
                conf = Configuration.objects.values('task_timeout').first()
                task_timeout = conf['task_timeout']
                revoke_overdue_task_async(pk, schedule=task_timeout)
        elif self.model_name == 'judgefeedback':
            count = JudgeFeedback.objects.filter(pk=pk, processor=None)\
            .update(processor=request.user, processed_at=timezone.now())
        elif self.model_name == 'lqpunctfeedback':
            count = LQPunctFeedback.objects.filter(pk=pk, status=LQPunctFeedback.STATUS_READY, processor=None)\
            .update(processor=request.user, processed_at=timezone.now(), status=LQPunctFeedback.STATUS_PROCESSING)
        elif self.model_name == 'pagetask':
            count = PageTask.objects.filter(pk=pk, owner=None, status__lt=TaskStatus.HANDLING)\
            .update(owner=request.user, obtain_date=localtime(now()).date(), status=TaskStatus.HANDLING)
            if count == 1:
                conf = Configuration.objects.values('task_timeout').first()
                task_timeout = conf['task_timeout']
                revoke_overdue_pagetask_async(pk, schedule=task_timeout)
        if count == 1:
            return Response({"status": 0, "task_id": pk})
        else:
            return Response({"status": -1, "task_id": pk, "msg": "任务已被占用无法领取."})


class CommonHistoryAPIView(ListCreateAPIView, RetrieveUpdateAPIView):
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend)
    serializer_class = 'TaskSerializer'

    def query_set(self, model_name, request):
        model_type = get_model_content_type(self.app_name, self.model_name)
        self.model = model_type.model_class()
        model = self.model
        if (model_name in TASK_MODELS):
            if model_name == 'correct':
                return model.objects.filter(typ=model.TYPE_CORRECT, picker=request.user)
            elif model_name == 'verify_correct':
                return model.objects.filter(typ=model.TYPE_CORRECT_VERIFY, picker=request.user)
            elif model_name == 'mark':
                return model.objects.filter(typ=model.TYPE_MARK, picker=request.user)
            elif model_name == 'verify_mark':
                return model.objects.filter(typ=model.TYPE_MARK_VERIFY, picker=request.user)
            elif model_name == 'judge':
                return model.objects.filter(typ=model.TYPE_JUDGE, picker=request.user)
            elif model_name =='verify_judge':
                return model.objects.filter(typ=model.TYPE_JUDGE_VERIFY, picker=request.user)
            elif model_name == 'punct':
                return model.objects.filter(typ=model.TYPE_PUNCT, picker=request.user)
            elif model_name =='verify_punct':
                return model.objects.filter(typ=model.TYPE_PUNCT_VERIFY, picker=request.user)
            elif model_name == 'lqpunct':
                return model.objects.filter(typ=model.TYPE_LQPUNCT, picker=request.user)
            elif model_name =='verify_lqpunct':
                return model.objects.filter(typ=model.TYPE_LQPUNCT_VERIFY, picker=request.user)
            elif model_name =='correct_difficult':
                return model.objects.filter(typ=model.TYPE_CORRECT_DIFFICULT, picker=request.user)
            elif model_name =='judge_difficult':
                return model.objects.filter(typ=model.TYPE_JUDGE_DIFFICULT, picker=request.user)
        elif self.model_name == 'pagetask':
            return model.objects.filter(owner=request.user)
        else:
            return model.objects.filter(processor=request.user)

    def _search_fields(self):
        model_name = self.model_name
        if (model_name in TASK_MODELS):
            if model_name in ['correct', 'verify_correct', 'punct', 'verify_punct', 'correct_difficult', 'mark', 'verify_mark']:
                return ('reel__sutra__name', 'reel__sutra__tripitaka__name', 'reel__sutra__tripitaka__code', '=reel__reel_no')
            elif model_name in ['judge', 'verify_judge', 'lqpunct', 'verify_lqpunct', 'judge_difficult']:
                return ('lqreel__lqsutra__name', '=lqreel__reel_no')
        else:
            return getattr(self.model.Config, 'search_fields', ())

    def get_serializer_class(self):
        model_type = get_model_content_type(self.app_name, self.model_name)
        self.model = model_type.model_class()
        serialize_name = self.model.__name__ + 'Serializer'
        if (self.model_name in TASK_MODELS):
            serialize_name = underscore_to_camelcase(self.model_name) + 'TaskSerializer'
        #print(serialize_name)
        module_str = '%s.serializers' % self.app_name
        serializer_module = sys.modules[module_str]

        return getattr(serializer_module, serialize_name)

    def get(self, request, *args, **kwargs):
        self.app_name, self.model_name = get_app_model_name(kwargs)

        if self.model_name in TASK_MODELS:
            self.queryset = self.query_set(self.model_name, request).order_by('-priority', 'id')
        elif self.model_name == 'pagetask':
            self.queryset = self.query_set(self.model_name, request).order_by('status', 'number')
        else:
            self.queryset = self.query_set(self.model_name, request).order_by('id')
        self.filter_fields = getattr(self.model.Config, 'filter_fields', ())
        self.search_fields = self._search_fields()
        self.serializer_class = self.get_serializer_class()

        return super(CommonHistoryAPIView, self).get(request, *args, **kwargs)


    def get_queryset(self):
        q = super(CommonHistoryAPIView, self).get_queryset()
        if hasattr(self.model.Config, 'filter_queryset'):
            q = self.model.Config.filter_queryset(self.request, q)
        return q

    def update(self, request, *args, **kwargs):
        # self.app_name, self.model_name = get_app_model_name(kwargs)
        # self.queryset = self.query_set(self.model_name)
        # self.serializer_class = self.get_serializer_class()

        return self.detail_task(request, kwargs.get('pk'))
    
    def detail_task(self, request, pk):
        task = Task.objects.get(pk=pk)
        if task.typ in [1, 2, 5, 6]:
            desc = "%s-%s-第%d卷" % (task.reel.sutra.tripitaka.name, task.reel.sutra.name, task.reel.reel_no)
        else:
            desc = "%s-第%d卷" % (task.lqreel.lqsutra.name, task.lqreel.reel_no)

        return Response({"status": 0, "task_id": pk, "title": desc})
