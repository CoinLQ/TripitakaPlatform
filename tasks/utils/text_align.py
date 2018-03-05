from tdata.models import Reel
from tasks.models import ReelCorrectText

from difflib import SequenceMatcher

def get_sutra_body_text(sutra):
    body_lst = []
    for reel in Reel.objects.filter(sutra=sutra).order_by('reel_no'):
        reel_correct_text = ReelCorrectText.objects.filter(reel=reel).order_by('-id').first()
        body_lst.append(reel_correct_text.body)
    return '\n\n'.join(body_lst)

def get_align_pos(text1, text2):
    opcodes = SequenceMatcher(lambda x: x in 'pb\n', text1, text2, False).get_opcodes()
    opcode_cnt = len(opcodes)
    start_index = 0
    end_index = len(text1)

    for i in range(0, opcode_cnt-1):
        tag, i1, i2, j1, j2 = opcodes[i]
        if tag == 'delete' and (i2 - i1) >= 30:
            start_index = i2
        elif tag == 'replace' and (i2 - i1) - (j2 - j1) >= 30:
            start_index = i2
        elif tag == 'equal' and (i2 - i1) >= 20:
            break
    for i in range(opcode_cnt-1, 0, -1):
        tag, i1, i2, j1, j2 = opcodes[i]
        if tag == 'delete' and (i2 - i1) >= 30:
            end_index = i1
        elif tag == 'replace' and (i2 - i1) - (j2 - j1) >= 30:
            end_index = i1
        elif tag == 'equal' and (i2 - i1) >= 20:
            break
    return (start_index, end_index)


