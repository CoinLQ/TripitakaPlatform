from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.db.models import Q

from tdata.models import *
from tasks.models import *
from tasks.common import SEPARATORS_PATTERN, judge_merge_text_punct, \
clean_separators, clean_jiazhu, compute_accurate_cut
from tasks.ocr_compare import OCRCompare
from tasks.utils.punct_process import PunctProcess
from tasks.reeldiff_processor import is_sutra_ready_for_judge, create_data_for_judge_tasks, \
create_new_data_for_judge_tasks
import json, re, logging, traceback
from operator import attrgetter, itemgetter
from background_task import background

logger = logging.getLogger(__name__)

def create_correct_tasks(batchtask, reel, base_reel_lst, sutra_to_body, correct_times, correct_verify_times):
    if correct_times == 0:
        return
    if reel.sutra.sid.startswith('CB') or reel.sutra.sid.startswith('GL'): # 不对CBETA, GL生成任务
        return
    # Correct Task
    print('create_correct_tasks: ', reel)
    reel_ocr_texts = list(ReelOCRText.objects.filter(reel=reel))
    if len(reel_ocr_texts) == 0:
        print('no ocr text for reel: ', reel)
        return None
    reel_ocr_text = reel_ocr_texts[0]
    ocr_text = OCRCompare.preprocess_ocr_text(reel_ocr_text.text)
    correctsegs_lst = []
    for base_reel in base_reel_lst:
        base_reel_correct_text = ReelCorrectText.objects.filter(reel=base_reel).order_by('-id').first()
        if not base_reel_correct_text:
            print('no base text.')
            return None
        base_text_lst = [base_reel_correct_text.head]
        base_text_lst.append(sutra_to_body[base_reel.sutra_id])
        base_text_lst.append(base_reel_correct_text.tail)
        base_text = OCRCompare.get_base_text(base_text_lst, ocr_text)
        correctsegs = OCRCompare.generate_correct_diff(base_text, ocr_text)
        correctsegs_lst.append(correctsegs)

    task_id_lst = []
    for task_no in range(1, correct_times + 1):
        task = Task(batchtask=batchtask, reel=reel, typ=Task.TYPE_CORRECT, task_no=task_no, status=Task.STATUS_NOT_READY,
        publisher=batchtask.publisher)
        task.save()
        index = (task_no - 1) % len(correctsegs_lst)
        correctsegs = correctsegs_lst[index]
        for correctseg in correctsegs:
            correctseg.task = task
            correctseg.id = None
        CorrectSeg.objects.bulk_create(correctsegs)
        task_id_lst.append(task.id)
    Task.objects.filter(id__in=task_id_lst).update(status=Task.STATUS_READY) # 实际修改任务状态

    if correct_verify_times:
        task = Task(batchtask=batchtask, reel=reel, typ=Task.TYPE_CORRECT_VERIFY, task_no=0, status=Task.STATUS_NOT_READY,
        publisher=batchtask.publisher)
        task.save()

def create_judge_tasks(batchtask, lqreel, base_reel, judge_times, judge_verify_times):
    if judge_times == 0:
        return
    for task_no in range(1, judge_times + 1):
        task = Task(batchtask=batchtask, typ=Task.TYPE_JUDGE, lqreel=lqreel,
        base_reel=base_reel, task_no=task_no, status=Task.STATUS_NOT_READY,
        publisher=batchtask.publisher)
        task.save()
    # 校勘判取审定任务只有一次
    if judge_verify_times:
        task = Task(batchtask=batchtask, typ=Task.TYPE_JUDGE_VERIFY, lqreel=lqreel,
        base_reel=base_reel, task_no=0, status=Task.STATUS_NOT_READY,
        publisher=batchtask.publisher)
        task.save()

def create_punct_tasks(batchtask, reel, punct_times, punct_verify_times):
    if punct_times == 0:
        return
    reelcorrecttext = None
    status = Task.STATUS_NOT_READY

    task_puncts = '[]'
    reelcorrecttext = ReelCorrectText.objects.filter(reel=reel).order_by('-id').first()
    if reelcorrecttext:
        status = Task.STATUS_READY
        punct = Punct.objects.filter(reeltext=reelcorrecttext).order_by('-id').first()
        if punct:
            task_puncts = punct.punctuation
    for task_no in range(1, punct_times + 1):
        task = Task(batchtask=batchtask, typ=Task.TYPE_PUNCT, reel=reel,
        reeltext=reelcorrecttext, result=task_puncts, task_no=task_no,
        status=status, publisher=batchtask.publisher)
        task.save()

    # 标点审定任务只有一次
    if punct_verify_times:
        task = Task(batchtask=batchtask, typ=Task.TYPE_PUNCT_VERIFY, reel=reel,
        reeltext=reelcorrecttext, result='[]', task_no=task_no,
        status=Task.STATUS_NOT_READY, publisher=batchtask.publisher)
        task.save()

