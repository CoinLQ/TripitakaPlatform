from django.conf import settings
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.db.models import Q

from tdata.models import *
from tasks.models import *
from tasks.common import SEPARATORS_PATTERN, judge_merge_text_punct, ReelText,\
extract_page_line_separators
from tasks.task_controller import publish_correct_result, correct_submit_result

import json, re
from operator import attrgetter, itemgetter

# TODO: 检查权限
#@login_required
def do_correct_task(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    if task.typ != Task.TYPE_CORRECT:
        return redirect('/')
    return render(request, 'tasks/do_correct_task.html', {'task_id': task_id})

#@login_required
def do_correct_verify_task(request, task_id):
    if request.method == 'POST':
        return do_correct_verify_task_post(request, task_id)
    else:
        return render(request, 'tasks/do_correct_verify_task.html', {'task_id': task_id })

def do_correct_verify_task_post(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    if task.status == Task.STATUS_FINISHED:
        return redirect('do_correct_verify_task', task_id=task_id)
    correctsegs = CorrectSeg.objects.filter(task_id=task_id)
    d = {}
    for seg in correctsegs:
        d[seg.id] = seg
    save_seg_ids = []
    for k, v in request.POST.items():
        if k.startswith('segtext_'):
            seg_id = int(k[8:])
            d[seg_id].selected_text = v
            save_seg_ids.append(seg_id)
        elif k.startswith('segpage_'):
            seg_id = int(k[8:])
            d[seg_id].page_no = int(v)
        elif k.startswith('segline_'):
            seg_id = int(k[8:])
            d[seg_id].line_no = int(v)
        elif k.startswith('segchar_'):
            seg_id = int(k[8:])
            d[seg_id].char_no = int(v)
        elif k.startswith('segpos_'):
            seg_id = int(k[7:])
            d[seg_id].position = int(v)
        elif k.startswith('segdoubt_'):
            seg_id = int(k[9:])
            d[seg_id].doubt_comment = v
    with transaction.atomic():
        for seg_id in save_seg_ids:
            d[seg_id].save()
        reel_text = request.POST.get('reel_text').replace('\r\n', '\n')
        if reel_text:
            separators = extract_page_line_separators(reel_text)
            task.separators = json.dumps(separators, separators=(',', ':'))
            task.result = reel_text
            task.save(update_fields=['result', 'separators'])
        finished = request.POST.get('finished')
        if finished == '1':
            task.status = Task.STATUS_FINISHED
            task.save(update_fields=['status'])
            publish_correct_result(task)
    return redirect('do_correct_verify_task', task_id=task_id)