from django.shortcuts import get_object_or_404, render, redirect
from tdata.models import Reel

def index(request, tcode):
    return render(request, 'tasks/tripitaka.html', {'tcode': tcode, 'reel_id': -1})

def correct_feedback(request, pk):
    return render(request, 'tasks/correct_feedback.html', {'correct_fb_id': pk})

def ebook(request):
    return render(request, 'tasks/ebook.html')
def reel(request, reelid):
    reel = Reel.objects.get(id=reelid)
    return render(request, 'tasks/tripitaka.html', {'reel_id': reelid, 'tcode': reel.sutra.tripitaka.code, 'sutraid': reel.sutra_id})
