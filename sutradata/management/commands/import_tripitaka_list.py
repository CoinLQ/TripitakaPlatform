from django.core.management.base import BaseCommand, CommandError
from sutradata.models import Tripitaka #, LQSutra, Sutra

import os, sys
from os.path import isfile, join
import traceback

class Command(BaseCommand):
    def handle(self, *args, **options):
        with open('data/tripitaka_list.txt', 'r') as f:
            for line in f.readlines():
                name, code = line.rstrip().split()
                tripitaka = Tripitaka(code=code, name=name)
                tripitaka.save()