def create_lqpunct_tasks(batchtask, lqreel, lqpunct_times, lqpunct_verify_times):
    if lqpunct_times == 0:
        return
    for task_no in range(1, lqpunct_times + 1):
        task = Task(batchtask=batchtask, typ=Task.TYPE_LQPUNCT, lqreel=lqreel,
        task_no=task_no, status=Task.STATUS_NOT_READY,
        publisher=batchtask.publisher)
        task.save()
    # 审定任务只有一次
    if lqpunct_verify_times:
        task = Task(batchtask=batchtask, typ=Task.TYPE_LQPUNCT_VERIFY, lqreel=lqreel,
        task_no=0, status=Task.STATUS_NOT_READY,
        publisher=batchtask.publisher)
        task.save()

def get_sutra_body(sutra):
    body_lst = []
    for reel in Reel.objects.filter(sutra=sutra).order_by('reel_no'):
        reel_correct_text = ReelCorrectText.objects.filter(reel=reel).order_by('-id').first()
        if reel_correct_text:
            body_lst.append(clean_jiazhu(reel_correct_text.body))
    return '\n\n'.join(body_lst)

# 从龙泉大藏经来发布
def create_tasks_for_batchtask(batchtask, reel_lst,
correct_times = 2, correct_verify_times = 0,
judge_times = 2, judge_verify_times = 0,
punct_times = 2, punct_verify_times = 0,
lqpunct_times = 0, lqpunct_verify_times = 0,
mark_times = 0, mark_verify_times = 0,
lqmark_times = 0, lqmark_verify_times = 0):
    '''
    reel_lst格式： [(lqsutra, reel_no), (lqsutra, reel_no)]
    '''
    sutra_to_body = {}
    for lqsutra, reel_no in reel_lst:
        # 创建文字校对任务
        origin_sutra_lst = list(lqsutra.sutra_set.all())
        # 将未准备好数据的藏经版本过滤掉
        sutra_lst = []
        for sutra in origin_sutra_lst:
            if sutra.tripitaka.cut_ready or sutra.sid.startswith('CB'):
                sutra_lst.append(sutra)

        # 先得到两个base_reel，CBETA和高丽藏
        base_sutra_lst = []
        for sutra in sutra_lst:
            if sutra.sid.startswith('CB') or sutra.sid.startswith('GL'):
                base_sutra_lst.append(sutra)
                if sutra.id not in sutra_to_body:
                    sutra_to_body[sutra.id] = get_sutra_body(sutra)
        if not base_sutra_lst:
            # 记录错误
            print('no base sutra')
            continue
        if not base_sutra_lst[0].sid.startswith('CB'):
            base_sutra_lst[0], base_sutra_lst[1] = base_sutra_lst[1], base_sutra_lst[0]
        base_reel_lst = []
        for sutra in base_sutra_lst:
            try:
                reel = Reel.objects.get(sutra=sutra, reel_no=reel_no)
                base_reel_lst.append(reel)
            except:
                pass

        for sutra in sutra_lst:
            try:
                reel = Reel.objects.get(sutra=sutra, reel_no=reel_no)
            except:
                # TODO: 记录错误
                continue
            if reel.ocr_ready:
                create_correct_tasks(batchtask, reel, base_reel_lst, sutra_to_body, correct_times, correct_verify_times)
                create_punct_tasks(batchtask, reel, punct_times, punct_verify_times)

        try:
            lqreel = LQReel.objects.get(lqsutra=lqsutra, reel_no=reel_no)
            base_reel = base_reel_lst[0]
            create_judge_tasks(batchtask, lqreel, base_reel, judge_times, judge_verify_times)
        except:
            print('create judge task failed: ', lqsutra, reel_no)
        if lqreel:
            create_lqpunct_tasks(batchtask, lqreel, lqpunct_times, lqpunct_verify_times)

