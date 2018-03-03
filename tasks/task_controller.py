from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.db.models import Q

from tdata.models import *
from tasks.models import *
from tasks.common import SEPARATORS_PATTERN, judge_merge_text_punct, ReelText, \
clean_separators, compute_accurate_cut
from tasks.reeldiff_processor import generate_reeldiff
from tasks.ocr_compare import OCRCompare
from tasks.utils.punct_process import PunctProcess
import json, re, logging, traceback
from operator import attrgetter, itemgetter
from difflib import SequenceMatcher
from background_task import background

logger = logging.getLogger(__name__)

def get_reeltext(lqsutra, tripitaka_id, reel_no):
    sutra = Sutra.objects.get(lqsutra=lqsutra, tripitaka_id=tripitaka_id)
    reel = Reel.objects.get(sutra=sutra, reel_no=reel_no)
    reel_correct_texts = list(ReelCorrectText.objects.filter(reel=reel).order_by('-id')[0:1])
    if not reel_correct_texts:
        return None
    reel_correct_text = reel_correct_texts[0]
    reeltext = ReelText(reel=reel, text=reel_correct_text.text, tripitaka_id=tripitaka_id,
    sid=sutra.sid, vol_no=reel.start_vol, start_vol_page=reel.start_vol_page)
    return reeltext

def create_correct_tasks(batchtask, reel, base_reel_lst, sutra_to_body, correct_times, correct_verify_times):
    if reel.sutra.sid.startswith('CB'): # 不对CBETA生成任务
        return
    # Correct Task
    print('create_correct_tasks: ', reel)
    reel_ocr_texts = list(ReelOCRText.objects.filter(reel=reel))
    if len(reel_ocr_texts) == 0:
        print('no ocr text for reel: ', reel)
        return None
    reel_ocr_text = reel_ocr_texts[0]

    for base_reel in base_reel_lst:
        try:
            base_reel_correct_text = ReelCorrectText.objects.filter(reel=base_reel).order_by('-id').first()
        except:
            print('no base text.')
            return None
        base_text_lst = [base_reel_correct_text.head]
        base_text_lst.append(sutra_to_body[base_reel.sutra_id])
        base_text_lst.append(base_reel_correct_text.tail)
        base_text = ''.join(base_text_lst)
        ocr_text = OCRCompare.preprocess_ocr_text(reel_ocr_text.text)
        correctsegs = OCRCompare.generate_compare_reel(base_text, ocr_text)

    task_id_lst = []
    for task_no in range(1, correct_times + 1):
        task = Task(batch_task=batchtask, reel=reel, typ=Task.TYPE_CORRECT, task_no=task_no, status=Task.STATUS_NOT_READY,
        publisher=batchtask.publisher)
        task.save()

        for correctseg in correctsegs:
            correctseg.task = task
            correctseg.id = None
        CorrectSeg.objects.bulk_create(correctsegs)
        task_id_lst.append(task.id)
    Task.objects.filter(id__in=task_id_lst).update(status=Task.STATUS_READY) # 实际修改任务状态

    if correct_verify_times:
        task = Task(batch_task=batchtask, reel=reel, typ=Task.TYPE_CORRECT_VERIFY, task_no=0, status=Task.STATUS_NOT_READY,
        publisher=batchtask.publisher)
        task.save()

def create_judge_tasks(batchtask, lqreel, base_reel, judge_times, judge_verify_times):
    for task_no in range(1, judge_times + 1):
        task = Task(batch_task=batchtask, typ=Task.TYPE_JUDGE, lqreel=lqreel,
        base_reel=base_reel, task_no=task_no, status=Task.STATUS_NOT_READY,
        publisher=batchtask.publisher)
        task.save()
    # 校勘判取审定任务只有一次
    if judge_verify_times:
        task = Task(batch_task=batchtask, typ=Task.TYPE_JUDGE_VERIFY, lqreel=lqreel,
        base_reel=base_reel, task_no=0, status=Task.STATUS_NOT_READY,
        publisher=batchtask.publisher)
        task.save()

