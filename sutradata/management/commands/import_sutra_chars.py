from django.core.management.base import BaseCommand, CommandError
from sutradata.models import Tripitaka, LQSutra, Sutra, Character

import os, sys
from os.path import isfile, join

class Command(BaseCommand):
    def handle(self, *args, **options):
        dirpath = "data/sutra_chars/"
        files = []
        for filename in os.listdir(dirpath):
            fullname = join(dirpath, filename)
            if isfile(fullname):
                pos = filename.find('.')
                pos2 = filename.find('_')
                sid = filename[:pos2]
                #reel_no = filename[pos2+1:pos]
                with open(fullname, 'r') as f:
                    for line in f.readlines():
                        ch, reel_no, vol_no, page_no, bar_no, line_no, char_no = line.rstrip().split('\t')
                        vol_no = int(vol_no)
                        page_no = int(page_no)
                        line_no = int(line_no)
                        char_no = int(char_no)
                        cid = '%sv%03dp%04da%02dn%02d' % (sid, vol_no, page_no, line_no, char_no)
                        sutra = Sutra.objects.get(pk=sid)
                        character = Character(cid=cid, sutra=sutra, reel_no=reel_no, vol_no=vol_no,
                        page_no=page_no, line_no=line_no, char_no=char_no, ch=ch)
                        character.save()