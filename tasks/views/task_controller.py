from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.db.models import Q

from sutradata.common import judge_merge_text_punct, ReelText, extract_page_line_separators
from sutradata.models import *
from tasks.models import *
from tasks.views.reeldiff_processor import generate_reeldiff

import json, re, logging
from operator import attrgetter, itemgetter
from difflib import SequenceMatcher

SEPARATORS_PATTERN = re.compile('[p\n]')

logger = logging.getLogger(__name__)

def get_reeltext(lqsutra, tripitaka_id, reel_no):
    sutra = Sutra.objects.get(lqsutra=lqsutra, tripitaka_id=tripitaka_id)
    reel = Reel.objects.get(sutra=sutra, reel_no=reel_no)
    reel_correct_texts = list(ReelCorrectText.objects.filter(reel=reel).order_by('-id')[0:1])
    if not reel_correct_texts:
        return None
    reel_correct_text = reel_correct_texts[0]
    reeltext = ReelText(text=reel_correct_text.text, tripitaka_id=tripitaka_id,
    sid=sutra.sid, vol_no=reel.start_vol, start_vol_page=reel.start_vol_page)
    return reeltext

def create_correct_tasks(batchtask, reel, base_reel_lst, correct_times, correct_verify_times):
    # Correct Task
    separators = extract_page_line_separators(reel.text)
    separators_json = json.dumps(separators, separators=(',', ':'))

    compare_reel1 = CompareReel(reel=reel, base_reel=base_reel_lst[0])
    compare_reel1.save()
    compare_reel2 = CompareReel(reel=reel, base_reel=base_reel_lst[1])
    compare_reel2.save()

    task_lst = []
    for task_no in range(1, correct_times + 1):
        task = Task(batch_task=batchtask, reel=reel, typ=Task.TYPE_CORRECT, task_no=task_no, status=Task.STATUS_NOT_READY,
        publisher=batchtask.publisher)
        if task_no <= int((correct_times + 1) / 2):
            task.compare_reel = compare_reel1
        else:
            task.compare_reel = compare_reel2
        task.separators = separators_json
        task.save()
        task_lst.append(task)

    if correct_verify_times:
        task = Task(batch_task=batchtask, reel=reel, typ=Task.TYPE_CORRECT_VERIFY, task_no=0, status=Task.STATUS_NOT_READY,
        publisher=batchtask.publisher)
        task.save()
    
    for task in task_lst:
        base_reel = task.compare_reel.base_reel
        reel = task.compare_reel.reel
        diff_lst = CompareReel.generate_compare_reel(base_reel.text, reel.text)
        for tag, base_pos, pos, base_text, ocr_text in diff_lst:
            compare_seg = CompareSeg(compare_reel=task.compare_reel,
            base_pos=base_pos,
            ocr_text=ocr_text, base_text=base_text)
            compare_seg.save()
            for task in task_lst:
                correct_seg = CorrectSeg(task=task, compare_seg=compare_seg)
                correct_seg.selected_text = compare_seg.ocr_text
                correct_seg.position = pos
                correct_seg.save()

# 从龙泉大藏经来发布
def create_tasks_for_batchtask(batchtask, reel_lst,
correct_times, correct_verify_times,
judge_times, judge_verify_times,
punct_times, punct_verify_times,
lqpunct_times, lqpunct_verify_times,
mark_times, mark_verify_times,
lqmark_times, lqmark_verify_times):
    '''
    reel_lst格式： [(lqsutra, reel_no), (lqsutra, reel_no)]
    '''
    for lqsutra, reel_no in reel_lst:
        # 创建文字校对任务
        sutra_lst = list(lqsutra.sutra_set.all())
        # 先得到两个base_reel，CBETA和高丽藏
        first_base_sutra = None
        second_base_sutra = None
        for sutra in sutra_lst:
            if sutra.sid.startswith('CB'):
                first_base_sutra = sutra
            if sutra.sid.startswith('GL'):
                second_base_sutra = sutra
        if not first_base_sutra or not second_base_sutra:
            # 记录错误
            print('no base sutra')
            continue
        base_reel_lst = []
        reel = Reel.objects.get(sutra=first_base_sutra, reel_no=reel_no)
        base_reel_lst.append(reel)
        reel = Reel.objects.get(sutra=second_base_sutra, reel_no=reel_no)
        base_reel_lst.append(reel)

        for sutra in sutra_lst:
            try:
                reel = Reel.objects.get(sutra=sutra, reel_no=reel_no)
            except:
                # TODO: 记录错误
                continue
            create_correct_tasks(batchtask, reel, base_reel_lst, correct_times, correct_verify_times)
            # TODO: other tasks

