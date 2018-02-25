from tdata.models import *
from tasks.models import *
from tasks.common import *

import os, sys
from os.path import isfile, join
import traceback

from difflib import SequenceMatcher
import re, json

def set_char_position(diffsegtext, tid_to_reeltext):
    tid = diffsegtext.tripitaka_id
    if len(diffsegtext.text) > 0:
        end_index = diffsegtext.position + len(diffsegtext.text) - 1
    else:
        end_index = diffsegtext.position
    start_page_no, start_line_no, start_char_no, end_page_no, end_line_no, end_char_no = \
    tid_to_reeltext[tid].get_char_position(
        diffsegtext.position,
        end_index)
    reel = tid_to_reeltext[tid].reel
    # 在校勘记中的字ID格式：
    # 8位sid_3位卷号_2位卷中页号_1位栏位号_2位行号_2位行中字序号
    # YB000860_001_01_0_01_01
    diffsegtext.start_char_pos = '%s_%03d_%02d_%s_%02d_%02d' % (\
        reel.sutra.sid, reel.reel_no, start_page_no, '0', start_line_no, start_char_no)
    diffsegtext.end_char_pos = '%s_%03d_%02d_%s_%02d_%02d' % (\
        reel.sutra.sid, reel.reel_no, end_page_no, '0', end_line_no, end_char_no)

def generate_text_diff(reeltext_lst, reeldiff):
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
    diffseg_lst = []
    diffsegtexts_lst = []
    position_lst = [0] * n
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
                position_lst[i] += min_length
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
            diffseg = DiffSeg(reeldiff=reeldiff, base_pos=start_pos)
            diffseg_lst.append(diffseg)
            diffsegtexts = []
            segtext_index_lst = []

            s = reeltext_lst[0].text[start_pos : start_pos + min_length]
            start_pos += min_length
            text[s] = [reeltext_lst[0].tripitaka_id]
            diffsegtext = DiffSegText(
                tripitaka=reeltext_lst[0].tripitaka,
                text=s,
                position=position_lst[0])
            diffsegtexts.append(diffsegtext)
            segtext_index_lst.append(0)
            position_lst[0] += min_length

            if min_length == 0: # process all insert opcode
                i = 0
                while i < n - 1:
                    if len(opcodes_lst[i]) > 0:
                        tag, i1, i2, j1, j2 = opcodes_lst[i][0]
                        if tag == 'insert':
                            s = reeltext_lst[i+1].text[j1:j2]
                            code_lst = text.setdefault( s, [] )
                            code_lst.append( reeltext_lst[i+1].tripitaka_id )

                            diffsegtext = DiffSegText(
                                tripitaka=reeltext_lst[i+1].tripitaka,
                                text=s,
                                position=position_lst[i+1])
                            diffsegtexts.append(diffsegtext)
                            segtext_index_lst.append(i+1)
                            position_lst[i+1] += len(diffsegtext.text)
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

                            diffsegtext = DiffSegText(
                                tripitaka=reeltext_lst[i+1].tripitaka,
                                text=s,
                                position=position_lst[i+1])
                            diffsegtexts.append(diffsegtext)
                            segtext_index_lst.append(i+1)
                            position_lst[i+1] += len(diffsegtext.text)

                            if (i2 - i1) == min_length:
                                opcodes_lst[i].pop(0)
                            else:
                                opcodes_lst[i][0] = (tag, i1+min_length, i2, j1+min_length, j2)
                        elif tag == 'delete':
                            code_lst = text.setdefault( u'', [] )
                            code_lst.append( reeltext_lst[i+1].tripitaka_id )

                            diffsegtext = DiffSegText(
                                tripitaka=reeltext_lst[i+1].tripitaka,
                                text='',
                                position=position_lst[i+1])
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
                                code_lst = text.setdefault( s, [])
                                code_lst.append( reeltext_lst[i+1].tripitaka_id )
                                opcodes_lst[i].pop(0)
                            else:
                                s = reeltext_lst[i+1].text[j1:j1+min_length]
                                code_lst = text.setdefault(s , [] )
                                code_lst.append( reeltext_lst[i+1].tripitaka_id )
                                opcodes_lst[i][0] = (tag, i1+min_length, i2, j1+min_length, j2)

                            diffsegtext = DiffSegText(
                                tripitaka=reeltext_lst[i+1].tripitaka,
                                text=s,
                                position=position_lst[i+1])
                            diffsegtexts.append(diffsegtext)
                            segtext_index_lst.append(i+1)
                            position_lst[i+1] += len(diffsegtext.text)
                    i += 1
            for i in range(n):
                if i not in segtext_index_lst:
                    diffsegtext = DiffSegText(
                        tripitaka=reeltext_lst[i].tripitaka,
                        text='',
                        position=position_lst[i])
                    diffsegtexts.append(diffsegtext)
            diffsegtexts_lst.append(diffsegtexts)
            result['text'] = text
            result_lst.append(result)

    diffseg_count = len(diffseg_lst)

    # 将连接的DiffSeg合并
    new_diffseg_lst = []
    new_diffsegtexts_lst = []
    diffseg_pos_lst = []
    diffseg_no = 1
    for i in range(diffseg_count):
        diffseg = diffseg_lst[i]
        diffsegtexts = diffsegtexts_lst[i]
        diffseg.base_pos = diffsegtexts[0].position
        diffseg.base_length = len(diffsegtexts[0].text)
        if i > 0:
            prev_diffseg = new_diffseg_lst[-1]
            prev_diffsegtexts = new_diffsegtexts_lst[-1]
            if prev_diffseg.base_pos + prev_diffseg.base_length == diffseg.base_pos:
                # 与上一条DiffSeg合并
                prev_diffseg.base_length += diffseg.base_length
                for diffsegtext in diffsegtexts:
                    tripitaka_id = diffsegtext.tripitaka_id
                    text = diffsegtext.text
                    for prev_diffsegtext in prev_diffsegtexts:
                        if prev_diffsegtext.tripitaka_id == tripitaka_id:
                            prev_diffsegtext.text += text
                            break
                continue
        diffseg.diffseg_no = diffseg_no
        new_diffseg_lst.append(diffseg)
        new_diffsegtexts_lst.append(diffsegtexts)
        diffseg_no += 1

    diffseg_lst = new_diffseg_lst
    diffsegtexts_lst = new_diffsegtexts_lst
    diffseg_count = len(diffseg_lst)

    # 创建DiffSeg
    DiffSeg.objects.bulk_create(diffseg_lst)
    for diffseg in diffseg_lst:
        diffseg_pos_lst.append({
            'diffseg_id': diffseg.id,
            'base_pos': diffseg.base_pos,
            'base_length': diffseg.base_length
        })


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

    diffseg_pos_lst_json = json.dumps(diffseg_pos_lst)
    ReelDiff.objects.filter(id=reeldiff.id).update(diffseg_pos_lst=diffseg_pos_lst_json)
    return result_lst

def generate_reeldiff(reeldiff, sutra_lst, reel_lst, correct_text_lst):
    reel_no = reeldiff.reel_no
    reeltexts = []
    sutra_count = len(sutra_lst)
    i = 0
    while i < sutra_count:
        reel = Reel.objects.get(sutra_id=sutra_lst[i].id, reel_no=reel_no)
        reeltext = ReelText(
            reel,
            correct_text_lst[i],
            sutra_lst[i].tripitaka_id,
            sutra_lst[i].sid,
            reel_lst[i].start_vol,
            reel_lst[i].start_vol_page)
        reeltexts.append(reeltext)
        i += 1
    generate_text_diff(reeltexts, reeldiff)