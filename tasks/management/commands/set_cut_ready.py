from django.core.management.base import BaseCommand, CommandError
from django.contrib import auth
from jwt_auth.models import Staff
from tdata.models import *
from tasks.models import *
from tasks.common import *

import TripitakaPlatform.settings

import os, sys
from os.path import isfile, join
import traceback

import re, json

class Command(BaseCommand):
    def handle(self, *args, **options):
        BASE_DIR = settings.BASE_DIR
        tcode_lst = ['YB', 'QL', 'ZH', 'QS', 'GL', 'SX', 'ZC', 'PL', 'LC']
        Tripitaka.objects.all().update(cut_ready=False)
        Tripitaka.objects.filter(code__in=tcode_lst).update(cut_ready=True)