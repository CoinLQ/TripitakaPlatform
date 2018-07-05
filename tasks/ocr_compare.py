from django.conf import settings
from cdifflib import CSequenceMatcher
SequenceMatcher=CSequenceMatcher
import re, sys

from tdata.models import Configuration
from tasks.models import CorrectSeg
from tasks.common import clean_separators
from tasks.utils.text_align import get_align_pos
from tasks.utils.variant_map import VariantManager

class SeparatorManager(object):

    def extract_ocr_separators(self, text):
        """
        例如，输入为以下字符串：
        p\n大方廣\n東晉b\n世間淨\n
           0 1 2  3 4   5 6 7
        这个函数的作用是把分隔符收集起来。其输出为
        [
            (0,"p\n"),
            (3,"\n"),
            (5,"b\n"),
            (8,"\n")
        ]
        元组第一个是文本字符下标。分隔符不计入下标的统计
        """
        if text == '':
            return []
        separators = []
        pos = 0
        sep = ''
        for c in text:
            if c in 'pb\n':
                sep += c
            else:
                if sep:
                    separators.append( (pos, sep) )
                    sep = ''
                pos += 1
        return separators

    def __init__(self, text):
        self.separators = self.extract_ocr_separators(text)
        self.count = len(self.separators)
        self.index = 0
        self.get_separator_pos()

    def get_separator_pos(self):
        if self.index < self.count:
            self.pos = self.separators[self.index][0]
        else:
            self.pos = sys.maxsize

    def move_to_next_separator(self):
        self.index += 1
        self.get_separator_pos()

    def merge_text_separator(self, text, start_pos, end_pos, text_tag):
        """
        根据分隔符所在位置，把分隔符和当前的文本单元合并起来

        start_pos是text对应的起始index
        end_pos是text对应的结束index
        """
        if text_tag == 'equal':
            text_tag = CorrectSeg.TAG_EQUAL
        else:
            text_tag = CorrectSeg.TAG_DIFF
        cur_pos = start_pos
        text_lst = []
        while self.pos >= cur_pos and self.pos <= end_pos:
            if self.pos > cur_pos:
                s = text[cur_pos - start_pos : self.pos - start_pos]
                text_lst.append({
                    'tag': text_tag,
                    'text': s,
                })
                cur_pos = self.pos
            for c in self.separators[self.index][1]:
                if c == '\n':
                    tag = CorrectSeg.TAG_LINEFEED
                else:
                    tag = CorrectSeg.TAG_P
                text_lst.append({
                    'tag': tag,
                    'text': c,
                })
            self.move_to_next_separator()
        if cur_pos < end_pos:
            s = text[cur_pos - start_pos : end_pos - start_pos]
            text_lst.append({
                'tag': text_tag,
                'text': s,
            })
        return text_lst

