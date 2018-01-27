from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, JsonResponse
from sutradata.models import *

def cutfixed_pages(request):
    queryset = Page.objects.exclude(cut_updated_at__isnull=True).values_list('pid', 'cut_updated_at', named=True)
    page_list = [{
        'pid': r.pid,
        'cut_updated_at': int(r.cut_updated_at.timestamp())
        } for r in queryset]
    return render(request, 'tools/cutfixed_pages.html', {'page_list': page_list})

def cutfixed_page_detail(request, pid):
    page = get_object_or_404(Page, pid=pid)
    return render(request, 'tools/cutfixed_page_detail.html', {'page': page})