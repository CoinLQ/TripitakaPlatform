from cdifflib import CSequenceMatcher
SequenceMatcher=CSequenceMatcher
import re, json, os
import urllib.request
import traceback

from tdata.models import *
from tdata.lib.image_name_encipher import get_cut_url
from tasks.models import *
from rect.models import *

from tasks.utils.cut_column import gene_new_col, crop_col_online

from django.db import transaction
from django.conf import settings

SEPARATORS_PATTERN = re.compile('[pb\n]')

import logging
logger = logging.getLogger(__name__)

def compact_json_dumps(obj):
    return json.dumps(obj, separators=(',', ':'))

def generate_accurate_chars(text1, text2, old_char_lst, debug=False):
    char_lst = []
    old_char_lst_length = len(old_char_lst)
    i = 0
    for ch in text2:
        if i >= old_char_lst_length:
            break
        if ch != '\n':
            old_char_lst[i]['ch'] = ch
            i += 1
    line_no = 1
    char_no = 1
    char_index = 0 # 下一个从old_char_lst要取出的字
    char_lst_length = 0
    opcodes = SequenceMatcher(None, text1, text2, False).get_opcodes()
    for tag, i1, i2, j1, j2 in opcodes:
        if debug:
            print(tag, text1[i1:i2], text2[j1:j2])
        if tag == 'equal':
            i = i1
            while i < i2:
                if text1[i] == '\n':
                    line_no += 1
                    char_no = 1
                else:
                    char_data = old_char_lst[char_index]
                    if debug:
                        print('move: ', char_data['ch'], char_data['line_no'], char_data['char_no'], line_no, char_no)
                    if text1[i] != char_data['ch']:
                        raise ValueError('not equal: %s %s' % (text1[i], char_data['ch']))
                    char_data['line_no'] = line_no
                    char_data['char_no'] = char_no
                    char_lst.append(char_data)
                    char_no += 1
                    char_lst_length += 1
                    char_index += 1
                i += 1
        elif tag == 'insert': # OCR本多出的字，需删除
            # text2[j1:j2]
            # 将相邻的同样的字标记为"need_confirm"
            # TODO: 改进
            length = j2 - j1
            # 前length
            i = 1
            temp_char_index = char_lst_length - 1
            while text2[j1-length*i : j2-length*i] == text2[j1:j2]:
                # 处理前length个字
                j = j2 - 1
                while temp_char_index >= 0 and j >= j1:
                    if text2[j] != '\n':
                        char_lst[temp_char_index]['need_confirm'] = 1
                        temp_char_index -= 1
                    j -= 1
                i += 1
            # 后length
            i = 1
            temp_char_index = char_index
            while text2[j1+length*i : j2+length*i] == text2[j1:j2]:
                # 处理后length个字
                j = j1
                while j < j2 and temp_char_index < old_char_lst_length:
                    if text2[j] != '\n':
                        old_char_lst[temp_char_index]['need_confirm'] = 1
                        temp_char_index += 1
                    j += 1
                i += 1

            for ch in text2[j1:j2]:
                if ch != '\n':
                    char_index += 1
        elif tag == 'replace':
            i = i1
            j = j1
            text2_ch_cnt = (j2-j1) - text2[j1:j2].count('\n')
            consumed_char_count = 0
            while i < i2:
                ch = text1[i]
                if ch == '\n':
                    line_no += 1
                    char_no = 1
                else:
                    text1_ch_cnt = (i-i1) - text1[i1:i].count('\n')
                    if text1_ch_cnt < text2_ch_cnt:
                        #print('char_index: ', char_index)
                        char_data = old_char_lst[char_index]
                        char_index += 1
                        consumed_char_count += 1
                        char_data['line_no'] = line_no
                        char_data['char_no'] = char_no
                        char_data['old_ch'] = char_data['ch']
                        char_data['ch'] = ch
                    else:
                        char_data = {
                            'line_no': line_no,
                            'char_no': char_no,
                            'ch': ch,
                            'added': 1,
                        }
                    char_lst.append(char_data)
                    char_no += 1
                i += 1
            text2_char_count = 0
            for ch in text2[j1:j2]:
                if ch != '\n':
                    text2_char_count += 1
            char_index += (text2_char_count - consumed_char_count)
        elif tag == 'delete': # OCR本缺少的字，需要增加
            add_count = i2 -i1
            for i in range(add_count):
                ch = text1[i1 + i]
                if ch == '\n':
                    line_no += 1
                    char_no = 1
                else:
                    char_data = {
                        'line_no': line_no,
                        'char_no': char_no,
                        'ch': ch,
                        'added': 1,
                    }
                    char_lst.append(char_data)
                    char_no += 1
    return char_lst

