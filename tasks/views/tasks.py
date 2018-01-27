from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.db.models import Q

from django.views.generic.edit import FormView
from tasks.forms import BatchTaskForm

from sutradata.common import judge_merge_text_punct, ReelText, extract_page_line_separators
from sutradata.models import *
from tasks.models import *

import json, re
from operator import attrgetter, itemgetter

SEPARATORS_PATTERN = re.compile('[p\n]')

class BatchTaskCreate(FormView):
    template_name = 'tasks/batchtask_create.html'
    form_class = BatchTaskForm
    success_url = '/batchtasks'

    def form_valid(self, form):
        # TODO: 创建批次任务，任务
        return super().form_valid(form)

@login_required
def batchtask_list(request):
    batchtask_lst = BatchTask.objects.filter(publisher=request.user)
    context = {'batchtask_lst': batchtask_lst}
    return render(request, 'tasks/batchtask_list.html', context)