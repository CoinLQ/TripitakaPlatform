from django.core.management.base import BaseCommand, CommandError
from sutradata.models import Tripitaka, LQSutra, Sutra

import os, sys
from os.path import isfile, join
import traceback

class Command(BaseCommand):
    def read_sutra_list(self, sutra_list_file, tripitaka_code):
        print('process: %s' % sutra_list_file)
        with open(sutra_list_file, 'r') as f:
            heads = f.readline().strip().split('\t')
            try:
                name_idx = heads.index('实体经名')
            except ValueError:
                try:
                    name_idx = heads.index('實體經名')
                except:
                    name_idx = heads.index('经文名称')
            code_idx = 3 - name_idx
            for line in f.readlines():
                try:
                    line = line.rstrip().replace('—', '-')
                    params = line.split('\t')
                    lqcode = params[0]
                    code = params[code_idx]
                    name = params[name_idx]
                    if name != '大方廣佛華嚴經':
                        continue
                    if len(params) >= 5:
                        total_reels_1 = params[3]
                        total_reels_2 = params[4]
                    else:
                        total_reels_1 = '0'
                        total_reels_2 = '0'
                    if len(lqcode) == 0 or len(code) == 0 or \
                    lqcode == '#N/A' or code == '#N/A' or name == '#N/A':
                        print('EXCEPT: %s' % line)
                        continue
                    lqcode = lqcode[2:]
                    lqvariant_code = 0
                    if '-' in lqcode:
                        pos = lqcode.find('-')
                        lqvariant_code = lqcode[pos+1:]
                        lqvariant_code_num = int(lqvariant_code)
                        if lqvariant_code_num >= 10:
                            lqvariant_code = chr( (lqvariant_code_num - 10) + ord('a') )
                        lqcode = lqcode[:pos]
                    lqcode = int(lqcode)

                    code = code.lstrip('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
                    variant_code = 0
                    if '-' in code:
                        pos = code.find('-')
                        variant_code = code[pos+1:]
                        variant_code_num = int(variant_code)
                        if variant_code_num >= 10:
                            variant_code = chr( (variant_code_num - 10) + ord('a') )
                        code = code[:pos]
                    code = int(code)
                    try:
                        total_reels = int(total_reels_2)
                    except:
                        total_reels = 0
                    lqcode_str = 'LQ%05d%s' % (lqcode, lqvariant_code)
                    lqsutra = LQSutra(sid=lqcode_str, name=name, total_reels=total_reels)
                    lqsutra.save()
                    tripitaka = Tripitaka.objects.get(pk=tripitaka_code)
                    code_str = '%05d' % code
                    sutra = Sutra(sid='%s%s%s' % (tripitaka_code, code_str, variant_code),
                    tripitaka=tripitaka, code=code_str, variant_code=variant_code,
                    name=name, lqsutra=lqsutra, total_reels=total_reels)
                    sutra.save()
                except Exception:
                    print(line)
                    traceback.print_exc()
                    continue
                    #sys.exit(-1)

    def handle(self, *args, **options):
        dirpath = "data/sutra_list/"
        files = []
        for filename in os.listdir(dirpath):
            fullname = join(dirpath, filename)
            if isfile(fullname):
                ext = filename[-3:]
                if ext != 'csv':
                    continue
                tripitaka_code = filename[:2]
                self.read_sutra_list(fullname, tripitaka_code)