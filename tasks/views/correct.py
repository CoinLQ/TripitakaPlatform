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
from tasks.task_controller import publish_correct_result

import json, re
from operator import attrgetter, itemgetter

# TODO: 检查权限
#@login_required
def do_correct_task(request, task_id):
    if request.method == 'POST':
        return do_correct_task_post(request, task_id)
    else:
        task = get_object_or_404(Task, pk=task_id)
        compare_reel = task.compare_reel
        comparesegs = [seg for seg in compare_reel.compareseg_set.all()]
        segs = []
        for compareseg in comparesegs:
            correctsegs = CorrectSeg.objects.filter(task=task, compare_seg=compareseg).order_by('position')
            seg = {
                'id': correctsegs[0].id,
                'base_pos': compareseg.base_pos,
                'ocr_text': compareseg.ocr_text,
                'base_text': compareseg.base_text,
                'selected_text': correctsegs[0].selected_text,
                'doubt_comment': correctsegs[0].doubt_comment,
                'pos': correctsegs[0].position,
                }
            segs.append(seg)
        context = {
            'task': task,
            'base_text': compare_reel.base_text,
            'segs': segs,
            'segs_json': json.dumps(segs),
            'start_vol_page': task.reel.start_vol_page,
            'image_url_prefix': settings.IMAGE_URL_PREFIX,
            }
        sort_index_lst = []
        if request.GET.get('order_by', '') == 'char':
            i = 0
            segs_len = len(segs)
            while i < segs_len:
                sort_index_lst.append( (i, segs[i]['selected_text'][:1]) )
                i += 1
            sort_index_lst.sort(key=itemgetter(1))
            context['sort_index_lst'] = sort_index_lst
        return render(request, 'tasks/do_correct_task.html', context)

def do_correct_task_post(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    if task.status == Task.STATUS_FINISHED:
        return redirect('do_correct_task', task_id=task_id)
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
            separators_json = json.dumps(separators, separators=(',', ':'))
            Task.objects.filter(id=task_id).update(result=reel_text, separators=separators_json)
        finished = request.POST.get('finished')
        if finished == '1':
            Task.objects.filter(id=task_id).update(status=Task.STATUS_FINISHED)
    if finished == '1':
        # 检查一组的几个文字校对任务是否都已完成
        correct_tasks = Task.objects.filter(reel=task.reel, batch_task=task.batch_task, typ=Task.TYPE_CORRECT)
        all_finished = True
        for correct_task in correct_tasks:
            if correct_task.status != Task.STATUS_FINISHED:
                all_finished = False
        task_count = len(correct_tasks)
        # 如果都已完成
        if all_finished and task_count > 1:
            # 查到文字校对审定任务
            correct_verify_tasks = [task for task in Task.objects.filter(reel=task.reel, batch_task=task.batch_task, typ=Task.TYPE_CORRECT_VERIFY)]
            if len(correct_verify_tasks) == 0:
                return redirect('/')
            correct_verify_task = correct_verify_tasks[0]

            # 比较一组的几个文字校对任务的结果
            correctsegs_lst = [ [] ] * task_count
            i = 0
            while i < task_count:
                correctsegs_lst[i] = [ seg for seg in CorrectSeg.objects.filter(task=correct_tasks[i]).order_by('compare_seg_id') ]
                i += 1
            correctsegs_verify = []
            seg_count = len(correctsegs_lst[0])
            i = 0
            while i < seg_count:
                seg = CorrectSeg(task=correct_verify_task, compare_seg=correctsegs_lst[0][i].compare_seg)
                j = 0
                all_equal = True
                while j < task_count - 1:
                    if correctsegs_lst[j][i].selected_text != correctsegs_lst[j+1][i].selected_text:
                        all_equal = False
                        break
                    j += 1
                if all_equal: # TODO: 都相同的文本段是否需要保存？
                    seg.diff_flag = 0
                seg.selected_text = correctsegs_lst[0][i].selected_text
                seg.position = correctsegs_lst[0][i].position
                seg.page_no = correctsegs_lst[0][i].page_no
                seg.line_no = correctsegs_lst[0][i].line_no
                seg.char_no = correctsegs_lst[0][i].char_no
                correctsegs_verify.append(seg)
                i += 1

            with transaction.atomic():
                # 保存文字校对审定任务的correctsegs
                CorrectSeg.objects.bulk_create(correctsegs_verify)

                # 文字校对审定任务设为待领取
                Task.objects.filter(reel=task.reel,
                batch_task=task.batch_task,
                typ=Task.TYPE_CORRECT_VERIFY).update(separators=correct_tasks[0].separators, status=Task.STATUS_READY)
    return redirect('do_correct_task', task_id=task_id)

#@login_required
def do_correct_verify_task(request, task_id):
    if request.method == 'POST':
        return do_correct_verify_task_post(request, task_id)
    else:
        task = get_object_or_404(Task, pk=task_id)
        if task.status == Task.STATUS_NOT_READY:
            return redirect('/')
        correct_tasks = Task.objects.filter(reel=task.reel, batch_task=task.batch_task, typ=Task.TYPE_CORRECT)
        correct_task_ids = [task.id for task in correct_tasks]
        segs = []
        for seg_verify in CorrectSeg.objects.filter(task=task).filter(~Q(diff_flag=0)).order_by('position'):
            #print(seg_verify.id)
            seg = {}
            seg['id'] = seg_verify.id
            seg['pos'] = seg_verify.position
            correctsegs = list(CorrectSeg.objects.filter(compare_seg=seg_verify.compare_seg, task_id__in=correct_task_ids))
            correctsegs.sort(key=attrgetter('task_id'))
            correct_segs = []
            for correctseg in correctsegs:
                correct_segs.append({
                    'selected_text': correctseg.selected_text,
                    'doubt_comment': correctseg.doubt_comment,
                })
            seg['base_pos'] = correctsegs[0].position
            seg['correct_segs'] = correct_segs
            seg['selected_text'] = seg_verify.selected_text
            seg['page_no'] = seg_verify.page_no
            seg['line_no'] = seg_verify.line_no
            seg['char_no'] = seg_verify.char_no
            seg['doubt_comment'] = seg_verify.doubt_comment
            segs.append(seg)
        base_text = SEPARATORS_PATTERN.sub('', correct_tasks[0].result)
        correct_count = len(correct_tasks)
        return render(request, 'tasks/do_correct_verify_task.html', {'task': task,
    'correct_tasks': correct_tasks,
    'correct_count': correct_count,
    'base_text': base_text,
    'segs': segs,
    'segs_json': json.dumps(segs),
    'start_vol_page': task.reel.start_vol_page,
    'image_url_prefix': settings.IMAGE_URL_PREFIX,
    })

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