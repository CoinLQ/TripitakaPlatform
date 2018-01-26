from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from sutradata.models import *
from tasks.models import *
from sutradata.common import *

import TripitakaPlatform.settings

import os, sys
from os.path import isfile, join
import traceback

from difflib import SequenceMatcher
import re, json

def generate_text_diff(reeltext_lst, reel_diff):
    n = len(reeltext_lst)
    if n <= 1:
        return []
    opcodes_lst = []
    start_pos = 0
    junk_func = lambda x: x in " \t"
    i = 1
    while i < n:
        opcodes = SequenceMatcher(junk_func, reeltext_lst[0].text, reeltext_lst[i].text, False).get_opcodes()
        opcodes_lst.append(opcodes)
        i += 1

    result_lst = []
    while True:
        length_lst = []
        all_equal = True
        i = 0
        while i < n - 1:
            if len(opcodes_lst[i]) > 0:
                length = opcodes_lst[i][0][2] - opcodes_lst[i][0][1]
                length_lst.append( length )
                if opcodes_lst[i][0][0] != 'equal':
                    all_equal = False
            i += 1
        if len(length_lst) == 0:
            break

        min_length = min(length_lst)
        if all_equal:
            result_str = reeltext_lst[0].text[start_pos : start_pos + min_length]
            start_pos += min_length
            # result_lst.append(result_str)
            i = 0
            while i < n:
                reeltext_lst[i].position += min_length
                i += 1

            i = 0
            while i < n - 1:
                if len(opcodes_lst[i]) > 0:
                    tag, i1, i2, j1, j2 = opcodes_lst[i][0]
                    if tag == 'equal':
                        if (i2 - i1) == min_length:
                            opcodes_lst[i].pop(0)
                        else:
                            opcodes_lst[i][0] = (tag, i1 + min_length, i2, j1 + min_length, j2)
                i += 1
        else:
            result = {}
            text = {}
            diff_seg = DiffSeg(reel_diff=reel_diff, base_pos=start_pos)
            diff_seg.save()
            diff_seg_text_lst = []
            seg_text_index_lst = []

            s = reeltext_lst[0].text[start_pos : start_pos + min_length]
            start_pos += min_length
            text[s] = [reeltext_lst[0].tripitaka_id]
            start_cid, end_cid = reeltext_lst[0].get_cid_range(reeltext_lst[0].position, reeltext_lst[0].position + len(s))
            diff_seg_text = DiffSegText(
                diff_seg=diff_seg,
                tripitaka=reeltext_lst[0].tripitaka,
                text=s,
                position=reeltext_lst[0].position,
                start_cid=start_cid,
                end_cid=end_cid)
            diff_seg_text_lst.append(diff_seg_text)
            seg_text_index_lst.append(0)
            DiffSeg.objects.filter(id=diff_seg.id).update(
                base_pos=diff_seg_text.position,
                base_length=len(diff_seg_text.text))
            reeltext_lst[0].position += min_length

            if min_length == 0: # process all insert opcode
                i = 0
                while i < n - 1:
                    if len(opcodes_lst[i]) > 0:
                        tag, i1, i2, j1, j2 = opcodes_lst[i][0]
                        if tag == 'insert':
                            s = reeltext_lst[i+1].text[j1:j2]
                            code_lst = text.setdefault( s, [] )
                            code_lst.append( reeltext_lst[i+1].tripitaka_id )

                            start_cid, end_cid = reeltext_lst[i+1].get_cid_range(reeltext_lst[i+1].position, reeltext_lst[i+1].position + len(s))
                            diff_seg_text = DiffSegText(
                                diff_seg=diff_seg,
                                tripitaka=reeltext_lst[i+1].tripitaka,
                                text=s,
                                position=reeltext_lst[i+1].position,
                                start_cid=start_cid,
                                end_cid=end_cid)
                            diff_seg_text_lst.append(diff_seg_text)
                            seg_text_index_lst.append(i+1)
                            reeltext_lst[i+1].position += (j2 - j1)

                            opcodes_lst[i].pop(0)
                    i += 1
            else:
                i = 0
                while i < n - 1:
                    if len(opcodes_lst[i]) > 0:
                        tag, i1, i2, j1, j2 = opcodes_lst[i][0]
                        if tag == 'equal':
                            s = reeltext_lst[0].text[i1:i1+min_length]
                            code_lst = text.setdefault( reeltext_lst[0].text[i1:i1+min_length], [] )
                            code_lst.append( reeltext_lst[i+1].tripitaka_id )

                            start_cid, end_cid = reeltext_lst[i+1].get_cid_range(reeltext_lst[i+1].position, reeltext_lst[i+1].position + min_length)
                            diff_seg_text = DiffSegText(
                                diff_seg=diff_seg,
                                tripitaka=reeltext_lst[i+1].tripitaka,
                                text=s,
                                position=reeltext_lst[i+1].position,
                                start_cid=start_cid,
                                end_cid=end_cid)
                            diff_seg_text_lst.append(diff_seg_text)
                            seg_text_index_lst.append(i+1)
                            reeltext_lst[i+1].position += min_length

                            if (i2 - i1) == min_length:
                                opcodes_lst[i].pop(0)
                            else:
                                opcodes_lst[i][0] = (tag, i1+min_length, i2, j1+min_length, j2)
                        elif tag == 'delete':
                            code_lst = text.setdefault( u'', [] )
                            code_lst.append( reeltext_lst[i+1].tripitaka_id )

                            start_cid, end_cid = reeltext_lst[i+1].get_cid_range(reeltext_lst[i+1].position, reeltext_lst[i+1].position)
                            diff_seg_text = DiffSegText(
                                diff_seg=diff_seg,
                                tripitaka=reeltext_lst[i+1].tripitaka,
                                text='',
                                position=reeltext_lst[i+1].position,
                                start_cid=start_cid,
                                end_cid=end_cid)
                            diff_seg_text_lst.append(diff_seg_text)
                            seg_text_index_lst.append(i+1)

                            if (i2 - i1) == min_length:
                                opcodes_lst[i].pop(0)
                            else:
                                opcodes_lst[i][0] = (tag, i1+min_length, i2, j1, j2)
                        elif tag == 'replace':
                            add_length = min_length
                            if (i2 - i1) == min_length:
                                s = reeltext_lst[i+1].text[j1:j2]
                                add_length = j2 - j1
                                code_lst = text.setdefault( s, [])
                                code_lst.append( reeltext_lst[i+1].tripitaka_id )
                                opcodes_lst[i].pop(0)
                            else:
                                s = reeltext_lst[i+1].text[j1:j1+min_length]
                                code_lst = text.setdefault(s , [] )
                                code_lst.append( reeltext_lst[i+1].tripitaka_id )
                                opcodes_lst[i][0] = (tag, i1+min_length, i2, j1+min_length, j2)

                            start_cid, end_cid = reeltext_lst[i+1].get_cid_range(reeltext_lst[i+1].position, reeltext_lst[i+1].position + len(s))
                            diff_seg_text = DiffSegText(
                                diff_seg=diff_seg,
                                tripitaka=reeltext_lst[i+1].tripitaka,
                                text=s,
                                position=reeltext_lst[i+1].position,
                                start_cid=start_cid,
                                end_cid=end_cid)
                            diff_seg_text_lst.append(diff_seg_text)
                            seg_text_index_lst.append(i+1)
                            reeltext_lst[i+1].position += add_length
                    i += 1
            for i in range(n):
                if i not in seg_text_index_lst:
                    start_cid, end_cid = reeltext_lst[i].get_cid_range(reeltext_lst[i].position, reeltext_lst[i].position)
                    diff_seg_text = DiffSegText(
                        diff_seg=diff_seg,
                        tripitaka=reeltext_lst[i].tripitaka,
                        text='',
                        position=reeltext_lst[i].position,
                        start_cid=start_cid,
                        end_cid=end_cid)
                    diff_seg_text_lst.append(diff_seg_text)
            DiffSegText.objects.bulk_create(diff_seg_text_lst)
            result['text'] = text
            result_lst.append(result)
    return result_lst

