from django.core.management.base import BaseCommand, CommandError
from django.contrib import auth
from jwt_auth.models import Staff
from tdata.models import *
from tasks.models import *
from tasks.common import *
from tasks.task_controller import create_tasks_for_batchtask

import TripitakaPlatform.settings

import os, sys
from os.path import isfile, join
import traceback

import re, json

class Command(BaseCommand):
    def handle(self, *args, **options):
        BASE_DIR = settings.BASE_DIR
        
        variant_map = {}
        with open(BASE_DIR + '/data/variant.txt', 'r') as f:
            lines = f.readlines()
        for line in lines:
            line = line.rstrip('\n')
            map_ch = line[0]
            ch_set = variant_map.setdefault(map_ch, set())
            for ch in line[1:]:
                ch_set.add(ch)
        with open(BASE_DIR + '/data/variant_converted.txt', 'w') as f:
            for map_ch, ch_set in variant_map.items():
                line = '%s%s\n' % (map_ch, ''.join(list(ch_set)))
                f.write(line)
        