class OCRCompare(object):
    '''
    用于文字校对前的文本比对，OCR文本除文本外，只含有p或\n
    '''

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
                    if last_tag.position + len(last_tag.text1) != seg.position:
                        new_correctsegs.append(seg)
                    else:
                        last_tag.text1 = last_tag.text1 + seg.text1
                        last_tag.selected_text = last_tag.text1
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
        filter_keywords = ['永乐北藏', '永樂北藏', '乾薩大藏', '乾隆大藏']
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
    def get_base_text(cls, base_text_lst, ocr_text):
        body = base_text_lst[1]
        clean_ocr_text = clean_separators(ocr_text)
        clean_body = clean_separators(body)
        start_index, end_index = get_align_pos(clean_body, clean_ocr_text)
        start = 0
        end = 0
        body_len = len(body)
        i = 0
        index = 0
        for i in range(body_len):
            if body[i] not in 'pb\n':
                index += 1
                if index == start_index:
                    start = i
                if index == end_index:
                    end = i
                    break
        while start > 0:
            if body[start] not in 'pb\n':
                start -= 1
            else:
                break
        while end < body_len:
            if body[end] not in 'pb\n':
                end += 1
            else:
                break
        base_text_lst[1] = body[start:end]
        return ''.join(base_text_lst)

    @classmethod
    def generate_correct_diff(cls, text1, text2):
        """
        用于文字校对前的文本比对
        text1是基础本；text2是要比对的版本。
        """
        variant_manager = VariantManager()
        variant_manager.load_variant_map(text2)
        SEPARATORS_PATTERN = re.compile('[pb\n]')
        text1 = SEPARATORS_PATTERN.sub('', text1)
        separator_manager = SeparatorManager(text2)
        text2 = SEPARATORS_PATTERN.sub('', text2)
        text1 = variant_manager.replace_variant(text1)
        correctsegs = []
        pos = 0
        page_no = 0
        line_no = 0
        char_no = 0
        opcodes = SequenceMatcher(lambda x: x in 'pb\n', text1, text2, False).get_opcodes()
        for tag, i1, i2, j1, j2 in opcodes:
            if tag == 'delete':
                correctseg = CorrectSeg(tag=CorrectSeg.TAG_DIFF, position=pos, \
                text1=text1[i1:i2], text2='', selected_text=None, \
                page_no=page_no, line_no=line_no, char_no=char_no)
                correctsegs.append(correctseg)
                continue
            base_index = i1
            consumed_text_len = 0
            text_lst = separator_manager.merge_text_separator(text2[j1:j2], j1, j2, tag)
            for text_seg in text_lst:
                text_tag = text_seg['tag']
                result = text_seg['text']
                result_len = len(result)
                correctseg = CorrectSeg(tag=text_tag, position=pos, \
                text1='', text2=result, selected_text=None, \
                page_no=page_no, line_no=line_no, char_no=char_no)
                if result in 'pb\n':
                    correctseg.selected_text = result
                    page_no, line_no, char_no = cls.count_page_line(result, page_no, line_no, char_no)
                else:
                    if tag == 'equal':
                        correctseg.text1 = result
                        correctseg.text2 = None
                        correctseg.selected_text = result
                    elif tag == 'replace':
                        consumed_text_len += result_len
                        if consumed_text_len == (j2 - j1):
                            end_index = i2
                        else:
                            end_index = min(base_index + result_len, i2)
                        correctseg.text1 = text1[base_index : end_index]
                        base_index = end_index
                    char_no += result_len
                correctsegs.append(correctseg)
                pos += result_len
        return correctsegs

    @classmethod
    def generate_correct_diff_for_verify(cls, text1, text2):
        """
        用于文字校对审定前的文本比对
        text1是校一；text2是校二、校三或校四。

        """
        SEPARATORS_PATTERN = re.compile('[pb\n]')
        separator_manager = SeparatorManager(text1)
        text1 = SEPARATORS_PATTERN.sub('', text1)
        text2 = SEPARATORS_PATTERN.sub('', text2)
        correctsegs = []
        pos = 0
        page_no = 0
        line_no = 0
        char_no = 0
        # 'p'/'b'/'\n'三个分隔符不参与对比
        opcodes = SequenceMatcher(lambda x: x in 'pb\n', text1, text2, False).get_opcodes()
        for tag, i1, i2, j1, j2 in opcodes:
            slice1=text1[i1:i2]
            slice2=text2[j1:j2]
            if tag == 'delete':
                correctseg = CorrectSeg(tag=CorrectSeg.TAG_DIFF, position=pos, \
                text1=text1[i1:i2], text2='', selected_text=None, \
                page_no=page_no, line_no=line_no, char_no=char_no)
                correctsegs.append(correctseg)
                pos += len(correctseg.text1)
                print(f"delete:{slice1}")
                print(f"\tcorrectseg:{correctseg.key_info()}")
                continue
            base_index = j1
            # text1[i1:i2]中已处理的文本长度
            consumed_text_len = 0
            print(f"\n=================处理:{tag},{i1}:{i2},{slice1},{j1}:{j2},{slice2}")
            text_lst = separator_manager.merge_text_separator(text1[i1:i2], i1, i2, tag)
            if len(text_lst)<=0:
                # 如果是insert类型,则slice2的文本就会被丢掉
                print("从text1产生的text_lst是空的")
            for text_seg in text_lst:
                text_tag = text_seg['tag']
                result = text_seg['text']
                result_len = len(result)
                correctseg = CorrectSeg(tag=text_tag, position=pos, \
                text1=result, text2=None, selected_text=None, \
                page_no=page_no, line_no=line_no, char_no=char_no)
                if result in 'pb\n':
                    correctseg.selected_text = result
                    print("分隔符")
                else:
                    if tag == 'equal':
                        correctseg.selected_text = result
                        print(f"equal:{result}")
                    elif tag == 'replace':
                        consumed_text_len += result_len
                        if consumed_text_len == (i2 - i1):
                            end_index = j2
                        else:
                            end_index = min(base_index + result_len, j2)
                        # 上面的代码保证了end_index<=j2,所以text2[base_index:end_index]不会溢出
                        correctseg.text2 = text2[base_index : end_index]
                        base_index = end_index
                        print(f"replace:{result} with {correctseg.text2}")
                    else:
                        print("[ERROR]未处理的tag类型")
                print(f"\tcorrectseg:{correctseg.key_info()}")
                correctsegs.append(correctseg)
                pos += result_len
        return correctsegs

    @classmethod
    def merge_correctseg_for_verify(cls, correctsegs, correctsegs_add, task_no):
        """
        合并两组文本切片。每一组切片都来自于两次校对结果的合并
        :param correctsegs:
        :param correctsegs_add:
        :param task_no:
        :return:
        """
        sep_tags = [CorrectSeg.TAG_P, CorrectSeg.TAG_LINEFEED]
        length = len(correctsegs)
        length_add = len(correctsegs_add)
        i = 0
        j = 0
        offset = 0
        offset_add = 0
        result_correctsegs = []
        while i < length and j < length_add:
            correctseg = correctsegs[i]
            correctseg_add = correctsegs_add[j]
            if correctseg.tag in sep_tags and correctseg_add.tag in sep_tags and \
                correctseg.position == correctseg_add.position:
                result_correctsegs.append(correctseg)
                i += 1
                j += 1
                offset = 0
                offset_add = 0
                continue
            remained = len(correctseg.text1) - offset
            remained_add  = len(correctseg_add.text1) - offset_add
            add_length = min(remained, remained_add)
            r_correctseg = CorrectSeg()
            r_correctseg.position = correctseg.position + offset
            if correctseg.tag == CorrectSeg.TAG_EQUAL and correctseg_add.tag == CorrectSeg.TAG_EQUAL:
                r_correctseg.tag = CorrectSeg.TAG_EQUAL
                r_correctseg.text1 = correctseg.text1[offset:(offset+add_length)]
                r_correctseg.selected_text = r_correctseg.text1
            else:
                r_correctseg.tag = CorrectSeg.TAG_DIFF
                r_correctseg.text1 = correctseg.text1[offset:(offset+add_length)]
                if correctseg.tag == CorrectSeg.TAG_EQUAL:
                    r_correctseg.text2 = r_correctseg.text1
                    if task_no == 4:
                        r_correctseg.text3 = r_correctseg.text1
                else:
                    if offset + add_length == len(correctseg.text1):
                        r_correctseg.text2 = correctseg.text2[offset:]
                    else:
                        r_correctseg.text2 = correctseg.text2[offset:(offset+add_length)]
                    if task_no == 4:
                        if offset + add_length == len(correctseg.text1):
                            r_correctseg.text3 = correctseg.text3[offset:]
                        else:
                            r_correctseg.text3 = correctseg.text3[offset:(offset+add_length)]
                text_add = ''
                if correctseg_add.tag == CorrectSeg.TAG_EQUAL:
                    text_add = r_correctseg.text1
                else:
                    if offset_add + add_length == len(correctseg_add.text1):
                        text_add = correctseg_add.text2[offset:]
                    else:
                        text_add = correctseg_add.text2[offset:(offset+add_length)]
                if task_no == 3:
                    r_correctseg.text3 = text_add
                elif task_no == 4:
                    r_correctseg.text4 = text_add
            if add_length == remained:
                i += 1
                offset = 0
            else:
                offset += add_length
            if add_length == remained_add:
                j += 1
                offset_add = 0
            else:
                offset_add += add_length
            result_correctsegs.append(r_correctseg)
        return result_correctsegs

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
