from django.shortcuts import get_object_or_404, render, redirect
import json
from django.http import JsonResponse
from ..task_controller import create_tasks_for_lqreels_async, create_tasks_for_reels_async, create_tasks_for_reels


def index(request):
    return render(request, 'tasks/lqtripitaka.html')

def generate_task(request):
    return render(request, 'tasks/do_generate_task.html')

def do_generate_task(request):
    task_para = json.loads(request.body)['paras']
    if task_para['lqdzj']:
        create_tasks_for_lqreels_async(
            json.dumps(task_para['reel_lst']),
            correct_times=task_para['correct_times'],
            correct_verify_times=task_para['correct_verify_times'],
            judge_times=task_para['judge_times'],
            judge_verify_times=task_para['judge_verify_times'],
            punct_times=task_para['punct_times'],
            punct_verify_times=task_para['punct_verify_times'],
            lqpunct_times=task_para['lqpunct_times'],
            lqpunct_verify_times=task_para['lqpunct_verify_times'],
            mark_times=task_para['mark_times'],
            mark_verify_times=task_para['mark_verify_times']
        )
    else:
        create_tasks_for_reels_async(
            json.dumps(task_para['reel_lst']),
            correct_times=task_para['correct_times'],
            correct_verify_times=task_para['correct_verify_times'],
            mark_times=task_para['mark_times'],
            mark_verify_times=task_para['mark_verify_times']
        )
    return JsonResponse({}, status=200)