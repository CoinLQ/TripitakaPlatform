"""TripitakaPlatform URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf.urls.static import static
from django.urls import include, path
from django.conf.urls import url

from tasks.views.correct import *
from tasks.views.judge import *
from tools.views import *
import xadmin

urlpatterns = [
    path('accounts/', include('django.contrib.auth.urls')),
    path('admin/', admin.site.urls),
    path('xadmin/', xadmin.site.urls),
    url(r'^auth/', include("jwt_auth.urls", namespace="api-auth")),
    url(r'^api-auth/', include('rest_framework.urls')),
    url(r'^api/', include('api.urls')),
    path('correct/<int:task_id>/', do_correct_task, name='do_correct_task'),
    path('correct_verify/<int:task_id>/', do_correct_verify_task, name='do_correct_verify_task'),
    path('sutra_pages/<pid>/view', sutra_page_detail, name='sutra_page_detail'),
    path('judge/<int:task_id>/', do_judge_task, name='do_judge_task'),
    path('judge_verify/<int:task_id>/', do_judge_verify_task, name='do_judge_verify_task'),

    path('tools/cutfixed_pages/', cutfixed_pages, name='cutfixed_pages'),
    path('tools/cutfixed_pages/<pid>/', cutfixed_page_detail, name='cutfixed_page_detail'),
]