def publish_correct_result(task):
    '''
    发布文字校对的结果，供校勘判取使用
    '''
    print('publish_correct_result')
    sutra = task.reel.sutra
    reel_no = task.reel.reel_no
    reel_correct_text = None
    text_changed = False
    saved_reel_correct_texts = list(ReelCorrectText.objects.filter(reel=task.reel).order_by('-id')[0:1])
    if len(saved_reel_correct_texts) == 0:
        with transaction.atomic():
            reeltext_count = ReelCorrectText.objects.filter(task_id=task.id).count()
            if reeltext_count == 0:
                reel_correct_text = ReelCorrectText(reel=task.reel, task=task, publisher=task.picker)
                reel_correct_text.set_text(task.result)
                reel_correct_text.save()
                task.reel.set_correct_ready()
    else: # 与最新的一份记录比较
        old_text = saved_reel_correct_texts[0].text
        new_text = task.result
        if old_text != new_text:
            with transaction.atomic():
                reeltext_count = ReelCorrectText.objects.filter(task_id=task.id).count()
                if reeltext_count == 0:
                    reel_correct_text = ReelCorrectText(reel=task.reel, task=task, publisher=task.picker)
                    reel_correct_text.set_text(task.result)
                    reel_correct_text.save()
                    task.reel.set_correct_ready()
                    text_changed = True
        else:
            return

    task_puncts = '[]'
    reel = task.reel
    if reel_correct_text:
        # 如果与前一卷有重叠，且前一卷未完成，不生成精确切分。
        generate_cut = True
        if reel.reel_no > 1:
            try:
                prev_reel = Reel.objects.get(sutra=reel.sutra, reel_no=reel.reel_no-1)
                if Reel.is_overlapping(prev_reel, reel):
                    if prev_reel.correct_ready:
                        prev_correct_text = ReelCorrectText.objects.filter(reel=prev_reel).order_by('-id').first()
                        last_page = prev_correct_text.text.split('\np\n')[-1]
                        line_count = 0
                        for line in last_page.split('\n'):
                            if line:
                                line_count += 1
                        if line_count:
                            new_text = reel_correct_text.text[:2] + '\n' * line_count + reel_correct_text.text[2:]
                            reel_correct_text.set_text(new_text)
                            reel_correct_text.save()
                    else:
                        generate_cut = False
            except:
                pass
        if generate_cut:
            # 得到精确的切分数据
            try:
                compute_accurate_cut(reel)
            except Exception:
                traceback.print_exc()

        # 如果与下一卷有重叠，且下一卷已完成，生成下一卷的精确切分。
        if reel.reel_no < reel.sutra.total_reels:
            try:
                next_reel = Reel.objects.get(sutra=reel.sutra, reel_no=reel.reel_no+1)
                if Reel.is_overlapping(reel, next_reel) and next_reel.correct_ready:
                    next_correct_text = ReelCorrectText.objects.filter(reel=next_reel).order_by('-id').first()
                    last_page = reel_correct_text.text.split('\np\n')[-1]
                    line_count = 0
                    for line in last_page.split('\n'):
                        if line:
                            line_count += 1
                    if line_count:
                        new_text = next_correct_text.text[:2] + '\n' * line_count + next_correct_text.text[2:]
                        next_correct_text.set_text(new_text)
                        next_correct_text.save()

                    # 得到精确的切分数据
                    try:
                        compute_accurate_cut(next_reel)
                    except Exception:
                        traceback.print_exc()
            except:
                pass

        task_puncts = PunctProcess.create_new_for_correcttext(task.reel, reel_correct_text)
        punct = Punct(reel=task.reel, reeltext=reel_correct_text, punctuation=task_puncts)
        punct.save()

        # 基础标点任务
        # 检查是否有未就绪的基础标点任务，如果有，状态设为READY
        Task.objects.filter(reel=task.reel, typ=Task.TYPE_PUNCT, status=Task.STATUS_NOT_READY)\
        .update(reeltext=reel_correct_text, result=task_puncts, status=Task.STATUS_READY)
        # 基础标点审定任务
        Task.objects.filter(reel=task.reel, typ=Task.TYPE_PUNCT_VERIFY, status=Task.STATUS_NOT_READY).update(reeltext=reel_correct_text)

    # 针对龙泉藏经这一卷查找是否有未就绪的校勘判取任务
    lqsutra = sutra.lqsutra
    batchtask = task.batchtask
    if not lqsutra:
        print('没有关联的龙泉藏经')
        logging.error('没有关联的龙泉藏经')
        return None
    judge_tasks = list(Task.objects.filter(batchtask=batchtask, lqreel__lqsutra=lqsutra, typ=Task.TYPE_JUDGE))
    if len(judge_tasks) == 0:
        print('没有校勘判取任务')
        return
    base_sutra = judge_tasks[0].base_reel.sutra
    judge_task_not_ready = (judge_tasks[0].status == Task.STATUS_NOT_READY)
    if is_sutra_ready_for_judge(lqsutra):
        if judge_task_not_ready: # 第一次创建校勘判取任务的数据
            create_data_for_judge_tasks(batchtask, lqsutra, base_sutra, lqsutra.total_reels)
            return
        else: # 已经创建过校勘判取任务的数据
            if all([t.status == Task.STATUS_READY for t in judge_tasks]): # 都还没被领取
                # 尝试将校勘判取任务的状态改为STATUS_NOT_READY
                count = Task.objects.filter(batchtask=batchtask, lqreel__lqsutra=lqsutra, typ=Task.TYPE_JUDGE,
                status=Task.STATUS_READY).update(status=Task.STATUS_NOT_READY)
                if count == len(judge_tasks):
                    task_ids = [t.id for t in judge_tasks]
                    DiffSegResult.objects.filter(task_id__in=task_ids).delete()
                    ReelDiff.objects.filter(lqsutra=lqsutra).delete()
                    create_data_for_judge_tasks(batchtask, lqsutra, base_sutra, lqsutra.total_reels)
                    return
                else: # 在上面代码运行时间内，有校勘判取任务被领取
                    Task.objects.filter(batchtask=task.batchtask, lqreel__lqsutra=lqsutra, typ=Task.TYPE_JUDGE,
                    status=Task.STATUS_NOT_READY).update(status=Task.STATUS_READY)
            # 已有校勘判取任务被领取，需要复制已有的判取结果
            if text_changed:
                create_new_data_for_judge_tasks(batchtask, lqsutra, base_sutra, lqsutra.total_reels)

