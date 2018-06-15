from tdata.models import *
from tasks.models import *
from tasks.common import *
from collections import defaultdict
from tasks.utils.variant_map import VariantManager

import os, sys
from os.path import isfile, join
import traceback

from cdifflib import CSequenceMatcher
SequenceMatcher=CSequenceMatcher
import re, json

def set_char_position(diffsegtext, tid_to_reeltext):
    tid = diffsegtext.tripitaka_id
    position = diffsegtext.position + diffsegtext.offset
    if diffsegtext.text:
        end_index = position + len(diffsegtext.text) - 1
    else:
        end_index = position
    diffsegtext.start_char_pos = tid_to_reeltext[tid].get_char_position(position)
    diffsegtext.end_char_pos = tid_to_reeltext[tid].get_char_position(end_index)

def is_in_skip_range(skip_ranges, i1, i2):
    for start, end in skip_ranges:
        if i1 >= start:
            if i1 < end:
                return True
        else:
            if i2 >= start:
                return True
    return False

def generate_text_diff(reeltext_lst, reeldiff_lst, skip_ranges_lst):
    n = len(reeltext_lst)
    if n <= 1:
        return []
    opcodes_lst = []
    for i in range(1, n):
        opcodes = SequenceMatcher(None, reeltext_lst[0].text, reeltext_lst[i].text, False).get_opcodes()
        opcodes_lst.append(opcodes)

    reeldiff_idx = 0
    diffseg_lst = []
    diffsegtexts_lst = []
    position_lst = [0] * n
    offset_lst = [0] * n
    while True:
        length_lst = []
        all_equal = True
        for i in range(n - 1):
            if len(opcodes_lst[i]) > 0:
                tag, i1, i2, j1, j2 = opcodes_lst[i][0]
                length = i2 - i1
                length_lst.append( length )
                if not is_in_skip_range(skip_ranges_lst[i], i1, i2):
                    if tag != 'equal':
                        all_equal = False
        if len(length_lst) == 0:
            break

        if reeldiff_idx >= len(reeldiff_lst):
            break

        min_length = min(length_lst)
        if position_lst[0] + min_length >= reeldiff_lst[reeldiff_idx].base_text_len:
            min_length = reeldiff_lst[reeldiff_idx].base_text_len - position_lst[0]
        if all_equal:
            position_lst[0] += min_length
            for i in range(n - 1):
                if len(opcodes_lst[i]) > 0:
                    tag, i1, i2, j1, j2 = opcodes_lst[i][0]
                    if tag == 'equal':
                        # print('equal:', reeltext_lst[0].text[i1:i1+min_length])
                        if (i2 - i1) == min_length:
                            opcodes_lst[i].pop(0)
                        else:
                            opcodes_lst[i][0] = (tag, i1 + min_length, i2, j1 + min_length, j2)
                        position_lst[i+1] += min_length
                    elif tag == 'replace': # in skip range
                        add_length = (j2 - j1)
                        if (i2 - i1) == min_length:
                            opcodes_lst[i].pop(0)
                        else:
                            if add_length > min_length:
                                add_length = min_length
                            opcodes_lst[i][0] = (tag, i1 + min_length, i2, j1 + add_length, j2)
                        position_lst[i+1] += add_length
                    elif tag == 'delete': # in skip range
                        if (i2 - i1) == min_length:
                            opcodes_lst[i].pop(0)
                        else:
                            opcodes_lst[i][0] = (tag, i1 + min_length, i2, j1, j2)
        else:
            diffseg = DiffSeg(base_pos=position_lst[0], reeldiff=reeldiff_lst[reeldiff_idx])
            diffseg_lst.append(diffseg)
            # print('diffseg start: ', position_lst)
            diffsegtexts = []
            segtext_index_lst = []

            start = position_lst[0] + offset_lst[0]
            end = start + min_length
            s = reeltext_lst[0].text[start : end]
            diffsegtext = DiffSegText(
                tripitaka=reeltext_lst[0].tripitaka,
                text=s,
                position=position_lst[0],
                offset=offset_lst[0])
            diffsegtexts.append(diffsegtext)
            segtext_index_lst.append(0)
            position_lst[0] += min_length

            if min_length == 0: # process all insert opcode
                for i in range(n - 1):
                    if len(opcodes_lst[i]) > 0:
                        tag, i1, i2, j1, j2 = opcodes_lst[i][0]
                        if tag == 'insert':
                            s = reeltext_lst[i+1].text[j1:j2]
                            diffsegtext = DiffSegText(
                                tripitaka=reeltext_lst[i+1].tripitaka,
                                text=s,
                                position=position_lst[i+1],
                                offset=offset_lst[i+1])
                            diffsegtexts.append(diffsegtext)
                            segtext_index_lst.append(i+1)
                            position_lst[i+1] += len(diffsegtext.text)
                            opcodes_lst[i].pop(0)
            else:
                for i in range(n - 1):
                    if len(opcodes_lst[i]) > 0:
                        tag, i1, i2, j1, j2 = opcodes_lst[i][0]
                        if tag == 'equal':
                            s = reeltext_lst[0].text[i1:i1+min_length]
                            diffsegtext = DiffSegText(
                                tripitaka=reeltext_lst[i+1].tripitaka,
                                text=s,
                                position=position_lst[i+1],
                                offset=offset_lst[i+1])
                            diffsegtexts.append(diffsegtext)
                            segtext_index_lst.append(i+1)
                            position_lst[i+1] += len(diffsegtext.text)

                            if (i2 - i1) == min_length:
                                opcodes_lst[i].pop(0)
                            else:
                                opcodes_lst[i][0] = (tag, i1+min_length, i2, j1+min_length, j2)
                        elif tag == 'delete':
                            start = position_lst[0] + offset_lst[0] - min_length
                            end = start + min_length
                            if is_in_skip_range(skip_ranges_lst[i], start, end):
                                s = None
                            else:
                                s = ''
                            diffsegtext = DiffSegText(
                                tripitaka=reeltext_lst[i+1].tripitaka,
                                text=s,
                                position=position_lst[i+1],
                                offset=offset_lst[i+1])
                            diffsegtexts.append(diffsegtext)
                            segtext_index_lst.append(i+1)

                            if (i2 - i1) == min_length:
                                opcodes_lst[i].pop(0)
                            else:
                                opcodes_lst[i][0] = (tag, i1+min_length, i2, j1, j2)
                        elif tag == 'replace':
                            add_length = min_length
                            if (i2 - i1) == min_length:
                                s = reeltext_lst[i+1].text[j1:j2]
                                add_length = j2 - j1
                                opcodes_lst[i].pop(0)
                            else:
                                if (j2 - j1) < min_length:
                                    add_length = j2 - j1
                                s = reeltext_lst[i+1].text[j1:j1+add_length]
                                opcodes_lst[i][0] = (tag, i1+min_length, i2, j1+add_length, j2)
                            start = position_lst[0] + offset_lst[0] - min_length
                            end = start + min_length
                            if is_in_skip_range(skip_ranges_lst[i], start, end):
                                s = None

                            diffsegtext = DiffSegText(
                                tripitaka=reeltext_lst[i+1].tripitaka,
                                text=s,
                                position=position_lst[i+1],
                                offset=offset_lst[i+1])
                            diffsegtexts.append(diffsegtext)
                            segtext_index_lst.append(i+1)
                            position_lst[i+1] += add_length
            for i in range(n):
                if i not in segtext_index_lst:
                    start = position_lst[0] + offset_lst[0] - min_length
                    end = start + min_length
                    if i > 0 and is_in_skip_range(skip_ranges_lst[i-1], start, end):
                        s = None
                    else:
                        s = ''
                    diffsegtext = DiffSegText(
                        tripitaka=reeltext_lst[i].tripitaka,
                        text=s,
                        position=position_lst[i],
                        offset=offset_lst[i])
                    diffsegtexts.append(diffsegtext)
            diffsegtexts_lst.append(diffsegtexts)
            # for diffsegtext in diffsegtexts:
            #     print(diffsegtext.tripitaka.code, diffsegtext.position, diffsegtext.offset, diffsegtext.text)
            # print('diffseg end: ', position_lst)

        if position_lst[0] == reeldiff_lst[reeldiff_idx].base_text_len:
            reeldiff_idx += 1
            for i in range(n):
                offset_lst[i] += position_lst[i]
            for i in range(n):
                position_lst[i] = 0
    
    diffseg_lst, diffsegtexts_lst = merge_diffseg(diffseg_lst, diffsegtexts_lst)
    create_diffseg(diffseg_lst, diffsegtexts_lst, reeltext_lst)

