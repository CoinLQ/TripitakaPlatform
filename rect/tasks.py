# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from django.contrib.contenttypes.models import ContentType
from rect.lib.gen_task import allocateTasks
from rect.models import *
from TripitakaPlatform import celery_app, email_if_fails
import os
import logging
from django.dispatch import receiver
from django.db import models




@shared_task(ignore_result=True)
@email_if_fails
def dummy_test(**kwargs):
    log = logging.getLogger()

    log.debug("Debug DUMMY TEST")
    log.info("Info DUMMY TEST")
    log.warning("Warning DUMMY TEST")
    log.error("Error DUMMY TEST")
    log.critical("Critical DUMMY TEST")
    Schedule.objects.get(id=9999999)