def create_punct_tasks(batchtask, reel, punct_times, punct_verify_times):
    reelcorrecttext = None
    punctuation_json = '[]'
    status = Task.STATUS_NOT_READY
    try:
        reelcorrecttext = ReelCorrectText.objects.filter(reel=reel).order_by('-id')[0]
        if reelcorrecttext:
            status = Task.STATUS_READY
    except:
        pass

    # 标点以CBETA的结果为起点
    task_puncts = '[]'
    try:
        CB = Tripitaka.objects.get(code='CB')
        sutra_cb = Sutra.objects.get(lqsutra=reel.sutra.lqsutra, tripitaka=CB)
        reel_cb = Reel.objects.get(sutra=sutra_cb, reel_no=reel.reel_no)
        punct = Punct.objects.filter(reel=reel_cb)[0]
        task_puncts = PunctProcess.create_new(reel, reelcorrecttext.text)
    except:
        pass
    for task_no in range(1, punct_times + 1):
        task = Task(batch_task=batchtask, typ=Task.TYPE_PUNCT, reel=reel,
        reeltext=reelcorrecttext, result=task_puncts, task_no=task_no,
        status=status, publisher=batchtask.publisher)
        task.save()

    # 标点审定任务只有一次
    if punct_verify_times:
        task = Task(batch_task=batchtask, typ=Task.TYPE_PUNCT_VERIFY, reel=reel,
        reeltext=reelcorrecttext, result='[]', task_no=task_no,
        status=Task.STATUS_NOT_READY, publisher=batchtask.publisher)
        task.save()

def get_sutra_body(sutra):
    body_lst = []
    for reel in Reel.objects.filter(sutra=sutra).order_by('reel_no'):
        reel_correct_text = ReelCorrectText.objects.filter(reel=reel).order_by('-id').first()
        body_lst.append(reel_correct_text.body)
    return '\n\n'.join(body_lst)