def merge_diffseg(diffseg_lst, diffsegtexts_lst):
    diffseg_count = len(diffseg_lst)

    # 将连接的DiffSeg合并
    new_diffseg_lst = []
    new_diffsegtexts_lst = []
    for i in range(diffseg_count):
        diffseg = diffseg_lst[i]
        diffsegtexts = diffsegtexts_lst[i]
        diffseg.base_pos = diffsegtexts[0].position
        diffseg.base_length = len(diffsegtexts[0].text)
        tid_set = get_diffsegtext_tripitaka_id(diffsegtexts)
        if i > 0:
            prev_diffseg = new_diffseg_lst[-1]
            prev_diffsegtexts = new_diffsegtexts_lst[-1]
            prev_tid_set = get_diffsegtext_tripitaka_id(prev_diffsegtexts)
            if prev_diffseg.base_pos + prev_diffseg.base_length == diffseg.base_pos and \
                prev_tid_set == tid_set:
                # 与上一条DiffSeg合并
                prev_diffseg.base_length += diffseg.base_length
                for diffsegtext in diffsegtexts:
                    tripitaka_id = diffsegtext.tripitaka_id
                    text = diffsegtext.text
                    for prev_diffsegtext in prev_diffsegtexts:
                        if prev_diffsegtext.tripitaka_id == tripitaka_id:
                            if prev_diffsegtext.text is not None:
                                prev_diffsegtext.text += text
                            break
                continue
        new_diffseg_lst.append(diffseg)
        new_diffsegtexts_lst.append(diffsegtexts)
    return (new_diffseg_lst, new_diffsegtexts_lst)

