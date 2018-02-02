from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.conf import settings
from .models import *

# Create your views here.
def page_cut_info(request, pid):
    page = get_object_or_404(Page, pid=pid)
    response = HttpResponse(page.cut_info, content_type='text/plain')
    return response

def page_cut_list(request):
    queryset = Page.objects.exclude(cut_updated_at__isnull=True).values_list('pid', 'cut_updated_at', named=True)
    page_list = [{
        'pid': r.pid,
        'cut_updated_at': int(r.cut_updated_at.timestamp())
        } for r in queryset]
    return JsonResponse({'page_list': page_list})

def page_verify_cut_list(request):
    queryset = Page.objects.filter(~Q(cut_verify_count=0)).values_list('pid', 'cut_updated_at', 'cut_add_count', 'cut_wrong_count', 'cut_confirm_count', 'cut_verify_count', named=True)
    page_list = [{
        'pid': r.pid,
        'cut_updated_at': int(r.cut_updated_at.timestamp()),
        'cut_verify_count': r.cut_verify_count,
        'cut_add_count': r.cut_add_count,
        'cut_wrong_count': r.cut_wrong_count,
        'cut_confirm_count': r.cut_confirm_count,
        } for r in queryset]
    return JsonResponse({'page_list': page_list})

def sutra_page_detail(request, pid):
    page = get_object_or_404(Page, pid=pid)
    reel = page.reel
    vol_page = reel.start_vol_page + page.reel_page_no - 1
    image_url = '%s%s%s.jpg' % (settings.IMAGE_URL_PREFIX, reel.url_prefix, vol_page)
    char_pos = request.GET.get('char_pos', '')
    s = char_pos[-4:]
    try:
        line_no = int(s[-4:-2])
        char_no = int(s[-2:])
    except:
        pass
    context = {
        'page': page,
        'image_url': image_url,
        'line_no': line_no,
        'char_no': char_no,
    }
    return render(request, 'sutradata/sutra_page_detail.html', context)