def count_line_char_count(text):
    line_char_count = {}
    lines = text.split('\n')
    line_no = 1
    bars = []
    bar = []
    for line in lines:
        if line == 'b':
            bars.append(bar)
            bar = []
        else:
            line_char_count[line_no] = len(line)
            bar.append(line_no)
            line_no += 1
    bars.append(bar)
    return line_char_count, bars

def get_bar_cord_lst(bars, line_char_count, char_map):
    bar_cord_lst = []
    for bar in bars:
        char_cnt_lst = []
        for line_no in bar:
            char_cnt_lst.append(line_char_count[line_no])
        if len(char_cnt_lst) == 0:
            bar_cord_lst.append([])
            continue
        max_cnt = max(char_cnt_lst)
        max_cnt_line_lst = []
        for line_no in bar:
            if line_char_count[line_no] == max_cnt:
                max_cnt_line_lst.append(line_no)
        cord_lst = []
        for i in range(max_cnt):
            total_y = 0
            total_h = 0
            cnt = 0
            for line_no in max_cnt_line_lst:
                s = '%02dn%02d' % (line_no, i + 1)
                try:
                    total_y += char_map[s]['y']
                    total_h += char_map[s]['h']
                    cnt += 1
                except:
                    pass
            if cnt != 0:
                avg_y = total_y / cnt
                avg_h = total_h / cnt
            else:
                avg_y = (i+1) * 25
                avg_h = 25
            cord_lst.append( (avg_y, avg_h) )
        bar_cord_lst.append(cord_lst)
    return bar_cord_lst

def get_line_cord_lst(char_lst):
    line_cord_lst = [] # 每行的平均x,w
    total_x = 0
    total_w = 0
    cnt = 0
    avg_x = 0
    avg_w = 0
    last_line_no = 0
    for char_data in char_lst:
        line_no = char_data['line_no']
        if line_no == last_line_no:
            if 'x' in char_data:
                total_x += char_data['x']
                total_w += char_data['w']
                cnt += 1
        elif line_no != 1:
            if cnt != 0:
                avg_x = total_x / cnt
                avg_w = total_w / cnt
            else:
                avg_x -= 35
                avg_w = 30
                if avg_x < 0:
                    avg_x = 0
            total_x = 0
            total_w = 0
            cnt = 0
            line_cord_lst.append( (avg_x, avg_w) )
        last_line_no = line_no
    # 最后一行
    if cnt != 0:
        avg_x = total_x / cnt
        avg_w = total_w / cnt
    else:
        avg_x -= 35
        avg_w = 30
        if avg_x < 0:
            avg_x = 0
    line_cord_lst.append( (avg_x, avg_w) )
    return line_cord_lst

