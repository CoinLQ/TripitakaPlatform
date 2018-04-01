from django.core.management.base import BaseCommand, CommandError
from django.contrib.contenttypes.models import ContentType
from xadmin.models import Bookmark
from jwt_auth.models import Staff
from tasks.models import Task

import os, sys
import traceback

class Command(BaseCommand):
    def handle(self, *args, **options):
        admin = Staff.objects.get(username='admin')
        task_content_type = ContentType.objects.get_for_model(Task)
        url_name = 'xadmin:tasks_task_changelist'
        for typ, title in list(Task.TYPE_CHOICES):
            query = '_p_typ__exact=%d' % typ
            if typ in [Task.TYPE_CORRECT, Task.TYPE_CORRECT_VERIFY, Task.TYPE_PUNCT, Task.TYPE_PUNCT_VERIFY]:
                query += '&_cols=batchtask.tripitaka_name.sutra_name.reel_no.priority.task_no.realtime_progress.status.publisher.created_at.picker.picked_at.finished_at.modify'
            else:
                query += '&_cols=batchtask.lqsutra_name.base_reel_name.reel_no.priority.task_no.realtime_progress.status.publisher.created_at.picker.picked_at.finished_at.modify'
            bookmark = Bookmark(
                content_type=task_content_type,
                title=title, user=admin, query=query,
                is_share=True, url_name=url_name)
            bookmark.save()