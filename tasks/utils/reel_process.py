
from difflib import SequenceMatcher

"""

"""

class ReelProcess(object):

    def nearest_rejust(self, sparses, pos):
        offset = 0
        for idx, mark in enumerate(sparses):
            if pos < mark['idx']:
                break
            offset = mark["offset"]
        return offset

    def gen_sparses(self, base, compare):
        opcodes = SequenceMatcher(None, base, compare, False).get_opcodes()
        offset = 0
        sparses = []
        for tag, i1, i2, j1, j2 in opcodes:
            print('{:7}   base[{}:{}] --> compare[{}:{}] {!r:>8} --> {!r}'.format(
                tag, i1, i2, j1, j2, base[i1:i2], compare[j1:j2]))
            offset = offset - ((i2-i1)-(j2-j1))
            sparses.append({"idx": j2, "offset": offset})
        return sparses

    def new_puncts(self, base_reel_text, base_puncts, new_reel_text):
        sparses = self.gen_sparses(base_reel_text, new_reel_text)
        new_puncts = list(map(lambda x: [x[0]+self.nearest_rejust(sparses,x[0]), x[1]], base_puncts))
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