from django.shortcuts import get_object_or_404, render, redirect
from tdata.models import *
from tdata.lib.image_name_encipher import get_image_url
from tasks.models import *


def do_mark_task(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    if task.typ == Task.TYPE_MARK:
        mark_task_ids = []
    elif task.typ in [Task.TYPE_MARK_VERIFY]:
        mark_task_ids = []
    else:
        return redirect('/')
    context = {
        'task': task,
        }
    return render(request, 'tasks/do_mark_task.html', context)


def process_judgefeedback(request, judgefeedback_id):
    return render(request, 'tasks/judge_feedback.html', {'judgefeedback_id': judgefeedback_id})