def create_diffseg(diffseg_lst, diffsegtexts_lst, reeltext_lst):
    diffseg_count = len(diffseg_lst)

    # 创建DiffSeg
    DiffSeg.objects.bulk_create(diffseg_lst)

    diffseg_pos_lst = []
    last_reeldiff_id = None
    for diffseg in diffseg_lst:
        if last_reeldiff_id and diffseg.reeldiff_id != last_reeldiff_id:
            diffseg_pos_lst_json = json.dumps(diffseg_pos_lst)
            ReelDiff.objects.filter(id=last_reeldiff_id).update(diffseg_pos_lst=diffseg_pos_lst_json)
            diffseg_pos_lst = []
        diffseg_pos_lst.append({
            'diffseg_id': diffseg.id,
            'base_pos': diffseg.base_pos,
            'base_length': diffseg.base_length
        })
        last_reeldiff_id = diffseg.reeldiff_id
    diffseg_pos_lst_json = json.dumps(diffseg_pos_lst)
    ReelDiff.objects.filter(id=last_reeldiff_id).update(diffseg_pos_lst=diffseg_pos_lst_json)

    # 创建DiffSegText
    tid_to_reeltext = {}
    for reeltext in reeltext_lst:
        tid_to_reeltext[reeltext.tripitaka_id] = reeltext
    diffsegtext_lst = []
    for i in range(diffseg_count):
        diffseg = diffseg_lst[i]
        diffsegtexts = diffsegtexts_lst[i]
        for diffsegtext in diffsegtexts:
            diffsegtext.diffseg = diffseg
            set_char_position(diffsegtext, tid_to_reeltext)
            diffsegtext_lst.append(diffsegtext)
    DiffSegText.objects.bulk_create(diffsegtext_lst)

def get_diffsegtext_tripitaka_id(diffsegtexts):
    tid_set = set()
    for diffsegtext in diffsegtexts:
        if diffsegtext.text is not None:
            tid_set.add(diffsegtext.tripitaka_id)
    return tid_set

def get_skip_ranges_lst(sutra_lst, multireeltexts):
    skip_ranges_lst = []
    text1 = clean_separators(multireeltexts[0].text)
    for i in range(1, len(sutra_lst)):
        text2 = clean_separators(multireeltexts[i].text)
        skip_ranges = []
        opcodes = SequenceMatcher(lambda x: x in 'pb\n', text1, text2, False).get_opcodes()
        for opcode in opcodes:
            tag, i1, i2, j1, j2 = opcode
            if tag == 'delete' and (i2 - i1) >= 100:
                skip_ranges.append( (i1, i2) )
            if tag == 'replace' and (i2 - i1) - (j2 - j1) >= 100:
                skip_ranges.append( (i1 + (j2 - j1), i2) )
        skip_ranges_lst.append(skip_ranges)
    return skip_ranges_lst

