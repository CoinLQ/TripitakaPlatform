from django.conf import settings
from cdifflib import CSequenceMatcher
SequenceMatcher=CSequenceMatcher
import re

from tdata.models import Configuration
from tasks.models import CorrectSeg

class OCRCompare(object):
    '''
    用于文字校对前的文本比对，OCR文本除文本外，只含有p或\n
    '''

    variant_map = None

    @classmethod
    def load_variant_map(cls):
        if cls.variant_map:
            return
        config = Configuration.objects.first()
        variant_map = {}
        i = 1
        for line in config.variant.split('\n'):
            line = line.strip()
            for ch in line:
                variant_map[ch] = i
            i += 1
        cls.variant_map = variant_map

    @classmethod
    def insert(cls, result_lst, t):
        if t:
            result_lst.append(t)

    @classmethod
    def split_text_by_linefeed(cls, result_lst, text):
        segs = text.split('\n')
        i = 0
        count = len(segs)
        while i < count:
            cls.insert(result_lst, segs[i])
            if i < count - 1:
                result_lst.append('\n')
            i += 1

    @classmethod
    def split_text_by_b(cls, result_lst, text):
        segs = text.split('b')
        i = 0
        count = len(segs)
        while i < count:
            cls.split_text_by_linefeed(result_lst, segs[i])
            if i < count - 1:
                result_lst.append('b')
            i += 1

    @classmethod
    def split_text(cls, text):
        result_lst = []
        segs = text.split('p')
        i = 0
        count = len(segs)
        while i < count:
            cls.split_text_by_b(result_lst, segs[i])
            if i < count - 1:
                result_lst.append('p')
            i += 1
        return result_lst

    @classmethod
    def count_page_line(cls, text, page_no, line_no, char_no):
        for ch in text:
            if ch == 'p':
                page_no += 1
                line_no = 0
                char_no = 0
            elif ch == '\n':
                line_no += 1
                char_no = 1
            elif ch == 'b':
                line_no -= 1
            else:
                char_no += 1
        return (page_no, line_no, char_no)

    @classmethod
    def get_tag(cls, text):
        if text == 'p':
            return CorrectSeg.TAG_P
        elif text == 'b':
            return CorrectSeg.TAG_P
        elif text == '\n':
            return CorrectSeg.TAG_LINEFEED
        return CorrectSeg.TAG_DIFF

    @classmethod
    def check_variant_equal(cls, text1, text2):
        if len(text1) != len(text2):
            return False
        for i in range(len(text1)):
            ch1 = text1[i]
            ch2 = text2[i]
            if ch1 == ch2:
                continue
            ch_no1 = cls.variant_map.get(ch1, -1)
            ch_no2 = cls.variant_map.get(ch2, -2)
            if ch_no1 != ch_no2:
                return False
        return True

    @classmethod
    def combine_equal_seg(cls, correctsegs):
        new_correctsegs = []
        last_tag = None
        for seg in correctsegs:
            if new_correctsegs:
                last_tag = new_correctsegs[-1]
            if seg.tag != CorrectSeg.TAG_EQUAL:
                new_correctsegs.append(seg)
            else:
                # 最后的tag是equal
                if last_tag and last_tag.tag == CorrectSeg.TAG_EQUAL:
                    if last_tag.position + len(last_tag.text2) != seg.position:
                        new_correctsegs.append(seg)
                    else:
                        last_tag.text2 = last_tag.text2 + seg.text2
                        last_tag.selected_text = last_tag.text2
                # 最后的tag不是equal
                else:
                    new_correctsegs.append(seg)

        return new_correctsegs

    @classmethod
    def preprocess_ocr_text(cls, text):
        for key in ['校勘記', '\n音釋\n']:
            pos = text.find(key)
            if pos != -1:
                text = text[:pos]
        lines = text.split('\n')
        filter_keywords = ['永乐北藏', '乾薩大藏', '乾隆大藏']
        new_lines = []
        for line in lines:
            for keyword in filter_keywords:
                if line.find(keyword) != -1:
                    line = ''
                    break
            new_lines.append(line)
        text = '\n'.join(new_lines)
        return text

    @classmethod
    def generate_correct_diff(cls, text1, text2):
        """
        用于文字校对前的文本比对
        text1是基础本；text2是要比对的版本。
        """
        cls.load_variant_map()
        SEPARATORS_PATTERN = re.compile('[pb\n]')
        text1 = SEPARATORS_PATTERN.sub('', text1)
        correctsegs = []
        pos = 0
        page_no = 0
        line_no = 0
        char_no = 0
        opcodes = SequenceMatcher(lambda x: x in 'pb\n', text1, text2, False).get_opcodes()
        for tag, i1, i2, j1, j2 in opcodes:
            if ((i2-i1) - (j2-j1) > 200):
                break
            if ((i2-i1) - (j2-j1) > 30):
                base_text = ''
            else:
                base_text = text1[i1:i2]
            if tag == 'equal':
                correctseg = CorrectSeg(tag=CorrectSeg.TAG_EQUAL, position=pos, \
                text1='', text2=text1[i1:i2], selected_text=text1[i1:i2], \
                page_no=page_no, line_no=line_no, char_no=char_no)
                correctsegs.append(correctseg)
                pos += (j2 - j1)
                page_no, line_no, char_no = cls.count_page_line(text2[j1:j2], page_no, line_no, char_no)
            elif tag == 'insert':
                base_text = ''
                result_lst = cls.split_text(text2[j1:j2])
                for result in result_lst:
                    tag = cls.get_tag(result)
                    correctseg = CorrectSeg(tag=tag, position=pos, \
                    text1='', text2=result, selected_text=None, \
                    page_no=page_no, line_no=line_no, char_no=char_no)
                    if result in 'pb\n':
                        correctseg.selected_text = result
                    correctsegs.append(correctseg)
                    pos += len(result)
                    page_no, line_no, char_no = cls.count_page_line(result, page_no, line_no, char_no)
            elif tag == 'replace':
                result_lst = cls.split_text(text2[j1:j2])
                replace_not_inserted = True # 有一次replace
                all_sep = all( [ result in 'pb\n' for result in result_lst ] )
                if all_sep:
                    correctseg = CorrectSeg(tag=CorrectSeg.TAG_DIFF, position=pos, \
                    text1=base_text, text2='', selected_text=None, \
                    page_no=page_no, line_no=line_no, char_no=char_no)
                    replace_not_inserted = False
                    correctsegs.append(correctseg)
                for result in result_lst:
                    if result not in 'pb\n' and replace_not_inserted:
                        correctseg = CorrectSeg(tag=CorrectSeg.TAG_DIFF, position=pos, \
                        text1=base_text, text2=result, selected_text=None, \
                        page_no=page_no, line_no=line_no, char_no=char_no)
                        replace_not_inserted = False
                        if OCRCompare.check_variant_equal(base_text, result):
                            correctseg.tag = CorrectSeg.TAG_EQUAL
                            correctseg.selected_text = result
                    else:
                        tag = cls.get_tag(result)
                        correctseg = CorrectSeg(tag=tag, position=pos, \
                        text1='', text2=result, selected_text=None, \
                        page_no=page_no, line_no=line_no, char_no=char_no)
                        if result in 'pb\n':
                            correctseg.selected_text = result
                    correctsegs.append(correctseg)
                    pos += len(result)
                    page_no, line_no, char_no = cls.count_page_line(result, page_no, line_no, char_no)
            elif tag == 'delete':
                correctseg = CorrectSeg(tag=CorrectSeg.TAG_DIFF, position=pos, \
                text1=base_text, text2='', selected_text=None, \
                page_no=page_no, line_no=line_no, char_no=char_no)
                correctsegs.append(correctseg)
        return cls.combine_equal_seg(correctsegs)

    @classmethod
    def compare_reel(cls, text1, text2):
        """
        用于文字校对前的文本比对
        text1是基础本；text2是要比对的版本。
        """
        ocr_text = OCRCompare.preprocess_ocr_text(text2)
        correctsegs = OCRCompare.generate_correct_diff(text1, ocr_text)
        return correctsegs

    @classmethod
    def set_position(cls, from_correctsegs, correctsegs):
        from_seg_count = len(from_correctsegs)
        seg_count = len(correctsegs)
        i = 0
        j = 0
        if j < from_seg_count:
            start_pos = from_correctsegs[j].position
            end_pos = start_pos + len(from_correctsegs[j].selected_text) - 1
            while i < seg_count:
                pos = correctsegs[i].position
                if pos < start_pos:
                    break
                if pos >= start_pos and pos <= end_pos:
                    offset = pos - start_pos
                    correctsegs[i].page_no = from_correctsegs[j].page_no
                    correctsegs[i].line_no = from_correctsegs[j].line_no
                    correctsegs[i].char_no = from_correctsegs[j].char_no + offset
                    i += 1
                else:
                    j += 1
                    if j < from_seg_count:
                        start_pos = from_correctsegs[j].position
                        end_pos = start_pos + len(from_correctsegs[j].selected_text) - 1
                    else:
                        break

    @classmethod
    def reset_segposition(cls, from_correctsegs):
        pos = 0
        for seg in from_correctsegs:
            seg.position = pos
            if (seg.selected_text):
                pos += len(seg.selected_text)

    @classmethod
    def combine_correct_doubtseg(cls, doubtsegs_a, doubtsegs_b):
        doubtsegs_b = list(doubtsegs_b)
        doubtsegs_a = list(doubtsegs_a)
        combined_ids = []
        for seg_b in doubtsegs_b:
            for seg_a in filter(lambda x: x.page_no == seg_b.page_no and x.line_no == seg_b.line_no and x.char_no == seg_b.char_no, doubtsegs_a):
                if seg_b.doubt_text == seg_a.doubt_text:
                    seg_b.doubt_comment = "%s | %s" % (seg_b.doubt_comment, seg_a.doubt_comment)
                    combined_ids.append(seg_a.id)
            seg_b.id = None

        for seg_a in doubtsegs_a:
            if seg_a.id in combined_ids:
                continue
            seg_a.id = None
            doubtsegs_b.append(seg_a)
        return sorted(doubtsegs_b, key=lambda x: x.page_no, reverse=True)