def get_accurate_cut(text1, text2, cut_json, pid):
    """
    用于文字校对后的文本比对，text1是文字校对审定后得到的精确本，text2是OCR原始结果，都包含换行和换页标记。
    """
    clean_text1 = text1.rstrip('b').replace('b\n', '')
    clean_text2 = text2.rstrip('b').replace('b\n', '')
    try:
        cut = json.loads(cut_json)
    except Exception as err:
        logger.error('cut_json: %s', cut_json)
        raise err
    old_char_lst = cut['char_data']
    for char_data in old_char_lst:
        if char_data['x'] < 0:
            char_data['x'] = 0
        if char_data['y'] < 0:
            char_data['y'] = 0
        char_data['line_no'] = int(char_data['line_no'])
        char_data['char_no'] = int(char_data['char_no'])

    debug = False
    if debug:
        print('pid: ', pid)
    char_lst = generate_accurate_chars(clean_text1, clean_text2, old_char_lst, debug)

    column_count = 0
    if not char_lst:
        return char_lst, 0, 0, [], 0, 0, 0
    line_count = char_lst[-1]['line_no']
    char_count_lst = [0] * line_count
    char_map = {}
    for char_data in char_lst:
        line_no = char_data['line_no']
        char_no = char_data['char_no']
        char_count_lst[line_no - 1] += 1
        if 'char_id' in char_data:
            del char_data['char_id']
        if line_no > line_count:
            line_count = line_no
        if char_no > column_count:
            column_count = char_no
        line_char_str = '%02dn%02d' % (line_no, char_no)
        char_map[line_char_str] = char_data

    # 每行的平均x, w
    line_cord_lst = get_line_cord_lst(char_lst)

    # 栏中包含的行号
    line_char_count, bars = count_line_char_count(text1)

    line_to_bar_index = {}
    for bar_index in range(len(bars)):
        for line_no in bars[bar_index]:
            line_to_bar_index[line_no] = bar_index

    # 生成每栏的平均y, h
    bar_cord_lst = get_bar_cord_lst(bars, line_char_count, char_map)

    # 给增加的字加上切分坐标
    add_count = 0
    wrong_count = 0
    confirm_count = 0
    for char_data in char_lst:
        if 'old_char' in char_data:
            wrong_count += 1
        elif 'need_confirm' in char_data:
            confirm_count += 1
        elif 'added' in char_data:
            # 设定一个缺省值
            char_data['w'] = 30
            char_data['h'] = 25
            char_data['x'] = 30
            char_data['y'] = 30
            try:
                line_no = char_data['line_no']
                char_no = char_data['char_no']
                prev_line_no = line_no - 1
                next_line_no = line_no + 1
                cur_line_char_count = line_char_count[line_no]
                bar_index = line_to_bar_index[line_no]
                s = None
                prev_char_count = line_char_count.get(prev_line_no, 0)
                next_char_count = line_char_count.get(next_line_no, 0)
                if prev_line_no in bars[bar_index] and prev_char_count == cur_line_char_count:
                    s = '%02dn%02d' % (prev_line_no, char_no)
                elif next_line_no in bars[bar_index] and next_char_count == cur_line_char_count:
                    s = '%02dn%02d' % (next_line_no, char_no)
                if s and (s in char_map) and ('y' in char_map[s]):
                    char_data['y'] = char_map[s]['y']
                    char_data['h'] = char_map[s]['h']
                else:
                    bar_index = line_to_bar_index[line_no]
                    if char_no == 1:
                        char_idx = 0
                    else: # 找到上一字对应的index
                        char_idx = len(bar_cord_lst[bar_index]) - 1
                        last_char_s = '%02dn%02d' % (line_no, char_no-1)
                        last_y = char_map[last_char_s]['y']
                        for i in range(len(bar_cord_lst[bar_index])):
                            y, h = bar_cord_lst[bar_index][i]
                            if y - h/2 < last_y and last_y <= y + h/2 and (i + 1) < len(bar_cord_lst[bar_index]):
                                char_idx = i + 1
                                break
                    char_data['y'], char_data['h'] = bar_cord_lst[bar_index][char_idx]

                x, w = line_cord_lst[line_no-1]
                char_data['x'] = x
                char_data['w'] = w
            except:
                logger.exception('get_accurate_cut except: %s', json.dumps(char_data))
    return char_lst, line_count, column_count, char_count_lst, add_count, wrong_count, confirm_count

def get_char_region_cord(char_lst):
    # 得到字框顶点中最小和最大的x, y
    min_x = 10000
    min_y = 10000
    max_x = 0
    max_y = 0
    for char_data in char_lst:
        x = char_data.get('x', None)
        y = char_data.get('y', None)
        w = char_data.get('w', 0)
        h = char_data.get('h', 0)
        if x and y:
            if x < min_x:
                min_x = x
            if (x + w) > max_x:
                max_x = x + w
            if y < min_y:
                min_y = y
            if (y + h) > max_y:
                max_y = y + h
    return min_x, min_y, max_x, max_y

def fetch_cut_file(reel, vol_page, suffix='cut', force_download=False):
    if reel.reel_no <= 0 or vol_page == 0:
        return ''
    cut_filename = "%s/logs/%s%s.%s" % (settings.BASE_DIR, reel.image_prefix(), vol_page, suffix)
    if not force_download and os.path.exists( cut_filename ):
        with open(cut_filename, 'r') as f:
            data = f.read()
            if data:
                return data
    cut_url = get_cut_url(reel, vol_page, suffix)
    logger.info('wget %s', cut_url)
    try:
        with urllib.request.urlopen(cut_url) as f:
            logger.info('fetch done: %s, %d, page: %s', reel.sutra.sid, reel.reel_no, vol_page)
            data = f.read()
    except:
        logger.error('no data: %s', cut_url)
        return ''
    # '' 串不写
    if data:
        with open(cut_filename, 'wb') as fout:
            fout.write(data)
    return data

