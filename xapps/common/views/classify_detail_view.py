from xadmin.sites import site
from xadmin.views.base import CommAdminView,csrf_protect_m
from django.template.response import TemplateResponse
from rect.models import Schedule, CharClassifyPlan


class CCDetailView(CommAdminView):

    @csrf_protect_m
    def get(self, request, *args, **kwargs):
        pid = request.GET['pk']
        # 这里的参数和页面，根据API再做调整
        context={'schedule_id': pid}
        return TemplateResponse(self.request, [
            'viewrects/cc_details.html'
            ], context)


class ClassifyDetailView(CommAdminView):
    @csrf_protect_m
    def get(self, request, *args, **kwargs):
        pid = request.GET['pk']
        cp = CharClassifyPlan.objects.get(id=pid)
        char = cp.ch
        schedule_id = cp.schedule_id

        context = {'ccpid': pid, 'schedule_id': schedule_id, 'char': cp.ch}

        return TemplateResponse(self.request, [
            'viewrects/cp_details.html'
            ], context)

class PPDetailView(CommAdminView):

    @csrf_protect_m
    def get(self, request, *args, **kwargs):
        #pid = request.GET['pk']
        # 这里的参数和页面，根据API再做调整
        context={'schedule_id': 0}
        return TemplateResponse(self.request, [
            'viewrects/pp_details.html'
            ], context)

class GeneTaskView(CommAdminView):

    @csrf_protect_m
    def get(self, request, *args, **kwargs):
        # 这里的参数和页面，根据API再做调整
        context = self.get_context()
        return TemplateResponse(self.request, [
            'tasks/gene_task.html'
            ], context)

site.register_view(r'^tasks/gene_task/$', GeneTaskView, name='gene_task')
site.register_view(r'^rect/pagerects/$',PPDetailView, name='pp_detail')
site.register_view(r'^rect/schedule/detail2/$',CCDetailView, name='cc_detail')
site.register_view(r'^rect/charclassifyplan/detail2/$',ClassifyDetailView, name='cp_detail')

