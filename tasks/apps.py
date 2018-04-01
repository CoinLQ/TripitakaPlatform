from django.apps import AppConfig


class TasksConfig(AppConfig):
    name = 'tasks'
    verbose_name = u'校勘业务管理'

    def ready(self):
        from tasks import serializers
        pass
