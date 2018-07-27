from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from tasks.models import Configuration

import os, sys
from os.path import isfile, join
import traceback

class Command(BaseCommand):
    def handle(self, *args, **options):
        task_timeout = 86400*7
        config = Configuration(code='task_timeout', key='校勘任务自动回收时间（秒）', value=str(task_timeout))
        config.save()
        filename = '%s/data/variant.txt' % settings.BASE_DIR
        with open(filename, 'r', encoding='utf-8') as f:
            variant = f.read()
        config = Configuration(code='variant', key='异体字列表', value=variant)
        config.save()