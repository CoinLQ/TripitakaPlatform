from tasks.models import Configuration

class VariantManager(object):
    def __init__(self):
        self.variant_map = None

    def load_variant_map(self, text=''):
        if self.variant_map:
            return
        ch_set = set(text)
        variant_conf = Configuration.objects.filter(code='variant').first()
        variant = variant_conf.value
        variant_map = {}
        for line in variant.split('\n'):
            line = line.strip()
            if not line:
                continue
            map_ch = line[0]
            if ch_set:
                for ch in line[1:]:
                    if ch in ch_set:
                        map_ch = ch
                        break
            for ch in line:
                variant_map[ch] = map_ch
        self.variant_map = variant_map

    def replace_variant(self, text):
        ch_lst = [self.variant_map.get(ch, ch) for ch in text]
        new_text = ''.join(ch_lst)
        return new_text