CORRECT_RESULT_FILTER = re.compile('[ 　ac-oq-zA-Z0-9.?\-",/，。、：]')
MULTI_LINEFEED = re.compile('\n\n+')
def generate_correct_result(task):
    text_lst = []
    last_ch_linefeed = False
    last_not_empty_correctseg = None
    for correctseg in CorrectSeg.objects.filter(task=task).order_by('id'):
        selected_text = CORRECT_RESULT_FILTER.sub('', correctseg.selected_text)
        selected_text = MULTI_LINEFEED.sub('\n', selected_text)
        if last_ch_linefeed:
            selected_text = selected_text.lstrip('\n')
        if len(selected_text) != len(correctseg.selected_text):
            correctseg.selected_text = selected_text
            correctseg.save(update_fields=['selected_text'])
        if selected_text:
            last_not_empty_correctseg = correctseg
            last_ch_linefeed = (selected_text[-1] == '\n')
            text_lst.append(selected_text)
    # 将最后一个换行符删除
    if last_not_empty_correctseg and last_not_empty_correctseg.selected_text.endswith('\n'):
        last_not_empty_correctseg.selected_text = last_not_empty_correctseg.selected_text.rstrip('\n')
        last_not_empty_correctseg.save(update_fields=['selected_text'])
        text_lst[-1] = last_not_empty_correctseg.selected_text
    result = ''.join(text_lst)
    task.result = result
    task.save(update_fields=['result'])

