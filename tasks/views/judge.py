from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.db.models import Q

from sutradata.common import judge_merge_text_punct, ReelText, extract_page_line_separators
from sutradata.models import *
from tasks.models import *

import json, re
from operator import attrgetter, itemgetter

SEPARATORS_PATTERN = re.compile('[p\n]')

def get_reeltext(lqsutra, tripitaka_id, reel_no):
    sutra = Sutra.objects.get(lqsutra=lqsutra, tripitaka_id=tripitaka_id)
    reel = Reel.objects.get(sutra=sutra, reel_no=reel_no)
    reeltext = ReelText(text=reel.correct_text, tripitaka_id=tripitaka_id,
    sid=sutra.sid, vol_no=reel.start_vol, start_vol_page=reel.start_vol_page)
    return reeltext

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

def api_judge_is_all_selected(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    if task.status == Task.STATUS_NOT_READY:
        return JsonResponse({'result': 'not ready'})
    reeldiff = task.reeldiff
    diffsegs = list(DiffSeg.objects.filter(reel_diff=reeldiff))
    all_selected = True
    doubt_count = 0
    for diffseg in diffsegs:
        if diffseg.status == 0:
            all_selected = False
        elif diffseg.status == 2:
            doubt_count += 1
    return JsonResponse({'result': 'ok', 'all_selected': all_selected, 'doubt_count': doubt_count})

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