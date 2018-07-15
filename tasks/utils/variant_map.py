from tdata.models import Configuration

class VariantManager(object):
    def __init__(self):
        self.variant_map = None

    def load_variant_map(self, text=''):
        """每一行都是一组异体字
        下𠄟丅
        上丄
        亥𢁳𠀅𠦇
        衛𠀄卫衞䘙
        丈𠀋
        丑丒𠃠
        """
        if self.variant_map:
            return
        ch_set = set(text)
        config = Configuration.objects.first()
        variant_map = {}
        for line in config.variant.split('\n'):
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
