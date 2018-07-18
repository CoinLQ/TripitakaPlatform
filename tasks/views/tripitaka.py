from django.shortcuts import get_object_or_404, render, redirect
from django.conf import settings
from tdata.models import Reel

def index(request, tcode):
    try:
        reel_id = int(request.GET.get('reel_id'))
        reel = Reel.objects.get(id=reel_id)
        sutra_id = reel.sutra_id
    except:
        reel_id = -1
        sutra_id = -1
    return render(request, 'tasks/tripitaka.html', {'tcode': tcode, 'reel_id': reel_id, 'sutra_id': sutra_id})

def correct_feedback(request, pk):
    return render(request, 'tasks/correct_feedback.html', {'correct_fb_id': pk})

def view_correctfeedback(request, correctfeedback_id):
    return render(request, 'tasks/correct_feedback.html', {'correct_fb_id': correctfeedback_id})

def ebook(request):
    return render(request, 'tasks/ebook.html')

def tripitakalist(request):
    return render(request, 'tasks/tripitaka_list.html')
