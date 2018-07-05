from django.conf import settings
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.db.models import Q

from tdata.models import *
from tasks.models import *

import json, re
from operator import attrgetter, itemgetter

def do_correct_task(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    if task.typ not in [Task.TYPE_CORRECT, Task.TYPE_CORRECT_VERIFY, Task.TYPE_CORRECT_DIFFICULT]:
        return redirect('/')
    try:
        page = int(request.GET.get('page', 0))
    except:
        page = 0
    host = settings.FRONT_HOST
    return render(request, 'tasks/do_correct_task.html', {'task': task, 'page': page, 'host': host})

def process_abnormal_line_count(request, task_id):
    return redirect('/')
