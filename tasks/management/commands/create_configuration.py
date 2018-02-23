from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from tdata.models import Configuration

import os, sys
from os.path import isfile, join
import traceback

class Command(BaseCommand):
    def handle(self, *args, **options):
        filename = '%s/data/variant.txt' % settings.BASE_DIR
        with open(filename, 'r', encoding='utf-8') as f:
            variant = f.read()

        config = Configuration.objects.first()
        if config is None:
            config = Configuration(id=1)
        config.variant = variant
        config.save()