def create_reeldiff_for_judge_task(lqreel, lqsutra):
    reel_no = lqreel.reel_no
    judge_task_lst = list(Task.objects.filter(lqreel=lqreel, typ=Task.TYPE_JUDGE, status=Task.STATUS_NOT_READY))
    if not judge_task_lst:
        print('没有校勘判取任务: ', lqreel)
        logging.info('没有校勘判取任务: %s' % lqreel)
        return None

    sutra_lst = list(lqsutra.sutra_set.all())
    sutra_id_lst = [sutra.id for sutra in sutra_lst]

    # 找实体卷，底本和对校本
    reel_lst = list(Reel.objects.filter(sutra_id__in=sutra_id_lst, reel_no=reel_no, edition_type__in=[Reel.EDITION_TYPE_BASE, Reel.EDITION_TYPE_CHECKED]))
    reel_id_lst = [reel.id for reel in reel_lst]
    if len(reel_lst) <= 1:
        return None

    try:
        base_reel_index = reel_id_lst.index(judge_task_lst[0].base_reel.id)
    except:
        logging.error('校勘判取任务%s设定的底本不存在' % judge_task_lst[0].id)
        return None
    # 将底本换到第一个位置
    reel = reel_lst[base_reel_index]
    reel_lst[base_reel_index] = reel_lst[0]
    reel_lst[0] = reel
    reel_id_lst = [reel.id for reel in reel_lst]
    new_sutra_lst = [reel.sutra for reel in reel_lst]
    
    reel_id_to_text = {}
    reel_id_to_reel_correct_text = {}
    for reel_correct_text in ReelCorrectText.objects.filter(reel_id__in=reel_id_lst):
        reel_id = reel_correct_text.reel_id
        if reel_id in reel_id_to_text and reel_id_to_reel_correct_text[reel_id].created_at > reel_correct_text.created_at:
            pass
        else:
            reel_id_to_text[reel_id] = reel_correct_text.text
            reel_id_to_reel_correct_text[reel_id] = reel_correct_text
    if len(reel_id_to_text) != len(reel_lst):
        print('reel_id_to_text', reel_id_to_created_at, reel_lst)
        logging.info('此卷的文字校对还未完成，暂时不触发校勘判取任务')
        return None
    correct_text_lst = []
    reel_correct_text_lst = []
    for reel in reel_lst:
        correct_text_lst.append( reel_id_to_text[reel.id] )
        reel_correct_text_lst.append( reel_id_to_reel_correct_text[reel.id] )
    base_text = SEPARATORS_PATTERN.sub('', correct_text_lst[0])
    reeldiff = ReelDiff(lqsutra=lqsutra, reel_no=reel_no, base_sutra=new_sutra_lst[0], base_text=base_text)
    reeldiff.save()
    reeldiff.correct_texts.set(reel_correct_text_lst)
    
    generate_reeldiff(reeldiff, new_sutra_lst, reel_lst, correct_text_lst)
    task_id_lst = [task.id for task in judge_task_lst]
    Task.objects.filter(id__in=task_id_lst).update(reeldiff=reeldiff, status=Task.STATUS_READY)
    judge_verify_task_lst = list(Task.objects.filter(lqreel=lqreel, typ=Task.TYPE_JUDGE_VERIFY, status=Task.STATUS_NOT_READY))
    task_id_lst = [task.id for task in judge_verify_task_lst]
    Task.objects.filter(id__in=task_id_lst).update(reeldiff=reeldiff)
    #Task.objects.filter(id__in=task_id_lst).update(reeldiff=reeldiff, status=Task.STATUS_PROCESSING) # for test