def rebuild_page_pagerects_for_s3(page):
    reel = page.reel
    schedule = Schedule.objects.filter(reels=reel).first()
    if schedule:
        for sched in Schedule.objects.filter(reels=reel):
            PageTask.objects.filter(schedule=sched, pagerect=page.pagerects.first()).all().delete()
            PageVerifyTask.objects.filter(schedule=sched, pagerect=page.pagerects.first()).all().delete()
    Rect.objects.filter(page_pid=page.pk).all().delete()
    page.pagerects.all().delete()
    cut_file = fetch_cut_file(reel, page.page_no, force_download=True)        
    try:
        print(page.pk)
        page.cut_info=cut_file
        page.save()
        cut_info_dict = json.loads(cut_file)
        pagerect = PageRect(page=page, reel=page.reel, rect_set=cut_info_dict['char_data'])
        pagerect.save()
        pagerect.rebuild_rect()
    except:
        logger.exception('rebuild_reel_pagerects_for_s3 failed.')
    task_no = "%s_%05X" % (schedule.schedule_no, PageTask().task_id())    
    task = PageTask.objects.create(number=task_no, schedule=schedule, ttype=SliceType.PPAGE, count=1, pagerect=pagerect,
                                  status=TaskStatus.NOT_GOT, page_set=[page.pk])
    #task.save()

def rebuild_reel_pagerects_for_s3(reel):
    schedule = Schedule.objects.filter(reels=reel).first()
    if schedule:
        for sched in Schedule.objects.filter(reels=reel):
            PageTask.objects.filter(schedule=sched).all().delete()
            PageVerifyTask.objects.filter(schedule=sched).all().delete()
            sched.delete()
    for page in reel.page_set.all():
        print(page.pk)
        Rect.objects.filter(page_pid=page.pk).all().delete()
        page.pagerects.all().delete()
        cut_file = fetch_cut_file(reel, page.page_no, force_download=True)
        
        try:
            page.cut_info=cut_file
            page.save()
            cut_info_dict = json.loads(cut_file)
            pagerect = PageRect(page=page, reel=page.reel, rect_set=cut_info_dict['char_data'])
            pagerect.save()
            pagerect.rebuild_rect()
        except:
            logger.exception('rebuild_reel_pagerects_for_s3 failed.')
    reel.image_ready = True
    reel.save(update_fields=['image_ready'])
    Schedule.create_reels_pptasks(reel)

def rebuild_reel_pagerects(reel):
    for page in reel.page_set.all():
        if Rect.objects.filter(page_pid=page.pk).first():
            continue
        print(page.pk)
        Rect.objects.filter(page_pid=page.pk).all().delete()
        page.pagerects.all().delete()

        try:
            cut_info_dict = json.loads(page.cut_info)
            pagerect = PageRect(page=page, reel=page.reel, rect_set=cut_info_dict['char_data'])
            pagerect.save()
            pagerect.rebuild_rect()
        except:
            logger.exception('rebuild_reel_pagerects error.')
    reel.image_ready = True
    reel.save(update_fields=['image_ready'])
    Schedule.create_reels_pptasks(reel)

