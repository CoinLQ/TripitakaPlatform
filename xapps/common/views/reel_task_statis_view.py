from xadmin.sites import site
from xadmin.views.base import CommAdminView
from django.template.response import TemplateResponse
from rect.models import Reel_Task_Statistical, PageTask, TaskStatus
from django.http import HttpResponseRedirect
from django.utils.timezone import localtime, now

class ReelPPTaskView(CommAdminView):

    def get(self, request, *args, **kwargs):
        reel_id = request.GET['reel_id']
        schedule_no = request.GET['schedule_no']
        task_header = "%s_%s" % (schedule_no, reel_id)
        Reel_Task_Statistical.objects.get(pk=request.GET['pk']).save()
        PageTask.objects.filter(number__regex=r'^' + task_header + r'.*',
                     status=TaskStatus.NOT_READY).update(status=TaskStatus.NOT_GOT, update_date=localtime(now()).date())

        return HttpResponseRedirect('/xadmin/rect/reel_task_statistical/')

site.register_view(r'^rect/reel_pptask/open/$',ReelPPTaskView, name='reel_pp_task')