def get_multireeltext(sutra, variant_manager=None):
    multireeltext = MultiReelText(sutra.tripitaka_id)
    queryset = Reel.objects.filter(sutra=sutra)
    for reel in queryset.order_by('reel_no'):
        if not reel.used_in_collation:
            continue
        mark = Mark.objects.filter(reel=reel).exclude(publisher=None).order_by('-id').first()
        if mark is None:
            continue
        reelcorrecttext = mark.reeltext
        reel_text = reelcorrecttext.text
        if variant_manager:
            reel_text = variant_manager.replace_variant(reel_text)
        start = 0
        end = 0
        for markunit in MarkUnit.objects.filter(mark=mark).order_by('start'):
            if not markunit.in_body():
                end = markunit.start
                if start < end and reel_text[start:end] not in ['p\n', 'b\n', '\n']:
                    # print('markunit.start, markunit.end, ', markunit.start, markunit.end)
                    # print('start, end, ', start, end)
                    # print('head: ', reel_text[:start])
                    # print('body: ', reel_text[start:end])
                    multireeltext.add_reeltext(reel, reel_text[start:end], reel_text[:start])
                start = markunit.end
                end = markunit.end
        end = len(reel_text)
        if start < end and reel_text[start:end] not in ['p\n', 'b\n', '\n']:
            multireeltext.add_reeltext(reel, reel_text[start:end], reel_text[:start])
    return multireeltext

class ReelText(object):
    def __init__(self, reel, text_len, head_text, separators):
        self.reel = reel
        self.text_len = text_len
        self.sid = self.reel.sutra.sid
        self.separators = separators
        self.head_text_len = len(SEPARATORS_PATTERN.sub('', head_text))
        self.start_count_p = head_text.count('p')
        self.start_count_n = head_text.count('\n')

    def get_char_position(self, index):
        count_p = self.start_count_p
        count_n = self.start_count_n
        page_no = -1
        line_no = -1
        char_no = -1
        last_pos = 0
        separator_count = len(self.separators)
        i = 0
        while i <= separator_count:
            if i < separator_count:
                pos, separator = self.separators[i]
            else:
                pos = self.text_len
            if pos > index and char_no == -1:
                # 第一次pos > index
                page_no = count_p
                line_no = count_n
                char_no = index - last_pos + 1
                break

            if i == separator_count:
                break
            if separator == 'p':
                count_p += 1
                count_n = 0
            elif separator == '\n':
                count_n += 1
            last_pos = pos
            i += 1
        # 在校勘记中的字ID格式：
        # 8位sid_3位卷号_2位卷中页号_1位栏位号_2位行号_2位行中字序号
        # YB000860_001_01_0_01_01
        char_pos = '%s_%03d_%02d_%s_%02d_%02d' % (\
            self.sid, self.reel.reel_no, page_no, '0', line_no, char_no)
        return char_pos

class MultiReelText(object):
    def __init__(self, tripitaka_id):
        self.reeltext_lst = []
        self.text = ''
        self.text_len = 0
        self.tripitaka_id = tripitaka_id
        self.tripitaka = Tripitaka.objects.get(id=self.tripitaka_id)

    def add_reeltext(self, reel, text, head_text):
        clean_text = SEPARATORS_PATTERN.sub('', text)
        clean_text_len = len(clean_text)
        separators = extract_page_line_separators(text)
        reeltext = ReelText(reel, clean_text_len, head_text, separators)
        self.reeltext_lst.append(reeltext)
        self.text += clean_text
        self.text_len += clean_text_len

    def get_char_position(self, index):
        relative_index = index
        reeltext_cnt = len(self.reeltext_lst)
        for i in range(reeltext_cnt):
            reeltext = self.reeltext_lst[i]
            if relative_index < reeltext.text_len:
                return reeltext.get_char_position(relative_index)
            else:
                relative_index -= reeltext.text_len
            if i == reeltext_cnt - 1:
                return reeltext.get_char_position(reeltext.text_len)

def create_reeldiff(lqsutra, base_sutra):
    sutra_lst = list(lqsutra.sutra_set.all())
    sutra_id_lst = [sutra.id for sutra in sutra_lst]
    base_sutra_index = sutra_id_lst.index(base_sutra.id)

    # 将底本换到第一个位置
    temp_sutra = sutra_lst[base_sutra_index]
    sutra_lst[base_sutra_index] = sutra_lst[0]
    sutra_lst[0] = temp_sutra

    multireeltexts = [get_multireeltext(base_sutra)]
    variant_manager = VariantManager()
    variant_manager.load_variant_map(multireeltexts[0].text)
    for sutra in sutra_lst[1:]:
        multireeltexts.append( get_multireeltext(sutra, variant_manager) )
    reeldiff_lst = []
    for reel in Reel.objects.filter(sutra=sutra_lst[0]).order_by('reel_no'):
        reelcorrecttext = ReelCorrectText.objects.filter(reel=reel).order_by('-id').first()
        reeldiff = ReelDiff(lqsutra=lqsutra, reel_no=reel.reel_no, base_text=reelcorrecttext)
        reeldiff_lst.append(reeldiff)
    ReelDiff.objects.bulk_create(reeldiff_lst)
    for reeldiff in reeldiff_lst:
        reeldiff.base_text_len = len(clean_separators(reeldiff.base_text.body))

    # get skip_ranges_lst
    skip_ranges_lst = get_skip_ranges_lst(sutra_lst, multireeltexts)
    generate_text_diff(multireeltexts, reeldiff_lst, skip_ranges_lst)
    return reeldiff_lst