def compute_accurate_cut(reel, process_cut=True):
    use_original_cut = reel.sutra.tripitaka.use_original_cut
    sid = reel.sutra.sid
    pagetexts = []
    if not use_original_cut:
        try:
            reel_ocr_text = ReelOCRText.objects.get(reel_id = reel.id)
        except:
            return None
        pagetexts = reel_ocr_text.text[2:].split('\np\n')
    reel_correct_text = ReelCorrectText.objects.filter(reel=reel).order_by('-id').first()
    correct_pagetexts = []
    if reel_correct_text:
        text = reel_correct_text.text
        if text[:2] == 'p\n':
            text = text[2:]
        correct_pagetexts = text.split('\np\n')
    page_count = reel.end_vol_page - reel.start_vol_page + 1
    correct_page_count = len(correct_pagetexts)

    reel.page_set.all().delete()
    for i in range(page_count):
        page_no = i + 1
        vol_page = reel.start_vol_page + i
        # 最后一位是栏号，如果有分栏，需用a/b；无分栏，用0
        pid = '%s_%03d_%02d_%s' % (sid, reel.reel_no, page_no, '0') # YB000860_001_01_0
        # 如果有分栏，最后一位是栏号，需用a/b；无分栏，为空
        page_code = '%s_%s_%s%s' % (sid[0:2], reel.path_str(), vol_page, '') # YB_1_1
        cut_file = fetch_cut_file(reel, vol_page)
        if i >= correct_page_count or not cut_file:
            use_original_cut = True
        if not use_original_cut:
            try:
                #print('vol_page: ', vol_page)
                #print('%s\n----------\n%s\n----------' % (correct_pagetexts[i], pagetexts[i]))
                char_lst, line_count, column_count, char_count_lst, cut_add_count, cut_wrong_count, cut_confirm_count = \
                get_accurate_cut(correct_pagetexts[i], pagetexts[i], cut_file, pid)
                min_x, min_y, max_x, max_y = get_char_region_cord(char_lst)
                cut_verify_count = cut_add_count + cut_wrong_count + cut_confirm_count
                cut_info = {
                    'page_code': page_code,
                    'min_x': min_x,
                    'min_y': min_y,
                    'max_x': max_x,
                    'max_y': max_y,
                    'char_data': char_lst,
                }
                cut_info_json = json.dumps(cut_info, indent=None)
                page = Page(pid=pid, reel_id=reel.id, reel_page_no=i+1, page_no=vol_page,
                text=correct_pagetexts[i], cut_info=cut_info_json, cut_updated_at=timezone.now(),
                cut_add_count=cut_add_count, cut_wrong_count=cut_wrong_count, cut_confirm_count=cut_confirm_count,
                cut_verify_count=cut_verify_count,
                page_code = page_code)
            except:
                logger.exception('get_accurate_cut failed: %s', pid)
                use_original_cut = True
        if use_original_cut:
            cut_info_json = cut_file
            char_count_lst = []
            line_count = 0
            column_count = 0
            if cut_file:
                cut_info = json.loads(cut_file)
                char_lst = cut_info['char_data']
                min_x, min_y, max_x, max_y = get_char_region_cord(char_lst)
                cut_info = {
                    'page_code': page_code,
                    'min_x': min_x,
                    'min_y': min_y,
                    'max_x': max_x,
                    'max_y': max_y,
                    'char_data': char_lst,
                }
            else:
                cut_info = {
                    'page_code': page_code,
                    'char_data': [],
                }
                cut_info_json = json.dumps(cut_info, indent=None)
                char_lst = []
            page = Page(pid=pid, reel_id=reel.id, reel_page_no=i+1, page_no=vol_page,
            cut_info=cut_info_json, cut_updated_at=timezone.now(),
            page_code=page_code)
            if correct_pagetexts and i < correct_page_count:
                page.text = correct_pagetexts[i]
        page.char_count_lst = json.dumps(char_count_lst, separators=(',', ':'))
        page.status = PageStatus.RECT_NOTREADY

        # 得到分列信息
        image_name_prefix = reel.image_prefix() + str(vol_page)
        img_path = reel.image_path()
        image_url = get_image_url(reel, vol_page)
        column_lst = gene_new_col(image_name_prefix, char_lst)
        page.bar_info = column_lst
        page.save()

        try:
            crop_col_online(img_path, image_url, column_lst)
        except:
            logger.exception('Crop image column failed.')
        columns = []
        for col in column_lst:
            column = Column(id = col['col_id'], page=page, x=col['x'], y=col['y'], x1=col['x1'], y1=col['y1'])
            columns.append(column)
        try:
            with transaction.atomic():
                Column.objects.bulk_create(columns)
        except:
            logger.exception('save Column failed.')

    # cut related
    if process_cut and not reel.cut_ready:
        rebuild_reel_pagerects(reel)

def create_pages_for_reel(reel):
    if reel.page_set.first(): # 已有page
        return
    sid = reel.sutra.sid
    page_count = reel.end_vol_page - reel.start_vol_page + 1
    pages = []
    for i in range(page_count):
        page_no = i + 1
        vol_page = reel.start_vol_page + i
        # 最后一位是栏号，如果有分栏，需用a/b；无分栏，用0
        pid = '%s_%03d_%02d_%s' % (sid, reel.reel_no, page_no, '0') # YB000860_001_01_0
        # 如果有分栏，最后一位是栏号，需用a/b；无分栏，为空
        page_code = '%s_%s_%s%s' % (sid[0:2], reel.path_str(), vol_page, '') # YB_1_1
        cut_info_json = fetch_cut_file(reel, vol_page)
        if type(cut_info_json) is bytes:
            cut_info_json = cut_info_json.decode()
        if not cut_info_json:
            cut_info = {
                'page_code': page_code,
                'char_data': [],
            }
            cut_info_json = json.dumps(cut_info, indent=None)
            char_lst = []
        else:
            cut_info = json.loads(cut_info_json)
            char_lst = cut_info['char_data']
        page = Page(pid=pid, reel_id=reel.id, reel_page_no=i+1, page_no=vol_page,
                    cut_info=cut_info_json, cut_updated_at=timezone.now(),
                    page_code=page_code)
        page.status = PageStatus.RECT_NOTREADY
        pages.append(page)
    Page.objects.bulk_create(pages)
    rebuild_reel_pagerects(reel)

