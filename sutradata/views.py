from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
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

def cutfixed_pages(request):
    queryset = Page.objects.exclude(cut_updated_at__isnull=True).values_list('pid', 'cut_updated_at', named=True)
    page_list = [{
        'pid': r.pid,
        'cut_updated_at': int(r.cut_updated_at.timestamp())
        } for r in queryset]
    return render(request, 'sutradata/cutfixed_pages.html', {'page_list': page_list})

def cutfixed_page_detail(request, pid):
    page = get_object_or_404(Page, pid=pid)
    return render(request, 'sutradata/cutfixed_page_detail.html', {'page': page})

def sutra_page_detail(request, pid):
    page = get_object_or_404(Page, pid=pid)
    cid = request.GET.get('cid', '')
    return render(request, 'sutradata/sutra_page_detail.html', {'page': page, 'cid': cid})