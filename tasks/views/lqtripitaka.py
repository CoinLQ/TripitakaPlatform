from django.shortcuts import get_object_or_404, render, redirect
import json
from django.http import JsonResponse
from ..task_controller import create_tasks_for_lqreels_async, create_tasks_for_reels_async, create_tasks_for_reels

def index(request):
    return render(request, 'tasks/lqtripitaka.html')

def do_generate_task(request):
    if request.user and request.user.is_admin:
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
    else:
        return JsonResponse({'没有权限发布任务'})

def process_judgefeedback(request, judgefeedback_id):
    return render(request, 'tasks/judge_feedback.html', {'judgefeedback_id': judgefeedback_id})

def view_judgefeedback(request, judgefeedback_id):
    return render(request, 'tasks/view_judge_feedback.html', {'judgefeedback_id': judgefeedback_id})

def process_lqpunctfeedback(request, lqpunctfeedback_id):
    return render(request, 'tasks/punct_feedback.html', {'lqpunctfeedback_id': lqpunctfeedback_id})

def view_lqpunctfeedback(request, lqpunctfeedback_id):
    return render(request, 'tasks/view_punct_feedback.html', {'lqpunctfeedback_id': lqpunctfeedback_id})