# 从龙泉大藏经来发布
def create_tasks_for_batchtask(batchtask, reel_lst,
correct_times = 0, correct_verify_times = 0,
judge_times = 0, judge_verify_times = 0,
punct_times = 0, punct_verify_times = 0,
lqpunct_times = 0, lqpunct_verify_times = 0,
mark_times = 0, mark_verify_times = 0,
lqmark_times = 0, lqmark_verify_times = 0):
    '''
    reel_lst格式： [(lqsutra, reel_no), (lqsutra, reel_no)]
    '''
    # 文字校对任务数最多只2个
    if correct_times > 2:
        correct_times = 2

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
        first_base_sutra = None
        second_base_sutra = None
        for sutra in sutra_lst:
            if sutra.sid.startswith('CB'):
                first_base_sutra = sutra
                if sutra.id not in sutra_to_body:
                    sutra_to_body[sutra.id] = get_sutra_body(sutra)
            # # 暂时不使用高丽藏作为比对本
            # if sutra.sid.startswith('GL'):
            #     second_base_sutra = sutra
        if not first_base_sutra and not second_base_sutra:
            # 记录错误
            print('no base sutra')
            continue
        base_reel_lst = []
        if first_base_sutra:
            reel = Reel.objects.get(sutra=first_base_sutra, reel_no=reel_no)
            base_reel_lst.append(reel)
        if second_base_sutra:
            reel = Reel.objects.get(sutra=second_base_sutra, reel_no=reel_no)
            base_reel_lst.append(reel)

        for sutra in sutra_lst:
            try:
                reel = Reel.objects.get(sutra=sutra, reel_no=reel_no)
            except:
                # TODO: 记录错误
                continue
            create_correct_tasks(batchtask, reel, base_reel_lst, sutra_to_body, correct_times, correct_verify_times)
            create_punct_tasks(batchtask, reel, punct_times, punct_verify_times)

        try:
            lqreel = LQReel.objects.get(lqsutra=lqsutra, reel_no=reel_no)
            base_reel = base_reel_lst[0]
            create_judge_tasks(batchtask, lqreel, base_reel, judge_times, judge_verify_times)
        except:
            print('create judge task failed: ', lqsutra, reel_no)

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
        print('reel_id_to_text', reel_lst)
        logging.info('此卷的文字校对还未完成，暂时不触发校勘判取任务')
        return None
    correct_text_lst = []
    reel_correct_text_lst = []
    for reel in reel_lst:
        correct_text_lst.append( reel_id_to_text[reel.id] )
        reel_correct_text_lst.append( reel_id_to_reel_correct_text[reel.id] )
    reeldiff = ReelDiff(lqsutra=lqsutra, reel_no=reel_no, base_text=reel_correct_text_lst[0])
    reeldiff.save()
    reeldiff.correct_texts.set(reel_correct_text_lst)

    generate_reeldiff(reeldiff, new_sutra_lst, reel_lst, correct_text_lst)
    for task in judge_task_lst:
        for diffseg in reeldiff.diffseg_set.all():
            diffsegresult = DiffSegResult(task=task, diffseg=diffseg, selected_text='')
            diffsegresult.save()

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
                reel_correct_text = ReelCorrectText(reel=task.reel, text=task.result, task=task, publisher=task.picker)
                reel_correct_text.save()
    else: # 与最新的一份记录比较
        text1 = saved_reel_correct_texts[0].text
        text2 = task.result
        if text1 != text2:
            with transaction.atomic():
                reeltext_count = ReelCorrectText.objects.filter(task_id=task.id).count()
                if reeltext_count == 0:
                    reel_correct_text = ReelCorrectText(reel=task.reel, text=task.result, task=task, publisher=task.picker)
                    reel_correct_text.save()
                    text_changed = True
        else:
            return

    task_puncts = '[]'
    if reel_correct_text:
        # 得到精确的切分数据
        try:
            compute_accurate_cut(task.reel)
        except Exception:
            traceback.print_exc()

        text = SEPARATORS_PATTERN.sub('', reel_correct_text.text)
        task_puncts = PunctProcess.create_new(task.reel, text)
        punct = Punct(reel=task.reel, reeltext=reel_correct_text, punctuation=task_puncts)
        punct.save()

        # 基础标点任务
        # 检查是否有未就绪的基础标点任务，如果有，状态设为READY
        punct_tasks = list(Task.objects.filter(reel=task.reel, typ=Task.TYPE_PUNCT, status=Task.STATUS_NOT_READY))
        if len(punct_tasks) > 0:
            punct_task_ids = [task.id for task in punct_tasks]
            Task.objects.filter(id__in=punct_task_ids).update(reeltext=reel_correct_text, result=task_puncts, status=Task.STATUS_READY)

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

CORRECT_RESULT_FILTER = re.compile('[ 　ac-oq-zA-Z0-9.?\-",/，。、：]')
def generate_correct_result(task):
    text_lst = []
    for correctseg in CorrectSeg.objects.filter(task=task).order_by('id'):
        text_lst.append(correctseg.selected_text)
    result = ''.join(text_lst)
    # result = CORRECT_RESULT_FILTER.sub('', result)
    # 清除空行
    # text_lst = result.replace('p', '\np\n').replace('b', '\nb\n').split('\n')
    # new_text_lst = [text for text in text_lst if text != '']
    # task.result = '\n'.join(new_text_lst)
    task.result = result
    task.save(update_fields=['result'])

