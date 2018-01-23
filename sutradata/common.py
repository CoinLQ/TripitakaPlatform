from difflib import SequenceMatcher
import re, json
import urllib.request
import traceback

def get_accurate_cut(text1, text2, cut_json, pid):
    """
    用于文字校对后的文本比对，text1是文字校对审定后得到的精确本，text2是OCR原始结果，都包含换行和换页标记。
    """
    cut = json.loads(cut_json)
    old_char_lst = cut['char_data']
    old_char_lst_length = len(old_char_lst)
    for char_data in old_char_lst:
        char_data['line_no'] = int(char_data['char_id'][18:20])
        char_data['char_no'] = int(char_data['char_id'][21:23])

    char_lst = []

    line_no = 1
    char_no = 1
    char_index = 0 # 下一个从old_char_lst要取出的字
    char_lst_length = 0
    opcodes = SequenceMatcher(None, text1, text2, False).get_opcodes()
    for tag, i1, i2, j1, j2 in opcodes:
        if tag == 'equal':
            i = i1
            while i < i2:
                if text1[i] == '\n':
                    line_no += 1
                    char_no = 1
                else:
                    char_data = old_char_lst[char_index]
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
            while i < i2:
                ch = text1[i]
                if ch == '\n':
                    line_no += 1
                    char_no = 1
                else:
                    if (i-i1)+j1 < j2:
                        #print('char_index: ', char_index)
                        char_data = old_char_lst[char_index]
                        char_index += 1
                        char_data['line_no'] = line_no
                        char_data['char_no'] = char_no
                        char_data['char'] = ch
                        char_data['old_char'] = text2[(i-i1)+j1]
                    else:
                        char_data = {
                            'line_no': line_no,
                            'char_no': char_no,
                            'char': ch,
                            'added': 1,
                        }
                    char_lst.append(char_data)
                    char_no += 1
                i += 1
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
                        'char': ch,
                        'added': 1,
                    }
                    char_lst.append(char_data)
                    char_no += 1

    # 给增加的字加上切分坐标
    line_count = 0
    char_map = {}
    line_char_count = {}
    for char_data in char_lst:
        line_no = char_data['line_no']
        char_no = char_data['char_no']
        line_char_str = '%02dn%02d' % (line_no, char_no)
        cid = '%s%s' % (pid, line_char_str)
        #char_data['char_id'] = cid
        if 'char_id' in char_data:
            del char_data['char_id']
        char_map[line_char_str] = char_data
        if line_no in line_char_count:
            line_char_count[line_no] += 1
        else:
            line_char_count[line_no] = 1
        if line_no > line_count:
            line_count = line_no

    add_count = 0
    wrong_count = 0
    confirm_count = 0
    for char_data in char_lst:
        if 'old_char' in char_data:
            wrong_count += 1
        elif 'need_confirm' in char_data:
            confirm_count += 1
        elif 'added' in char_data:
            try:
                line_no = char_data['line_no']
                char_no = char_data['char_no']
                prev_line_no = line_no - 1
                next_line_no = line_no + 1
                cur_line_char_count = line_char_count[line_no]
                s = None
                if line_char_count.get(prev_line_no, 0) == cur_line_char_count:
                    s = '%02dn%02d' % (prev_line_no, char_no)
                elif line_char_count.get(next_line_no, 0) == cur_line_char_count:
                    s = '%02dn%02d' % (next_line_no, char_no)
                if not s:
                    if prev_line_no > 0:
                        s = '%02dn%02d' % (prev_line_no, char_no)
                    else:
                        s = '%02dn%02d' % (next_line_no, char_no)
                char_data['y'] = char_map[s]['y']
                char_data['h'] = char_map[s]['h']

                if char_no == 1:
                    s = '%02dn%02d' % (line_no, char_no + 1)
                else:
                    s = '%02dn%02d' % (line_no, char_no - 1)
                if s in char_map and 'x' in char_map[s]:
                    char_data['x'] = char_map[s]['x']
                    char_data['w'] = char_map[s]['w']
                else:
                    s1 = '%02dn%02d' % (line_no - 1, char_no)
                    s2 = '%02dn%02d' % (line_no + 1, char_no)
                    if char_map[s1]['x'] - char_map[s2]['x'] < 200:
                        char_data['x'] = (char_map[s1]['x'] + char_map[s2]['x'])/2
                        char_data['w'] = (char_map[s1]['w'] + char_map[s2]['w'])/2
            except:
                print('get_accurate_cut except: ', json.dumps(char_data))

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
    return char_lst, add_count, wrong_count, confirm_count, min_x, min_y, max_x, max_y

def fetch_cut_file(pid):
    t_code = pid[:2]
    s_code = pid[2:8]
    volstr = pid[8:12]
    url = 'https://s3.cn-north-1.amazonaws.com.cn/lqcharacters-images/%s/%s/%s/%s.cut' % (t_code, s_code, volstr, pid)
    with urllib.request.urlopen(url) as f:
        data = f.read()
        return data

SUTRA_CLEAN_PATTERN = re.compile('[「」　 \r]')
def clean_sutra_text(text):
    text = text.replace('\r\n', '\n').replace('\n\n', '\n')
    return SUTRA_CLEAN_PATTERN.sub('', text)

PUNCT_CHARACTERS = '：，。；、\n'
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