def read_sutra_text(sid, reel_no):
    BASE_DIR = settings.BASE_DIR
    filepath = os.path.join(BASE_DIR, 'data/sutra_text/%s_%03d.txt' % (sid, reel_no))
    f = open(filepath, 'r')
    text = f.read()
    f.close()
    return text

def test_text_diff(reel_diff):
    reel_no = reel_diff.reel_no
    sutras = list(reel_diff.lqsutra.sutra_set.all())
    i = 0
    for sutra in sutras:
        if sutra.id == reel_diff.base_sutra_id:
            break
        i += 1
    if i != 0:
        sutra = sutras[i]
        sutras[i] = sutras[0]
        sutras[0] = sutra
    reel_lst = []
    for sutra in sutras:
        reel = Reel.objects.get(sutra=sutra, reel_no=reel_no)
        reel_lst.append(reel)

    reeltexts = []
    sutra_count = len(sutras)
    i = 0
    while i < sutra_count:
        reeltext = ReelText(
            reel_lst[i].correct_text,
            sutras[i].tripitaka_id,
            sutras[i].sid,
            reel_lst[i].start_vol,
            reel_lst[i].start_vol_page)
        reeltexts.append(reeltext)
        i += 1
    result_lst = generate_text_diff(reeltexts, reel_diff)
    print(json.dumps(result_lst, ensure_ascii=False))