def correct_submit(task):
    '''
    文字校对提交结果
    '''
    generate_correct_result(task)
    # 检查一组的几个文字校对任务是否都已完成
    correct_tasks = Task.objects.filter(reel=task.reel, batch_task=task.batch_task, typ=Task.TYPE_CORRECT).order_by('task_no')
    all_finished = True
    for correct_task in correct_tasks:
        if correct_task.status != Task.STATUS_FINISHED:
            all_finished = False
    task_count = len(correct_tasks)
    # 如果都已完成
    if all_finished:
        if task_count == 1:
            publish_correct_result(task)
        elif task_count == 2:
            # 查到文字校对审定任务
            correct_verify_tasks = list(Task.objects.filter(reel=task.reel, batch_task=task.batch_task, typ=Task.TYPE_CORRECT_VERIFY))
            if len(correct_verify_tasks) == 0:
                return 
            correct_verify_task = correct_verify_tasks[0]

            # 比较一组的两个文字校对任务的结果
            correctsegs = OCRCompare.generate_compare_reel(correct_tasks[0].result, correct_tasks[1].result)
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

    judge_verify_tasks = list(Task.objects.filter(batch_task_id=task.batch_task_id,
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
        diffsegresults = list(DiffSegResult.objects.filter(task_id=judge_tasks[i].id).order_by('diffseg__diffseg_no').all())
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
        return
    lqreeltext_count = LQReelText.objects.filter(task_id=task.id).count()
    if lqreeltext_count != 0:
        return
    base_correct_text = task.reeldiff.base_text
    base_text = clean_separators(base_correct_text.text)
    base_tripitaka_id = base_correct_text.reel.sutra.tripitaka_id
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
            lqreeltext = LQReelText(lqreel=task.lqreel, text=''.join(text_lst), task=task, publisher=task.picker)
            lqreeltext.save()

            sutra_cb = Sutra.objects.get(lqsutra=task.lqreel.lqsutra, tripitaka=Tripitaka.objects.get(code='CB'))
            reel_cb = Reel.objects.get(sutra=sutra_cb, reel_no=task.lqreel.reel_no)
            punct = Punct.objects.filter(reel=reel_cb).first()
            _puncts = PunctProcess().new_puncts(punct.reeltext.text, json.loads(punct.punctuation), lqreeltext.text)
            task_puncts = json.dumps(_puncts, separators=(',', ':'))

            punct = LQPunct(lqreel=task.lqreel, lqreeltext=lqreeltext, punctuation=task_puncts)
            punct.save()

            # 检查是否有未就绪的定本标点任务，如果有，状态设为READY
            Task.objects.filter(lqreel=task.lqreel, typ=Task.TYPE_LQPUNCT, status=Task.STATUS_NOT_READY)\
            .update(lqtext=lqreeltext, result=task_puncts, status=Task.STATUS_READY)

def punct_submit_result(task):
    verify_tasks = list(Task.objects.filter(batch_task=task.batchtask, typ=Task.TYPE_PUNCT_VERIFY, reel=task.reel))
    if len(verify_tasks) == 0:
        publish_punct_result(task)
        return
    verify_task = verify_tasks[0]
    punct_tasks = Task.objects.filter(batch_task=task.batchtask, typ=Task.TYPE_PUNCT, reel=task.reel)
    if all([t.status == Task.STATUS_FINISHED for t in punct_tasks]):
        verify_task.status = Task.STATUS_READY
        verify_task.result = punct_tasks[0].result
        verify_task.save(update_fields=['status', 'result'])

def publish_punct_result(task):
    punct = Punct(reel=task.reel, reeltext=task.reeltext, \
    punctuation=task.result, task=task, publisher=task.picker)
    punct.save()

def lqpunct_submit_result(task):
    verify_tasks = list(Task.objects.filter(batch_task=task.batchtask, typ=Task.TYPE_LQPUNCT_VERIFY, lqreel=task.lqreel))
    if len(verify_tasks) == 0:
        publish_lqpunct_result(task)
        return
    verify_task = verify_tasks[0]
    punct_tasks = Task.objects.filter(batch_task=task.batchtask, typ=Task.TYPE_LQPUNCT, lqreel=task.lqreel)
    if all([t.status == Task.STATUS_FINISHED for t in punct_tasks]):
        verify_task.status = Task.STATUS_READY
        verify_task.result = punct_tasks[0].result
        verify_task.save(update_fields=['status', 'result'])

def publish_lqpunct_result(task):
    punct = LQPunct(reel=task.lqreel, lqreeltext=task.lqtext, \
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