def create_diffsegresults_for_judge_task(reeldiff_lst, lqsutra, base_sutra, max_reel_no):
    all_judge_tasks = []
    for reel_no in range(1, max_reel_no + 1):
        diffsegresult_lst = []
        reeldiff = reeldiff_lst[reel_no - 1]
        diffsegs = list(reeldiff.diffseg_set.all())
        lqreel = LQReel.objects.get(lqsutra=lqsutra, reel_no=reel_no)
        judge_task_lst = list(Task.objects.filter(typ=Task.TYPE_JUDGE, lqreel=lqreel))
        judge_task_ids = [t.id for t in judge_task_lst]
        all_judge_tasks.extend(judge_task_lst)
    
        for task in judge_task_lst:
            for diffseg in diffsegs:
                diffsegresult = DiffSegResult(task=task, diffseg=diffseg, selected_text=None)
                diffsegresult_lst.append(diffsegresult)
            task.reeldiff = reeldiff
            task.status = Task.STATUS_READY
        DiffSegResult.objects.bulk_create(diffsegresult_lst)
        Task.objects.filter(id__in=judge_task_ids).update(reeldiff=reeldiff, status=Task.STATUS_READY)
        Task.objects.filter(typ=Task.TYPE_JUDGE_VERIFY, lqreel=lqreel).update(reeldiff=reeldiff)
    return all_judge_tasks

def get_text_map(diffseg):
    text_map = defaultdict(None)
    for diffsegtext in diffseg.diffsegtexts.all():
        text_map[diffsegtext.tripitaka_id] = diffsegtext.text
    return text_map


def text_equal_for_diffseg(old_diffseg, diffseg, selected_text):
    old_text_map = get_text_map(old_diffseg)
    text_map = get_text_map(diffseg)
    # 当加入藏的文变化了，但更新后的文内容与已判断选定结果相同，不算异文，继续合并之前的判取结果
    for new_key in text_map.keys():
        if text_map[new_key] != old_text_map[new_key]:
            if (selected_text is not None) and text_map[new_key] != selected_text:
                return False
    return True

def copy_judge_result(old_diffsegresults, diffsegresults):
    old_len = len(old_diffsegresults)
    new_len = len(diffsegresults)
    old_idx = 0
    idx = 0
    while old_idx < old_len and idx < new_len:
        old_diffsegresult = old_diffsegresults[old_idx]
        diffsegresult = diffsegresults[idx]
        old_base_pos = old_diffsegresult.diffseg.base_pos
        base_pos = diffsegresult.diffseg.base_pos
        if old_base_pos < base_pos:
            old_idx += 1
            continue
        elif old_base_pos > base_pos:
            idx += 1
            continue
        if old_diffsegresult.diffseg.base_length == diffsegresult.diffseg.base_length and \
            text_equal_for_diffseg(old_diffsegresult.diffseg, diffsegresult.diffseg, old_diffsegresult.selected_text):
            diffsegresult.typ = old_diffsegresult.typ
            diffsegresult.selected_text = old_diffsegresult.selected_text
            diffsegresult.selected = old_diffsegresult.selected
            diffsegresult.doubt = old_diffsegresult.doubt
            diffsegresult.doubt_comment = old_diffsegresult.doubt_comment
            if diffsegresult.typ == DiffSegResult.TYPE_SPLIT:
                diffsegresult.split_info = old_diffsegresult.split_info
            elif old_diffsegresult.merged_diffsegresults:
                ids = old_diffsegresult.merged_diffsegresults.values_list('id', flat=True)
                new_merged = []
                bigger_len = len(list(filter(lambda x: x > old_diffsegresult.id, ids)))
                less_len = len(list(filter(lambda x: x < old_diffsegresult.id, ids)))
                for r in range( -1 * less_len, bigger_len + 1):
                    if r == 0:
                        continue
                    index = idx + r
                    if index >=0 and index < new_len:
                        new_merged.append(diffsegresults[index])
                diffsegresult.merged_diffsegresults.set(new_merged)
        old_idx += 1
        idx += 1