def correct_submit(task):
    '''
    文字校对提交结果
    '''
    print('correct_submit')
    generate_correct_result(task)
    # 检查一组的几个文字校对任务是否都已完成
    correct_tasks = Task.objects.filter(reel=task.reel, batchtask=task.batchtask, typ=Task.TYPE_CORRECT).order_by('task_no')
    all_finished = all([correct_task.status == Task.STATUS_FINISHED for correct_task in correct_tasks])
    task_count = len(correct_tasks)
    # 如果都已完成
    if all_finished:
        if task_count == 1:
            # 系统暂不支持单一校对，如果只有一个校对任务，不进行后续的任务任务。
            pass
            # publish_correct_result(task)
        elif task_count == 2:
            # 查到文字校对审定任务
            correct_verify_task = Task.objects.filter(reel=task.reel, batchtask=task.batchtask, typ=Task.TYPE_CORRECT_VERIFY).first()
            if correct_verify_task is None:
                return 
            if correct_verify_task.status > Task.STATUS_READY:
                # 已被领取的任务，不再重新发布
                return
            # 比较一组的两个字校对任务的结果
            CorrectSeg.objects.filter(task=correct_verify_task).delete()
            correctsegs = OCRCompare.generate_correct_diff(correct_tasks[0].result, correct_tasks[1].result)
            from_correctsegs = list(CorrectSeg.objects.filter(task=correct_tasks[1]).order_by('id'))
            OCRCompare.reset_segposition(from_correctsegs)
            OCRCompare.set_position(from_correctsegs, correctsegs)
            for correctseg in correctsegs:
                correctseg.task = correct_verify_task
                correctseg.id = None
            CorrectSeg.objects.bulk_create(correctsegs)

            # 文字校对审定任务设为待领取
            correct_verify_task.status = Task.STATUS_READY
            task_ids = correct_tasks.values_list('id', flat=True)

            DoubtSeg.objects.filter(task=correct_verify_task).delete()
            new_doubt_segs = OCRCompare.combine_correct_doubtseg(correct_tasks[0].doubt_segs.all(), correct_tasks[1].doubt_segs.all())        
            for doubt_seg in new_doubt_segs:
                doubt_seg.task = correct_verify_task
                doubt_seg.id = None
            DoubtSeg.objects.bulk_create(new_doubt_segs)
            correct_verify_task.save(update_fields=['status'])

def correct_verify_submit(task):
    generate_correct_result(task)
    publish_correct_result(task)

def judge_submit_result(task):
    '''
    校勘判取提交结果
    '''
    print('judge_submit_result')
    lqreel = task.lqreel
    judge_tasks = list(Task.objects.filter(batchtask_id=task.batchtask_id, lqreel_id=lqreel.id, typ=Task.TYPE_JUDGE).all())
    task_count = len(judge_tasks)
    if task_count == 0:
        return None
    all_finished = True
    for judge_task in judge_tasks:
        if judge_task.status != Task.STATUS_FINISHED:
            all_finished = False
    if not all_finished:
        return None

    judge_verify_tasks = list(Task.objects.filter(batchtask_id=task.batchtask_id,
    lqreel_id=lqreel.id, typ=Task.TYPE_JUDGE_VERIFY, status=Task.STATUS_NOT_READY).all())
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
        diffsegresults = list(DiffSegResult.objects.filter(task_id=judge_tasks[i].id).order_by('diffseg__base_pos').all())
        diffsegresults_lst.append(diffsegresults)

    to_save_diffsegresults = []
    diffseg_count = len(diffsegresults_lst[0])
    for i in range(diffseg_count):
        all_equal = True
        for j in range(task_count-1):
            diffsegresult1 = diffsegresults_lst[j][i]
            diffsegresult2 = diffsegresults_lst[j+1][i]
            if not diffsegresult1.is_equal(diffsegresult2):
                all_equal = False
                break
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
    if task.status != Task.STATUS_FINISHED:
        print('task status is not finished.')
        return
    lqreeltext_count = LQReelText.objects.filter(task_id=task.id).count()
    if lqreeltext_count != 0:
        print('this task already published.')
        return
    base_correct_text = task.reeldiff.base_text
    base_text = clean_separators(base_correct_text.body)
    text_lst = []
    base_index = 0
    base_text_length = len(base_text)
    diffsegresults = list(DiffSegResult.objects.filter(task_id=task.id).order_by('id'))
    for diffsegresult in diffsegresults:
        if not diffsegresult.selected:
            print('not selected')
            return
        base_pos = diffsegresult.diffseg.base_pos
        base_length = diffsegresult.diffseg.base_length
        if base_index < base_pos:
            text_lst.append( base_text[base_index: base_pos] )
            base_index = base_pos
        if base_index != base_pos:
            print('error')
            return
        text_lst.append(diffsegresult.selected_text)
        base_index += base_length
    if base_index < base_text_length:
        text_lst.append( base_text[base_index: base_text_length] )
    else:
        print('error')
        return
    with transaction.atomic():
        lqreeltext_count = LQReelText.objects.filter(task_id=task.id).count()
        if lqreeltext_count == 0:
            body = ''.join(text_lst)
            reeltext = LQReelText(lqreel=task.lqreel, text=body, body=body, task=task, publisher=task.picker)
            reeltext.save()

            sutra_cb = Sutra.objects.get(lqsutra=task.lqreel.lqsutra, tripitaka=Tripitaka.objects.get(code='CB'))
            reel_cb = Reel.objects.get(sutra=sutra_cb, reel_no=task.lqreel.reel_no)
            punct = Punct.objects.filter(reel=reel_cb).first()
            base_reel_text = clean_separators(punct.reeltext.text)
            _puncts = PunctProcess().new_puncts(base_reel_text, json.loads(punct.punctuation), reeltext.text)
            task_puncts = json.dumps(_puncts, separators=(',', ':'))

            punct = LQPunct(lqreel=task.lqreel, reeltext=reeltext, punctuation=task_puncts)
            punct.save()

            # 检查是否有未就绪的定本标点任务，如果有，状态设为READY
            Task.objects.filter(lqreel=task.lqreel, typ=Task.TYPE_LQPUNCT, status=Task.STATUS_NOT_READY)\
            .update(lqtext=reeltext, result=task_puncts, status=Task.STATUS_READY)
            Task.objects.filter(lqreel=task.lqreel, typ=Task.TYPE_LQPUNCT_VERIFY, status=Task.STATUS_NOT_READY)\
            .update(lqtext=reeltext)

