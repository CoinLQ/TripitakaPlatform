from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse
from .models import *

# Create your views here.
def page_cut_info(request, pid):
    page = get_object_or_404(Page, pid=pid)
    return HttpResponse(page.cut_info, content_type='text/plain')