def create_new_diffsegresults_for_judge_task(reeldiff_lst, lqsutra, base_sutra, max_reel_no):
    for reel_no in range(1, max_reel_no + 1):
        reeldiff = reeldiff_lst[reel_no - 1]
        diffsegs = list(reeldiff.diffseg_set.order_by('id').all())
        lqreel = LQReel.objects.get(lqsutra=lqsutra, reel_no=reel_no)
        judge_task_lst = list(Task.objects.filter(typ=Task.TYPE_JUDGE, lqreel=lqreel))
        judge_task_ids = [t.id for t in judge_task_lst]
        for task in judge_task_lst:
            diffsegresults = []
            for diffseg in diffsegs:
                diffsegresult = DiffSegResult(task=task, diffseg=diffseg, selected_text=None)
                diffsegresults.append(diffsegresult)
            old_diffsegresults = list(task.diffsegresult_set.order_by('id').all())
            DiffSegResult.objects.filter(task=task).delete()
            DiffSegResult.objects.bulk_create(diffsegresults)
            copy_judge_result(old_diffsegresults, diffsegresults)
        Task.objects.filter(id__in=judge_task_ids).update(reeldiff=reeldiff)
        judge_verify_task = Task.objects.get(typ=Task.TYPE_JUDGE_VERIFY, lqreel=lqreel)
        DiffSegResult.objects.filter(task=judge_verify_task).delete()
        judge_verify_task.reeldiff = reeldiff
        judge_verify_task.save(update_fields=['reeldiff'])

def create_data_for_judge_tasks(lqsutra, base_sutra, max_reel_no):
    reeldiff_lst = create_reeldiff(lqsutra, base_sutra)
    return create_diffsegresults_for_judge_task(reeldiff_lst, lqsutra, base_sutra, \
    max_reel_no)

def create_new_data_for_judge_tasks(lqsutra, base_sutra, max_reel_no):
    Task.objects.filter(lqreel__lqsutra=lqsutra, typ=Task.TYPE_JUDGE,
    status__in=[Task.STATUS_PROCESSING, Task.STATUS_FINISHED]).update(status=Task.STATUS_SYSTEM_PAUSED)
    Task.objects.filter(lqreel__lqsutra=lqsutra, typ=Task.TYPE_JUDGE,
    status=Task.STATUS_READY).update(status=Task.STATUS_NOT_READY)
    # 校勘判取审定任务的状态改为STATUS_NOT_READY
    Task.objects.filter(typ=Task.TYPE_JUDGE_VERIFY, lqreel__lqsutra=lqsutra)\
    .update(status=Task.STATUS_NOT_READY)
    judge_tasks = list(Task.objects.filter(lqreel__lqsutra=lqsutra, typ=Task.TYPE_JUDGE))
    task_ids = [t.id for t in judge_tasks]

    old_diffsegresult_ids = list([diffsegresult.id for diffsegresult in \
    DiffSegResult.objects.filter(task_id__in=task_ids)])
    old_reeldiff_ids = list([reeldiff.id for reeldiff in ReelDiff.objects.filter(lqsutra=lqsutra)])

    reeldiff_lst = create_reeldiff(lqsutra, base_sutra)
    create_new_diffsegresults_for_judge_task(reeldiff_lst, lqsutra, base_sutra, \
    max_reel_no)
    DiffSegResult.objects.filter(id__in=old_diffsegresult_ids).delete()
    ReelDiff.objects.filter(id__in=old_reeldiff_ids).delete()

    Task.objects.filter(lqreel__lqsutra=lqsutra, typ=Task.TYPE_JUDGE,
    status=Task.STATUS_SYSTEM_PAUSED).update(status=Task.STATUS_PROCESSING)
    Task.objects.filter(lqreel__lqsutra=lqsutra, typ=Task.TYPE_JUDGE,
    status=Task.STATUS_NOT_READY).update(status=Task.STATUS_READY)

def is_sutra_ready_for_judge(lqsutra):
    sutra_lst = list(lqsutra.sutra_set.all())
    for sutra in sutra_lst:
        for reel in sutra.reel_set.all():
            if reel.used_in_collation and (not reel.mark_ready):
                return False
    return True