def punct_submit_result(task):
    print('punct_submit_result')
    verify_tasks = list(Task.objects.filter(batchtask=task.batchtask, typ=Task.TYPE_PUNCT_VERIFY, reel=task.reel))
    if len(verify_tasks) == 0:
        publish_punct_result(task)
        return
    verify_task = verify_tasks[0]
    punct_tasks = Task.objects.filter(batchtask=task.batchtask, typ=Task.TYPE_PUNCT, reel=task.reel)
    if all([t.status == Task.STATUS_FINISHED for t in punct_tasks]):
        verify_task.status = Task.STATUS_READY
        verify_task.result = punct_tasks[0].result
        verify_task.save(update_fields=['status', 'result'])

def publish_punct_result(task):
    print('publish_punct_result')
    count = Punct.objects.filter(task=task).count()
    if count == 0:
        punct = Punct(reel=task.reel, reeltext=task.reeltext, \
        punctuation=task.result, task=task, publisher=task.picker)
        punct.save()

def lqpunct_submit_result(task):
    print('lqpunct_submit_result')
    verify_tasks = list(Task.objects.filter(batchtask=task.batchtask, typ=Task.TYPE_LQPUNCT_VERIFY, lqreel=task.lqreel))
    if len(verify_tasks) == 0:
        publish_lqpunct_result(task)
        return
    verify_task = verify_tasks[0]
    punct_tasks = Task.objects.filter(batchtask=task.batchtask, typ=Task.TYPE_LQPUNCT, lqreel=task.lqreel)
    if all([t.status == Task.STATUS_FINISHED for t in punct_tasks]):
        verify_task.status = Task.STATUS_READY
        verify_task.result = punct_tasks[0].result
        verify_task.save(update_fields=['status', 'result'])

def publish_lqpunct_result(task):
    print('publish_lqpunct_result')
    count = LQPunct.objects.filter(task=task).count()
    if count == 0:
        punct = LQPunct(lqreel=task.lqreel, reeltext=task.lqtext, \
        punctuation=task.result, task=task, publisher=task.picker)
        punct.save()

@background(schedule=0)
def correct_submit_async(task_id):
    task = Task.objects.get(pk=task_id)
    correct_submit(task)

@background(schedule=0)
def correct_verify_submit_async(task_id):
    task = Task.objects.get(pk=task_id)
    correct_verify_submit(task)

@background(schedule=0)
def publish_correct_result_async(task_id):
    task = Task.objects.get(pk=task_id)
    publish_correct_result(task)

@background(schedule=0)
def judge_submit_result_async(task_id):
    task = Task.objects.get(pk=task_id)
    judge_submit_result(task)

@background(schedule=0)
def publish_judge_result_async(task_id):
    task = Task.objects.get(pk=task_id)
    publish_judge_result(task)

@background(schedule=0)
def punct_submit_result_async(task_id):
    task = Task.objects.get(pk=task_id)
    punct_submit_result(task)

@background(schedule=0)
def publish_punct_result_async(task_id):
    task = Task.objects.get(pk=task_id)
    publish_punct_result(task)

@background(schedule=0)
def lqpunct_submit_result_async(task_id):
    task = Task.objects.get(pk=task_id)
    lqpunct_submit_result(task)

@background(schedule=0)
def publish_lqpunct_result_async(task_id):
    task = Task.objects.get(pk=task_id)
    publish_lqpunct_result(task)