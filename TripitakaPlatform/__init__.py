from .celery import app as celery_app
from .celery import email_if_fails

__all__ = ['celery_app', 'email_if_fails']