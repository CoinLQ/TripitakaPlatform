from django.shortcuts import render

def vuejs_test(request):
    context = {}
    return render(request, 'tools/vuejs_test.html', context)