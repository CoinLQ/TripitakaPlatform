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
        ch_set_list = []
        next_index = 0
        
        for line in lines:
            line = line.rstrip('\n')
            index = None
            added_ch = ''
            for ch in line:
                index = variant_map.get(ch, None)
                if index is not None:
                    added_ch = ch
                    break
            if index is None:
                ch_set_list.append(set())
                index = next_index
                next_index += 1
            for ch in line:
                if ch != added_ch and ch not in variant_map:
                    variant_map[ch] = index
                    ch_set_list[index].add(ch)
        with open(BASE_DIR + '/data/variant_converted.txt', 'w') as f:
            for ch_set in ch_set_list:
                line = '%s\n' % ''.join(list(ch_set))
                f.write(line)
        
