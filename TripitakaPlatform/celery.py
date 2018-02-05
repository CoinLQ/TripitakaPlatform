from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings
from functools import wraps
import socket
import traceback
from django.core.mail import send_mail

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cutrect.settings')

app = Celery('cutrect')

app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

"""

@shared_task(ignore_result=True)
@email_if_fails
def dummy_test(**kwargs):
    raise

"""
def email_if_fails(fn):
    @wraps(fn)
    def decorated(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except:
            if not settings.DEBUG:
                try:
                    fnName = fn.func_name
                except AttributeError:
                    fnName = fn.__name__
                send_error_email(fnName, args, kwargs, socket.gethostname(),
                                 traceback.format_exc())
            raise
    return decorated


def send_error_email(fnName, args, kwargs, host, formatted_exc):
    formatted_exc = formatted_exc.strip()
    contents = (
        "Task: {fnName}\nArgs: {args}\nKwargs: {kwargs}\nHost: {host}\n"
        "Error: {error}".format(
            fnName=fnName,
            args=args,
            kwargs=kwargs,
            host=host,
            error=formatted_exc,
        ))
    short_exc = formatted_exc.rsplit('\n')[-1]
    subject = '[celery-error] {host} {fnName} {short_exc}'.format(
        host=host,
        fnName=fnName,
        short_exc=short_exc,
    )
    send_mail(subject, contents, settings.EMAIL_HOST_USER, [email for _, email in settings.ADMINS],
             fail_silently=False,)

