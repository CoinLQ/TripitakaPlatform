from django.shortcuts import get_object_or_404, render, redirect
from tdata.models import *
from tasks.models import *

def do_judge_task(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    if task.typ != Task.TYPE_JUDGE:
        return redirect('/')
    return render(request, 'tasks/do_judge_task.html', {'task_id': task_id})

def do_judge_verify_task(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    if task.typ != Task.TYPE_JUDGE_VERIFY:
        return redirect('/')
    judge_task_ids = [ judge_task.id for judge_task in \
    Task.objects.filter(batch_task_id=task.batch_task_id, lqreel_id=task.lqreel.id, typ=Task.TYPE_JUDGE).order_by('task_no') ]
    return render(request, 'tasks/do_judge_verify_task.html', {'task_id': task_id, 'judge_task_ids': judge_task_ids})

def sutra_page_detail(request, pid):
    page = get_object_or_404(Page, pid=pid)
    reel = page.reel
    vol_page = reel.start_vol_page + page.reel_page_no - 1
    image_url = '%s%s%s.jpg' % (settings.IMAGE_URL_PREFIX, reel.url_prefix(), vol_page)
    char_pos = request.GET.get('char_pos', '')
    s = char_pos[-5:]
    try:
        line_no = int(s[0:2])
        char_no = int(s[3:])
    except:
        return redirect('/')
    context = {
        'page': page,
        'image_url': image_url,
        'line_no': line_no,
        'char_no': char_no,
    }
    return render(request, 'tasks/sutra_page_detail.html', context)