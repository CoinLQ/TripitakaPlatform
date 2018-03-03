
from difflib import SequenceMatcher
from tasks.models import Punct, LQPunct
from tdata.models import Sutra, Tripitaka, Reel
from tasks.common import clean_separators
from .text_align import get_align_pos
# from tasks.models import ReelCorrectText
import json
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
"""

"""

class PunctProcess(object):

    def nearest_rejust(self, sparses, pos):
        offset = 0
        for idx, mark in enumerate(sparses):
            if pos < mark['idx']:
                break
            offset = mark["offset"]
        if (offset == 0):
            offset = sparses[0]["offset"]
        return offset

    def gen_sparses(self, base, compare):
        opcodes = SequenceMatcher(None, base, compare, False).get_opcodes()
        offset = 0
        sparses = []
        filter_ranges = []
        for tag, i1, i2, j1, j2 in opcodes:
            #print('{:7}   base[{}:{}] --> compare[{}:{}] {!r:>8} --> {!r}'.format(
            #    tag, i1, i2, j1, j2, base[i1:i2], compare[j1:j2]))
            offset = offset - ((i2-i1)-(j2-j1))
            sparses.append({"idx": j2, "offset": offset})
            if tag == 'delete':
                # print('{:7}   base[{}:{}] --> compare[{}:{}] {!r:>8} --> {!r}'.format(
                #     tag, i1, i2, j1, j2, base[i1:i2], compare[j1:j2]))
                filter_ranges.append( (i1, i2) )
        return sparses, filter_ranges

    def new_puncts(self, base_reel_text, base_puncts, new_reel_text):
        sparses, filter_ranges = self.gen_sparses(base_reel_text, new_reel_text)
        new_base_puncts = []
        for punct in base_puncts:
            pos = punct[0]
            add = True
            for filter_range in filter_ranges:
                if pos > filter_range[0] and pos < filter_range[1]:
                    add = False
                    break
            if add:
                new_base_puncts.append(punct)
        new_puncts = list(map(lambda x: [x[0]+self.nearest_rejust(sparses,x[0]), x[1]], new_base_puncts))
        return new_puncts

    def reel_align_punct(self, base_reel_text, base_puncts, new_reel_text):
        new_puncts = self.new_puncts(base_reel_text, base_puncts, new_reel_text)
        begin=0
        result_text = ''
        for punct in new_puncts:
            if punct[0] < 0:
                continue
            result_text += "%s%s" % (new_reel_text[begin: punct[0]], punct[1])
            begin = punct[0]
        result_text += new_reel_text[begin:]
        return result_text

    def output_punct_texts(self, new_puncts, new_reel_text):
        begin=0
        result_text = ''
        for punct in new_puncts:
            if punct[0] < 0:
                continue
            result_text += "%s%s" % (new_reel_text[begin: punct[0]], punct[1])
            begin = punct[0]
        result_text += new_reel_text[begin:]
        return result_text

    def body_punct(self, base_reel_text, head_text, tail_text, puncts):
        _puncts = filter(lambda a: a[0]> len(head_text), puncts)
        
        tail_pos = len(base_reel_text)-len(tail_text)
        new_puncts = list(filter(lambda a: a[0]<= tail_pos, _puncts))
        for punct in new_puncts:
            punct[0] = punct[0] - len(head_text)
        return new_puncts

    def get_sutra_body_text_and_puncts(self, sutra):
        body_lst = []
        punct_lst = []
        for reel in Reel.objects.filter(sutra=sutra).order_by('reel_no'):
            reel_correct_text = reel.reel_correct_texts.order_by('-id').first()
            punct_lst.append(json.loads(Punct.objects.filter(reeltext=reel_correct_text).first().body_punctuation))
            body_lst.append(clean_separators(reel_correct_text.body))
        puncts = PunctProcess.combined_punct(punct_lst)
        return [''.join(body_lst) , puncts]

    @staticmethod
    def combined_punct(puncts_group):
        end_pos = 0
        page = 0
        current_pos = 0
        for n, puncts in enumerate(puncts_group):
            end_pos = current_pos
            for punct in puncts:
                punct[0] = punct[0] + end_pos
                current_pos = punct[0]
        flatten_puncts = [item for sublist in puncts_group for item in sublist]
        return flatten_puncts

    @staticmethod
    def create_new(reel, newtext):
        '''
        增加新的标点信息
        '''
        sutra_cb = Sutra.objects.get(lqsutra=reel.sutra.lqsutra, tripitaka=Tripitaka.objects.get(code='CB'))
        body_and_puncts = PunctProcess().get_sutra_body_text_and_puncts(sutra_cb)
        body_text = clean_separators(body_and_puncts[0])
        puncts = body_and_puncts[1]
        pos_pair = get_align_pos(body_text, newtext)
        aligned_puncts = list(filter(lambda n: n[0] >= pos_pair[0] and n[0] <= pos_pair[1], puncts))
        reel_align_text = body_text[pos_pair[0]:pos_pair[1]]
        PunctProcess().output_punct_texts(aligned_puncts, reel_align_text)
        # 这里找的CBETA来源的标点
        try:
            _puncts = PunctProcess().new_puncts(reel_align_text, aligned_puncts, clean_separators(newtext))
            task_puncts = json.dumps(_puncts, separators=(',', ':'))
            #PunctProcess().output_punct_texts(_puncts, newtext)
            return task_puncts
        except:
            return '[]'

@receiver(pre_save, sender=Punct)
@receiver(pre_save, sender=LQPunct)
def update_body_punctuation_fields(sender, instance, **kwargs):
    punctuation = json.loads(instance.punctuation)
    body_puncts = PunctProcess().body_punct(clean_separators(instance.reeltext.text), clean_separators(instance.reeltext.head), clean_separators(instance.reeltext.tail), punctuation)
    instance.body_punctuation = json.dumps(body_puncts, separators=(',', ':'))
