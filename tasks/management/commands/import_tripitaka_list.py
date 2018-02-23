from django.core.management.base import BaseCommand, CommandError
from tdata.models import Tripitaka

import os, sys
from os.path import isfile, join
import traceback

class Command(BaseCommand):
    def handle(self, *args, **options):
        with open('data/tripitaka_list.txt', 'r', encoding='utf-8') as f:
            for line in f.readlines():
                code, name, shortname = line.rstrip().split()
                tripitaka = Tripitaka(code=code, name=name, shortname=shortname)
                tripitaka.save()