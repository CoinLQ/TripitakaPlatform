from django.shortcuts import get_object_or_404, render, redirect
from sutradata.models import *
from tasks.models import *

def do_judge_task(request, task_id):
    return render(request, 'tasks/do_judge_task.html', {'task_id': task_id})

def do_judge_verify_task(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    judge_task_ids = [ judge_task.id for judge_task in \
    Task.objects.filter(batch_task_id=task.batch_task_id, lqreel_id=task.lqreel.id, typ=Task.TYPE_JUDGE).order_by('task_no') ]
    return render(request, 'tasks/do_judge_verify_task.html', {'task_id': task_id, 'judge_task_ids': judge_task_ids})