SUTRA_CLEAN_PATTERN = re.compile('[「」　 \r]')
def clean_sutra_text(text):
    text = text.replace('\r\n', '\n').replace('\n\n', '\n')
    return SUTRA_CLEAN_PATTERN.sub('', text)

PUNCT_CHARACTERS = '：，。；、！“”‘’？\n'
def extract_punct(text):
    pos = 0
    punct_lst = []
    text_lst = []
    for ch in text:
        if ch in PUNCT_CHARACTERS:
            punct_lst.append( (pos, ch) )
        else:
            text_lst.append(ch)
            pos += 1
    return (punct_lst, ''.join(text_lst))

def judge_merge_text_punct(text, punct_lst):
    i = 0
    punct_idx = 0
    text_length = len(text)
    punct_lst_length = len(punct_lst)
    result_lst = []
    line = []
    while i < text_length and punct_idx < punct_lst_length:
        if punct_lst[punct_idx][0] <= i:
            s = punct_lst[punct_idx][1]
            if s == '\n':
                result_lst.append(''.join(line))
                line = []
            else:
                line.append(s)
            punct_idx += 1
        elif punct_lst[punct_idx][0] > i:
            line.append(text[i])
            i += 1
    return result_lst

def extract_page_line_separators(text):
    if text == '':
        return []
    text = text.replace('b\n', '')
    separators = []
    pos = 0
    for c in text:
        if c in 'p\n':
            separators.append( (pos, c) )
        else:
            pos += 1
    return separators

def extract_line_separators(text):
    if text == '':
        return []
    separators = []
    pos = 0
    for c in text:
        if c == '\n':
            separators.append( (pos, c) )
        elif c not in 'pb':
            pos += 1
    return separators

def get_reel_text(reel, force_download=False):
    pages = []
    for vol_page in range(reel.start_vol_page, reel.end_vol_page+1):
        data = fetch_cut_file(reel, vol_page, 'txt', force_download)
        if type(data) is bytes:
            data = data.decode()
        pages.append('p')
        pages.append(data)
    return '\n'.join(pages)

def get_reel_text_from_cut(reel, force_download=False):
    pages = []
    for vol_page in range(reel.start_vol_page, reel.end_vol_page+1):
        data = fetch_cut_file(reel, vol_page, 'cut', force_download)
        if not data:
            pages.append( 'p\n' )
            continue
        json_data = json.loads(data)
        chars = ['p']
        last_line_no = 0
        last_char_no = 0
        last_x = 0
        avg_x = 0
        total_x = 0
        for char_data in json_data['char_data']:
            line_no = int(char_data['line_no'])
            char_no = int(char_data['char_no'])
            x = char_data['x']
            w = char_data['w']
            if line_no != last_line_no:
                chars.append('\n')
                if last_line_no:
                    avg_x = total_x / last_char_no
                    total_x = 0
                    if (x - avg_x) > 5*w:
                        chars.append('b\n')
                last_char_no = 0
            total_x += x
            if char_no != last_char_no + 1:
                logger.error('%s char_no error: %d, %d, %d, %d', reel, reel.reel_no, vol_page, line_no, char_no)
                last_line_no = 0
                chars = ['p']
                break
            chars.append(char_data['ch'])
            last_line_no = line_no
            last_char_no = char_no
        pages.append( ''.join(chars) )
    return '\n'.join(pages)

def clean_separators(text):
    return SEPARATORS_PATTERN.sub('', text)

#JIAZHU_PATTERN = re.compile('<[^\n]*>')
JIAZHU_PATTERN = re.compile('[<>]')
def clean_jiazhu(text):
    return JIAZHU_PATTERN.sub('', text)
