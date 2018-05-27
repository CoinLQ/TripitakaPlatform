from django.shortcuts import get_object_or_404, render, redirect

def index(request):
    return render(request, 'tasks/tripitaka.html')

def correct_feedback(request, pk):
    return render(request, 'tasks/correct_feedback.html', {'correct_fb_id': pk})