class Command(BaseCommand):
    def handle(self, *args, **options):
        BASE_DIR = settings.BASE_DIR
        admin = User.objects.get(username='admin')

        # get LQSutra
        lqsutra = LQSutra.objects.get(sid='LQ003100') #大方廣佛華嚴經60卷

        # create Sutra
        QL = Tripitaka.objects.get(code='QL')
        try:
            huayan_ql = Sutra.objects.get(sid='QL000870')
        except:
            huayan_ql = Sutra(sid='QL000870', tripitaka=QL, code='00087', variant_code='0',
            name='大方廣佛華嚴經', lqsutra=lqsutra, total_reels=60)
            huayan_ql.save()

        # 乾隆藏第1卷的文本
        try:
            huayan_ql_1 = Reel.objects.get(sutra=huayan_ql, reel_no=1)
        except:
            huayan_ql_1 = Reel(sutra=huayan_ql, reel_no=1, start_vol=24,
            start_vol_page=2, end_vol=24, end_vol_page=17)
            filename = os.path.join(BASE_DIR, 'data/sutra_text/%s_001.txt' % huayan_ql.sid)
            with open(filename, 'r') as f:
                huayan_ql_1.text = f.read()
            filename = os.path.join(BASE_DIR, 'data/sutra_text/%s_001_fixed.txt' % huayan_ql.sid)
            with open(filename, 'r') as f:
                huayan_ql_1.correct_text = f.read()
            huayan_ql_1.save()
        # 得到精确的切分数据
        try:
            compute_accurate_cut(huayan_ql_1)
        except Exception:
            traceback.print_exc()

        # CBETA第1卷
        CB = Tripitaka.objects.get(code='CB')
        try:
            huayan_cb = Sutra.objects.get(sid='CB000800')
        except:
            huayan_cb = Sutra(sid='CB000800', tripitaka=CB, code='00080', variant_code='0',
            name='大方廣佛華嚴經', lqsutra=lqsutra, total_reels=60)
            huayan_cb.save()
        try:
            huayan_cb_1 = Reel.objects.get(sutra=huayan_cb, reel_no=1)
        except:
            huayan_cb_1 = Reel(sutra=huayan_cb, reel_no=1, start_vol=14,
            start_vol_page=31, end_vol=14, end_vol_page=37)
            filename = os.path.join(BASE_DIR, 'data/sutra_text/%s_001_punct.txt' % huayan_cb.sid)
            with open(filename, 'r') as f:
                text = f.read()
            punctuation, huayan_cb_1.text = extract_punct(text)
            huayan_cb_1.correct_text = huayan_cb_1.text
            huayan_cb_1.punctuation = json.dumps(punctuation)
            huayan_cb_1.save()

        # get LQReel
        try:
            lqreel = LQReel.objects.get(lqsutra=lqsutra, reel_no=1)
        except:
            # create LQReel
            lqreel = LQReel(lqsutra=lqsutra, reel_no=1)
            lqreel.save()

        # create BatchTask
        priority = 2
        CORRECT_TIMES = 2
        CORRECT_VERIFY_TIMES = 1
        JUDGE_TIMES = 2
        JUDGE_VERIFY_TIMES = 1
        reel_no = 1
        batch_task = BatchTask.objects.all()[0]

        huayan_gl = Sutra.objects.get(sid='GL000800')
        huayan_gl_1 = Reel.objects.get(sutra=huayan_gl, reel_no=1)

        ### 文字校对
        # huayan_gl = Sutra.objects.get(sid='GL000800')
        # huayan_gl_1 = Reel.objects.get(sutra=huayan_gl, reel_no=1)
        # CompareReel.objects.filter(reel=huayan_ql_1, base_reel=huayan_gl_1).delete()
        # compare_reel = CompareReel(reel=huayan_ql_1, base_reel=huayan_gl_1)
        # compare_reel.save()

        # separators = extract_page_line_separators(huayan_ql_1.text)
        # separators_json = json.dumps(separators, separators=(',', ':'))
        # Task.objects.filter(id=4, batch_task=batch_task, typ=Task.TYPE_CORRECT, base_reel=huayan_gl_1).delete()
        # task1 = Task(id=4, batch_task=batch_task, typ=Task.TYPE_CORRECT, base_reel=huayan_gl_1, task_no=1, status=Task.STATUS_READY,
        # publisher=admin)
        # task1.compare_reel = compare_reel
        # task1.separators = separators_json
        # task1.reel = huayan_ql_1
        # task1.save()
        
        # diff_lst = CompareReel.generate_compare_reel(compare_reel.base_reel.text, huayan_ql_1.text)
        # #compare_segs = []
        # for tag, base_pos, pos, base_text, ocr_text in diff_lst:
        #     compare_seg = CompareSeg(compare_reel=compare_reel,
        #     base_pos=base_pos,
        #     ocr_text=ocr_text, base_text=base_text)
        #     compare_seg.save()
        #     correct_seg = CorrectSeg(task=task1, compare_seg=compare_seg)
        #     correct_seg.selected_text = compare_seg.ocr_text
        #     correct_seg.position = pos
        #     correct_seg.save()
        ###

        # create Tasks
        # Correct Task
        # separators = extract_page_line_separators(huayan_yb_1.text)
        # separators_json = json.dumps(separators, separators=(',', ':'))

        # 校勘判取
        Task.objects.filter(batch_task=batch_task, typ=Task.TYPE_JUDGE).delete()
        Task.objects.filter(batch_task=batch_task, typ=Task.TYPE_JUDGE_VERIFY).delete()
        ReelDiff.objects.all().delete()

        task1 = Task(id=4, batch_task=batch_task, typ=Task.TYPE_JUDGE, base_reel=huayan_cb_1, task_no=1, status=Task.STATUS_READY,
        publisher=admin)
        task1.lqreel = lqreel
        task1.save()

        task2 = Task(id=5, batch_task=batch_task, typ=Task.TYPE_JUDGE, base_reel=huayan_cb_1, task_no=2, status=Task.STATUS_READY,
        publisher=admin)
        task2.lqreel = lqreel
        task2.save()

        task3 = Task(id=6, batch_task=batch_task, typ=Task.TYPE_JUDGE_VERIFY, base_reel=huayan_cb_1, task_no=0, status=Task.STATUS_NOT_READY,
        publisher=admin)
        #task3.separators = separators_json
        task3.lqreel = lqreel
        task3.save()

        reel_diff = ReelDiff(lqsutra=lqsutra, reel_no=reel_no, base_sutra=huayan_cb, task=task1, base_text=huayan_cb_1.text)
        reel_diff.save()
        test_text_diff(reel_diff)
        
        
            


