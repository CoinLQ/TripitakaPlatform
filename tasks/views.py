from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction

from django.views.generic.edit import FormView
from .forms import BatchTaskForm

from sutradata.models import *
from .models import *

import json

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

#@login_required
def do_correct_task(request, task_id):
    if request.method == 'GET':
        task = get_object_or_404(Task, pk=task_id)
        compare_reel = task.compare_reel
        comparesegs = [seg for seg in compare_reel.compareseg_set.all()]
        segs = []
        for compareseg in comparesegs:
            correctsegs = CorrectSeg.objects.filter(task=task, compare_seg=compareseg)
            seg = {
                'id': correctsegs[0].id,
                'base_pos': compareseg.base_pos,
                'ocr_text': compareseg.ocr_text,
                'base_text': compareseg.base_text,
                'selected_text': correctsegs[0].selected_text,
                'pos': correctsegs[0].position,
            }
            segs.append(seg)
        return render(request, 'tasks/do_correctreel.html', {'task': task,
    'base_reel_text': compare_reel.base_reel.text,
    'segs': segs, 'segs_json': json.dumps(segs),
    'sid': task.reel.sutra.sid,
    'start_vol': '%03d' % task.reel.start_vol,
    'start_vol_page': task.reel.start_vol_page,
    })
    else:
        correctsegs = CorrectSeg.objects.filter(task_id=task_id)
        d = {}
        for seg in correctsegs:
            d[seg.id] = seg
        with transaction.atomic():
            for k, v in request.POST.items():
                if k.startswith('segtext_'):
                    seg_id = int(k[8:])
                    d[seg_id].selected_text = v
                    d[seg_id].save()
            reel_text = request.POST.get('reel_text').replace('\r\n', '\n')
            if reel_text:
                separators = Reel.extract_page_line_separators(reel_text)
                separators_json = json.dumps(separators, separators=(',', ':'))
                Task.objects.filter(id=task_id).update(result=reel_text, separators=separators_json)
            finished = request.POST.get('finished')
            if finished == '1':
                Task.objects.filter(id=task_id).update(status=Task.STATUS_FINISHED)
        return redirect('do_correct_task', task_id=task_id)

def update_correct_task_result(request, task_id):
    if request.method == 'POST':
        reel_text = request.POST.get('reel_text').replace('\r\n', '\n')
        if reel_text:
            separators = Reel.extract_page_line_separators(reel_text)
            separators_json = json.dumps(separators, separators=(',', ':'))
            Task.objects.filter(id=task_id).update(result=reel_text, separators=separators_json)
    return redirect('do_correct_task', task_id=task_id)