from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.db.models import Q

from django.views.generic.edit import FormView
from .forms import BatchTaskForm

from sutradata.common import judge_merge_text_punct, ReelText, extract_page_line_separators
from sutradata.models import *
from .models import *

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

def get_reeltext(lqsutra, tripitaka_id, reel_no):
    sutra = Sutra.objects.get(lqsutra=lqsutra, tripitaka_id=tripitaka_id)
    reel = Reel.objects.get(sutra=sutra, reel_no=reel_no)
    reeltext = ReelText(text=reel.correct_text, tripitaka_id=tripitaka_id,
    sid=sutra.sid, vol_no=reel.start_vol, start_vol_page=reel.start_vol_page)
    return reeltext

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
        base_text = SEPARATORS_PATTERN.sub('', compare_reel.base_reel.text)
        context = {
            'task': task,
            'base_text': base_text,
            'segs': segs,
            'segs_json': json.dumps(segs),
            'sid': task.reel.sutra.sid,
            'start_vol': '%03d' % task.reel.start_vol,
            'start_vol_page': task.reel.start_vol_page,
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
                for seg in correctsegs_verify:
                    seg.save()

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
    'sid': task.reel.sutra.sid,
    'start_vol': '%03d' % task.reel.start_vol,
    'start_vol_page': task.reel.start_vol_page,
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
            separators_json = json.dumps(separators, separators=(',', ':'))
            Task.objects.filter(id=task_id).update(result=reel_text, separators=separators_json)
        finished = request.POST.get('finished')
        if finished == '1':
            Task.objects.filter(id=task_id).update(status=Task.STATUS_FINISHED)
            task.reel.update(correct_text=reel_text)
    return redirect('do_correct_verify_task', task_id=task_id)

def do_judge_task(request, task_id):
    if request.method == 'POST':
        return do_judge_task_post(request, task_id)
    else:
        task = get_object_or_404(Task, pk=task_id)
        if task.status == Task.STATUS_NOT_READY:
            return redirect('/')
        reeldiff = task.reeldiff
        base_tripitaka = reeldiff.base_sutra.tripitaka
        diffseg_count = DiffSeg.objects.filter(reel_diff=reeldiff).count()
        if diffseg_count > 0:
            diffseg_page_count = int((diffseg_count - 1) / 5) + 1
        else:
            diffseg_page_count = 0
        diffsegs = list(DiffSeg.objects.filter(reel_diff=reeldiff).order_by('base_pos'))
        diffseg_pos_lst = []
        for diffseg in diffsegs:
            diffseg.text_tname_map = {}
            for diffsegtext in diffseg.diffsegtext_set.all():
                tname_lst = diffseg.text_tname_map.setdefault(diffsegtext.text, [])
                tname_lst.append('<a href="/sutra_pages/%s/view?cid=%s" start-cid="%s" end-cid="%s" target="_blank">%s</a>' % (
                    diffsegtext.start_cid[:18],
                    diffsegtext.start_cid,
                    diffsegtext.start_cid,
                    diffsegtext.end_cid,
                    diffsegtext.tripitaka.shortname
                    ))
                if base_tripitaka == diffsegtext.tripitaka:
                    diffseg.base_text = diffsegtext.text
            if not diffseg.base_text:
                diffseg.base_text = '底本为空'
            diff_str_lst = []
            for text, tname_lst in diffseg.text_tname_map.items():
                if text == '':
                    s = '为空'
                else:
                    s = '：%s' % text
                diff_str_lst.append( '%s%s' % ('/'.join(tname_lst), s) )
            diffseg.diff_desc = '，'.join(diff_str_lst) + '。'
            diffseg_pos_lst.append({
                'diffseg_id': diffseg.id,
                'base_pos': diffseg.base_pos,
                'base_length': diffseg.base_length,
            })

        diffseg_lst = get_diffseg_lst(diffsegs[0:5], base_tripitaka)
        base_reel = Reel.objects.get(sutra=reeldiff.base_sutra, reel_no=reeldiff.reel_no)
        context = {
            'task': task,
            'base_text': task.reeldiff.base_text,
            'punct_lst': base_reel.punctuation,
            'diffseg_pos_lst': json.dumps(diffseg_pos_lst),
            'diffseg_lst': json.dumps(diffseg_lst),
            'diffseg_page_count': diffseg_page_count,
        }
        return render(request, 'tasks/do_judge_task.html', context)

def do_judge_task_post(request, task_id):
    pass

def get_diffseg_lst(diffsegs, base_tripitaka):
    diffseg_lst = []
    for diffseg in diffsegs:
        seg = {}
        text_tname_map = {}
        for diffsegtext in diffseg.diffsegtext_set.all():
            tname_lst = text_tname_map.setdefault(diffsegtext.text, [])
            tname_lst.append({
                'pid': diffsegtext.start_cid[:18],
                'start_cid': diffsegtext.start_cid,
                'end_cid': diffsegtext.end_cid,
                'tname': diffsegtext.tripitaka.shortname,
                'tripitaka_id': diffsegtext.tripitaka_id,
            })
            if base_tripitaka == diffsegtext.tripitaka:
                if diffsegtext.text:
                    base_text = diffsegtext.text
                else:
                    base_text = '底本为空'
                seg['base_text'] = base_text
        text_diffsegtexts_map = []
        for k, v in text_tname_map.items():
            text_diffsegtexts_map.append({
                'text': k,
                'diffsegtexts': v,
            })
        seg['text_diffsegtexts_map'] = text_diffsegtexts_map
        if diffseg.status == 2:
            seg['doubt'] = 1
        else:
            seg['doubt'] = 0
        seg['doubt_comment'] = diffseg.doubt_comment
        seg['id'] = diffseg.id
        seg['base_pos'] = diffseg.base_pos
        if diffseg.selected_text is not None:
            seg['selected'] = 1
            seg['selected_text'] = diffseg.selected_text
            if diffseg.selected_text in text_tname_map:
                seg['selected_tname'] = text_tname_map[diffseg.selected_text][0]['tname']
        else:
            seg['selected'] = 0
        diffseg_lst.append(seg)
    return diffseg_lst

def api_judge_diffsegs(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    if task.status == Task.STATUS_NOT_READY:
        return JsonResponse({'result': 'not ready'})
    try:
        p = int(request.GET.get('p', 1))
    except:
        p = 1
    reeldiff = task.reeldiff
    base_tripitaka = reeldiff.base_sutra.tripitaka
    diffsegs = list(DiffSeg.objects.filter(reel_diff=reeldiff).order_by('base_pos')[(p-1)*5: p*5])
    diffseg_lst = get_diffseg_lst(diffsegs, base_tripitaka)
    return JsonResponse({'result': 'ok', 'diffsegs': diffseg_lst})

def api_judge_diffseg_pos_list(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    if task.status == Task.STATUS_NOT_READY:
        return JsonResponse({'result': 'not ready'})
    reeldiff = task.reeldiff
    diffsegs = list(DiffSeg.objects.filter(reel_diff=reeldiff).order_by('base_pos'))
    diffseg_pos_lst = []
    for diffseg in diffsegs:
        diffseg_pos_lst.append({
            'diffseg_id': diffseg.id,
            'base_pos': diffseg.base_pos,
            'base_length': diffseg.base_length,
        })
    return JsonResponse({'result': 'ok', 'diffseg_pos_lst': diffseg_pos_lst})

def api_judge_diffseg_select(request, task_id, diffseg_id):
    '''
    格式如下：
    {
        "selected_text": "ab",
        "doubt": 1,
        "doubt_comment": "存疑说明"
    }
    无存疑：
    {
        "selected_text": "ab",
        "doubt": 0,
        "doubt_comment": ""
    }
    '''
    if request.method != 'POST':
        return JsonResponse({'result': 'not allowed'})
    task = get_object_or_404(Task, pk=task_id)
    #TODO: 判断此任务属于当前用户

    if task.status == Task.STATUS_NOT_READY:
        return JsonResponse({'result': 'not ready'})
    json_str = request.body
    json_obj = json.loads(json_str)
    selected_text = json_obj.get('selected_text', '')
    status = 1
    if json_obj.get('doubt', 1): # 判取，并存疑
        status = 2
    doubt_comment = json_obj.get('doubt_comment', '')
    DiffSeg.objects.filter(id=diffseg_id).update(selected_text=selected_text, status=status, doubt_comment=doubt_comment)
    return JsonResponse({'result': 'ok'})

def api_judge_get_merge_list(request, task_id, diffseg_id):
    task = get_object_or_404(Task, pk=task_id)
    if task.status == Task.STATUS_NOT_READY:
        return JsonResponse({'result': 'not ready'})

    reeldiff = task.reeldiff
    base_tripitaka = reeldiff.base_sutra.tripitaka
    if 'base_pos' not in request.GET:
        return JsonResponse({'result': 'no base_pos'})
    try:
        base_pos = int(request.GET['base_pos'])
    except:
        return JsonResponse({'result': 'bad base_pos'})
    diffsegs = list(reversed(DiffSeg.objects.filter(reel_diff=reeldiff, base_pos__lte=base_pos).order_by('-base_pos')[0:3]))
    diffsegs_next = list(DiffSeg.objects.filter(reel_diff=reeldiff, base_pos__gt=base_pos).order_by('base_pos')[0:2])
    diffsegs.extend(diffsegs_next)
    diffseg_lst = get_diffseg_lst(diffsegs, base_tripitaka)
    return JsonResponse({'result': 'ok', 'diffsegs': diffseg_lst})

def api_judge_diffseg_merge(request, task_id):
    '''
    格式如下：
    {
        "diffseg_ids": [3, 4, 5]
    }
    '''
    if request.method != 'POST':
        return JsonResponse({'result': 'not allowed'})
    task = get_object_or_404(Task, pk=task_id)
    #TODO: 判断此任务属于当前用户

    if task.status == Task.STATUS_NOT_READY:
        return JsonResponse({'result': 'not ready'})
    json_str = request.body
    json_obj = json.loads(json_str)
    diffseg_ids = json_obj.get('diffseg_ids', [])
    reeldiff = task.reeldiff
    diffsegs = list(DiffSeg.objects.filter(id__in=diffseg_ids).order_by('base_pos').all())
    if len(diffsegs) != len(diffseg_ids):
        return JsonResponse({'result': 'bad data'})

    start_base_pos = 100000
    end_base_pos = 0
    for diffseg in diffsegs:
        if diffseg.reel_diff != reeldiff:
            return JsonResponse({'result': 'bad data'})

        if diffseg.base_pos < start_base_pos:
            start_base_pos = diffseg.base_pos
        if (diffseg.base_pos + diffseg.base_length) > end_base_pos:
            end_base_pos = (diffseg.base_pos + diffseg.base_length)

    # 检查[start_base_pos, end_base_pos)中是否还有其他的diffseg
    diffsegs_remained = list(DiffSeg.objects.filter(reel_diff=reeldiff, base_pos__gte=start_base_pos, base_pos__lt=end_base_pos)
    .exclude(id__in=diffseg_ids).all())
    if len(diffsegs_remained) > 0:
        return JsonResponse({'result': 'bad data'})

    # 开始合并
    last_base_pos = start_base_pos
    base_pos = start_base_pos
    base_length = end_base_pos - start_base_pos
    status = 1
    doubt_comment = ''
    doubt_comment_lst = []
    
    tripitaka_segtext_map = {}
    for diffseg in diffsegs:
        if diffseg.status == 0:
            status = 0
        elif diffseg.status == 2:
            if status == 1:
                status = 2
        if diffseg.doubt_comment:
            doubt_comment_lst.append(diffseg.doubt_comment)

        diffsegtexts = list(diffseg.diffsegtext_set.all())

        if last_base_pos == diffseg.base_pos:
            last_base_pos += diffseg.base_length
            for diffsegtext in diffsegtexts:
                if diffsegtext.tripitaka_id not in tripitaka_segtext_map:
                    tripitaka_segtext_map[diffsegtext.tripitaka_id] = {
                        'text': diffsegtext.text,
                        'position': diffsegtext.position,
                        'start_cid': diffsegtext.start_cid,
                        'end_cid': diffsegtext.end_cid,
                        'old_text': diffsegtext.text,
                    }
                else:
                    tripitaka_segtext_map[diffsegtext.tripitaka_id]['text'] += diffsegtext.text
        elif last_base_pos < diffseg.base_pos: # 还需要插入底本的文本
            s = reeldiff.base_text[last_base_pos:diffseg.base_pos]
            last_base_pos = diffseg.base_pos
            for tripitaka_id, v in tripitaka_segtext_map.items():
                v['text'] += s
            last_base_pos += diffseg.base_length
            for diffsegtext in diffsegtexts:
                tripitaka_segtext_map[diffsegtext.tripitaka_id]['text'] += diffsegtext.text
        else:
            return JsonResponse({'result': 'bad data'})
    if doubt_comment_lst:
        doubt_comment = ' '.join(doubt_comment_lst)
    
    # 数据库操作
    new_diffseg = DiffSeg(reel_diff=None, selected_text=None, base_pos=base_pos,
    base_length=base_length, status=status, doubt_comment=doubt_comment)
    new_diffseg.save()
    
    for tripitaka_id, v in tripitaka_segtext_map.items():
        end_cid = ''
        if v['text'] != v['old_text']: # 重新计算end_cid
            sutra = Sutra.objects.get(lqsutra=reeldiff.lqsutra, tripitaka_id=tripitaka_id)
            reel = Reel.objects.get(sutra=sutra, reel_no=reeldiff.reel_no)
            reeltext = ReelText(text=reel.correct_text, tripitaka_id=tripitaka_id,
            sid=sutra.sid, vol_no=reel.start_vol, start_vol_page=reel.start_vol_page)
            start_cid, end_cid = reeltext.get_cid_range(v['position'], v['position'] + len(v['text']))
        else:
            end_cid = v['end_cid']
        diffsegtext = DiffSegText(diff_seg=new_diffseg, tripitaka_id=tripitaka_id, text=v['text'], position=v['position'],
        start_cid=v['start_cid'], end_cid=end_cid)
        diffsegtext.save()
    with transaction.atomic(): # 事务操作，设置新DiffSeg的reel_diff，并删除老的DiffSeg
        diffsegs = list(DiffSeg.objects.filter(id__in=diffseg_ids).all())
        if len(diffsegs) == len(diffseg_ids):
            DiffSeg.objects.filter(id=new_diffseg.id).update(reel_diff=reeldiff)
            DiffSeg.objects.filter(id__in=diffseg_ids).delete()
        else: # 可能已经是在重复操作
            DiffSeg.objects.filter(id=new_diffseg.id).delete()

    return JsonResponse({'result': 'ok'})

def api_judge_diffseg_split(request, task_id, diffseg_id):
    '''
    格式如下：
    {
        "split_count": 4,
        "tripitaka_ids": [1, 2, 3],
        "segtexts_lst": [
            ["a", "a", "A"],
            ["b", "b", "b"],
            ["c", "", ""],
            ["d", "D", "d"]
        ]
    }
    '''
    if request.method != 'POST':
        return JsonResponse({'result': 'not allowed'})
    task = get_object_or_404(Task, pk=task_id)
    #TODO: 判断此任务属于当前用户

    if task.status == Task.STATUS_NOT_READY:
        return JsonResponse({'result': 'not ready'})
    json_str = request.body
    json_obj = json.loads(json_str)
    split_count = json_obj.get('split_count', 0)
    if not split_count:
        return JsonResponse({'result': 'bad data'})
    tripitaka_ids = json_obj.get('tripitaka_ids', [])
    if not tripitaka_ids:
        return JsonResponse({'result': 'bad data'})
    tripitaka_count = len(tripitaka_ids)

    diffseg = get_object_or_404(DiffSeg, id=diffseg_id)
    diffsegtexts = list(diffseg.diffsegtext_set.all())
    if len(diffsegtexts) != tripitaka_count:
        return JsonResponse({'result': 'bad data'})

    reeldiff = task.reeldiff
    reel_no = reeldiff.reel_no
    lqsutra = reeldiff.lqsutra
    base_tripitaka_id = reeldiff.base_sutra.tripitaka_id
    try:
        base_tripitaka_index = tripitaka_ids.index(base_tripitaka_id)
    except:
        return JsonResponse({'result': 'bad data'})

    segtexts_lst = json_obj.get('segtexts_lst', [])
    if len(segtexts_lst) != split_count:
        return JsonResponse({'result': 'bad data'})

    # 校验数据
    tripitakaid_to_texts = {}
    tripitakaid_to_mergetext = {}
    for t_idx in range(tripitaka_count):
        tripitakaid_to_texts[ tripitaka_ids[t_idx] ] = []
    for i in range(split_count):
        segtexts = segtexts_lst[i]
        if len(segtexts) != tripitaka_count:
            return JsonResponse({'result': 'bad data'})
        for t_idx in range(tripitaka_count):
            tripitakaid_to_texts[ tripitaka_ids[t_idx] ].append( segtexts[t_idx] )
    for t_idx in range(tripitaka_count):
        tripitakaid_to_mergetext[ tripitaka_ids[t_idx] ] = ''.join(tripitakaid_to_texts[ tripitaka_ids[t_idx] ])

    for diffsegtext in diffsegtexts:
        if tripitakaid_to_mergetext[ diffsegtext.tripitaka_id ] != diffsegtext.text:
            return JsonResponse({'result': 'bad data'})
    # 校验数据结束

    tripitakaid_to_position = {}
    for diffsegtext in diffsegtexts:
        tripitakaid_to_position[diffsegtext.tripitaka_id] = diffsegtext.position
    tripitaka_to_reeltext = {}
    new_diffseg_lst = []
    base_pos = diffseg.base_pos
    for i in range(split_count):
        segtexts = segtexts_lst[i]
        all_equal = True
        for t_idx in range(tripitaka_count-1):
            if segtexts[t_idx] != segtexts[t_idx+1]:
                all_equal = False
                break
        if all_equal: # 不创建DiffSeg
            # 更新position
            for t_idx in range(tripitaka_count):
                tripitaka_id = tripitaka_ids[t_idx]
                tripitakaid_to_position[tripitaka_id] += len(segtexts[t_idx])
                if tripitaka_id == base_tripitaka_id:
                    base_pos = tripitakaid_to_position[tripitaka_id]
        else:
            base_length = 0
            diffsegtext_lst = []
            new_diffseg = DiffSeg(
                reel_diff=None,
                base_pos=tripitakaid_to_position[base_tripitaka_id],
                base_length=len(segtexts[base_tripitaka_index]))
            new_diffseg.save()
            new_diffseg_lst.append(new_diffseg)
            for t_idx in range(tripitaka_count):
                tripitaka_id = tripitaka_ids[t_idx]
                diffsegtext = DiffSegText(
                    diff_seg=new_diffseg,
                    tripitaka_id=tripitaka_id,
                    text=segtexts[t_idx],
                    position=tripitakaid_to_position[tripitaka_id])
                diffsegtext_lst.append(diffsegtext)
                # 重新计算start_cid, end_cid
                # 得到reeltext
                if tripitaka_id in tripitaka_to_reeltext:
                    reeltext = tripitaka_to_reeltext[tripitaka_id]
                else:
                    reeltext = get_reeltext(lqsutra, tripitaka_id, reel_no)
                    tripitaka_to_reeltext[tripitaka_id] = reeltext
                diffsegtext.start_cid, diffsegtext.end_cid = reeltext.get_cid_range(
                    diffsegtext.position,
                    diffsegtext.position + len(diffsegtext.text))
                diffsegtext.save()
                # 更新position
                tripitakaid_to_position[tripitaka_id] += len(segtexts[t_idx])

    # 最后设置新增加的DiffSeg的reel_diff，并将原DiffSeg删除
    new_diffseg_ids = []
    for new_diffseg in new_diffseg_lst:
        new_diffseg_ids.append(new_diffseg.id)    
    with transaction.atomic():
        diffsegs = list(DiffSeg.objects.filter(id=diffseg.id).all())
        print(len(diffsegs))
        if len(diffsegs) == 1:
            DiffSeg.objects.filter(id__in=new_diffseg_ids).update(reel_diff=reeldiff)
            DiffSeg.objects.filter(id=diffseg.id).delete()
        else: # 不处理重复请求
            DiffSeg.objects.filter(id__in=new_diffseg_ids).delete()

    return JsonResponse({'result': 'ok'})