def publish_correct_result(task):
    '''
    发布文字校对的结果，供校勘判取使用
    '''
    sutra = task.reel.sutra
    reel_no = task.reel.reel_no
    text_changed = False
    saved_reel_correct_texts = list(ReelCorrectText.objects.filter(reel=task.reel).order_by('-id')[0:1])
    if len(saved_reel_correct_texts) == 0:
        reel_correct_text = ReelCorrectText(reel=task.reel, text=task.result, task=task)
        reel_correct_text.save()
    else: # 与最新的一份记录比较
        text1 = saved_reel_correct_texts[0].text
        text2 = task.result
        if text1 != text2:
            reel_correct_text = ReelCorrectText(reel=task.reel, text=text2, task=task)
            reel_correct_text.save()
            text_changed = True

    # 针对龙泉藏经这一卷查找是否有未就绪的校勘判取任务
    lqsutra = sutra.lqsutra
    if not lqsutra:
        print('没有关联的龙泉藏经')
        logging.error('没有关联的龙泉藏经')
        return None
    try:
        lqreel = LQReel.objects.get(lqsutra=lqsutra, reel_no=reel_no)
    except:
        print('没找到龙泉藏经卷对应的记录')
        logging.error('没找到龙泉藏经卷对应的记录')
        return None
    
    create_reeldiff_for_judge_task(lqreel, lqsutra)

def correct_submit_result():
    '''
    文字校对提交结果
    '''
    pass

def correct_verify_submit_result(task):
    '''
    文字校对审定发布结果
    '''
    pass

def judge_submit_result(task):
    '''
    校勘判取提交结果
    '''
    print('judge_submit_result')
    lqreel = task.lqreel
    judge_tasks = list(Task.objects.filter(batch_task_id=task.batch_task_id, lqreel_id=lqreel.id, typ=Task.TYPE_JUDGE).all())
    task_count = len(judge_tasks)
    if task_count == 0:
        return None
    all_finished = True
    for judge_task in judge_tasks:
        if judge_task.status != Task.STATUS_FINISHED:
            all_finished = False
    if not all_finished:
        return None

    judge_verify_tasks = list(Task.objects.filter(batch_task_id=task.batch_task_id, lqreel_id=lqreel.id, typ=Task.TYPE_JUDGE_VERIFY).all())
    if len(judge_verify_tasks) == 0:
        # 直接发布校勘判取结果
        # publish_judge_result(task)
        return None
    judge_verify_task = judge_verify_tasks[0]
    if task_count == 1:
        # 直接复制结果到校勘判取审定任务
        diffsegresults = []
        for diffsegresult in judge_tasks[0].diffsegresult_set.all():
            diffsegresult.task = judge_verify_task
            diffsegresult.id = None
            diffsegresults.append(diffsegresult)
        DiffSegResult.objects.bulk_create(diffsegresults)
        return None

    # 比较校勘判取任务的结果
    diffsegresults_lst = []
    for i in range(task_count):
        diffsegresults = list(DiffSegResult.objects.filter(task_id=judge_tasks[i].id).order_by('diffseg__diffseg_no').all())
        diffsegresults_lst.append(diffsegresults)

    to_save_diffsegresults = []
    diffseg_count = len(diffsegresults_lst[0])
    for i in range(diffseg_count):
        all_equal = True
        for j in range(task_count-1):
            diffsegresult1 = diffsegresults_lst[j][i]
            diffsegresult2 = diffsegresults_lst[j+1][i]
            print('compare diffsegresult: ', diffsegresult1.diffseg.diffseg_no, diffsegresult2.diffseg.diffseg_no)
            if not diffsegresult1.is_equal(diffsegresult2):
                all_equal = False
                break
        print('all_equal: ', all_equal)
        if all_equal:
            # 复制结果到校勘判取审定任务
            diffsegresult = diffsegresults_lst[0][i]
            diffsegresult.id = None
            diffsegresult.task_id = judge_verify_task.id
            diffsegresult.all_equal = True
            to_save_diffsegresults.append(diffsegresult)
        else:
            diffsegresult = DiffSegResult(task_id=judge_verify_task.id, diffseg_id=diffsegresults_lst[0][i].diffseg_id)
            to_save_diffsegresults.append(diffsegresult)
    DiffSegResult.objects.bulk_create(to_save_diffsegresults)
    
    # 设定校勘判取审定任务状态
    Task.objects.filter(id=judge_verify_task.id).update(status=Task.STATUS_READY)

def publish_judge_result(task):
    '''
    发布校勘判取结果
    '''
    print('publish_judge_result')
    pass