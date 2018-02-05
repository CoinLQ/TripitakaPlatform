from django.core.cache import cache
import functools
from rect.models import TaskStatus, CCTask, ClassifyTask, PageTask, DelTask, AbsentTask



def redis_lock(method):
    @functools.wraps(method)
    def lock(*args, **kw):
        with cache.lock(method.__name__):
            result = method(*args, **kw)
        return result
    return lock


@redis_lock
def retrieve_cctask(user):
    return retrieve_task(CCTask, user)


@redis_lock
def retrieve_classifytask(user):
    return retrieve_task(ClassifyTask, user)


@redis_lock
def retrieve_pagetask(user):
    return retrieve_task(PageTask, user)

@redis_lock
def retrieve_deltask(user):
    return retrieve_task(DelTask, user)

@redis_lock
def retrieve_absenttask(user):
    return retrieve_task(AbsentTask, user)



def retrieve_task(task_class, user):
    current = task_class.objects.filter(owner=user, status=TaskStatus.HANDLING).first()
    if not current:
        current = task_class.objects.filter(status__lt=TaskStatus.HANDLING).order_by('priority').first()
        current and current.obtain(user)
    return current