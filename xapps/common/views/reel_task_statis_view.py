from xadmin.sites import site
from xadmin.views.base import CommAdminView
from django.template.response import TemplateResponse
from rect.models import Reel_Task_Statistical, PageTask, TaskStatus
from django.http import HttpResponseRedirect
from django.utils.timezone import localtime, now

from django.shortcuts import get_object_or_404, render, redirect
from tdata.models import *
from tasks.models import *

class ReelPPTaskView(CommAdminView):

    def get(self, request, *args, **kwargs):
        reel_id = request.GET['reel_id']
        schedule_no = request.GET['schedule_no']
        task_header = "%s_%s" % (schedule_no, reel_id)
        Reel_Task_Statistical.objects.get(pk=request.GET['pk']).save()
        PageTask.objects.filter(number__regex=r'^' + task_header + r'.*',
                     status=TaskStatus.NOT_READY).update(status=TaskStatus.NOT_GOT, update_date=localtime(now()).date())

        return HttpResponseRedirect('/xadmin/rect/reel_task_statistical/')

class QiefenPreviewView(CommAdminView):
    def get(self, request, *args, **kwargs):
        
        # 这里的参数和页面，根据API再做调整
        # context={'task': task}
        # return TemplateResponse(self.request, [
        #     'viewrects/tripitaka.html'
        #     ], context)
        task_id = 1;
        task = get_object_or_404(Task, pk=task_id)
        # if task.typ not in [Task.TYPE_CORRECT, Task.TYPE_CORRECT_VERIFY, Task.TYPE_CORRECT_DIFFICULT]:
        #     return redirect('/')
        context={'task': task}
        return TemplateResponse(self.request, [
            'viewrects/tripitaka.html'
            ],context)

site.register_view(r'^rect/reel_pptask/open/$',ReelPPTaskView, name='reel_pp_task')

site.register_view(r'^rect/tripitaka/$',QiefenPreviewView, name='reel_rect_tripitaka')
