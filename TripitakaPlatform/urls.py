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

from tasks.views import *
from sutradata.views import *
from tools.views import *

urlpatterns = [
    path('accounts/', include('django.contrib.auth.urls')),
    path('admin/', admin.site.urls),
    path('batchtasks/', batchtask_list),
    path('batchtasks/create', BatchTaskCreate.as_view(), name='batchtasks_create'),
    path('correct/<int:task_id>/', do_correct_task, name='do_correct_task'),
    path('correct_verify/<int:task_id>/', do_correct_verify_task, name='do_correct_verify_task'),
    path('pages/cutlist', page_cut_list, name='page_cut_list'),
    path('pages/verify_cutlist', page_verify_cut_list, name='page_verify_cut_list'),
    path('pages/<pid>/cut', page_cut_info, name='page_cut_info'),
    path('sutra_pages/<pid>/view', sutra_page_detail, name='sutra_page_detail'),
    path('judge/<int:task_id>/', do_judge_task, name='do_judge_task'),

    path('api/judge/<int:task_id>/diffsegs', api_judge_diffsegs, name='api_judge_diffsegs'),
    path('api/judge/<int:task_id>/diffseg_pos_list', api_judge_diffseg_pos_list, name='api_judge_diffseg_pos_list'),
    path('api/judge/<int:task_id>/is_all_selected', api_judge_is_all_selected, name='api_judge_is_all_selected'),
    path('api/judge/<int:task_id>/diffsegs/<int:diffseg_id>/select', api_judge_diffseg_select, name='api_judge_diffseg_select'),
    path('api/judge/<int:task_id>/diffsegs/merge', api_judge_diffseg_merge, name='api_judge_diffseg_merge'),
    path('api/judge/<int:task_id>/diffsegs/<int:diffseg_id>/merge_list', api_judge_get_merge_list, name='api_judge_get_merge_list'),
    path('api/judge/<int:task_id>/diffsegs/<int:diffseg_id>/split', api_judge_diffseg_split, name='api_judge_diffseg_split'),

    path('tools/cutfixed_pages/', cutfixed_pages, name='cutfixed_pages'),
    path('tools/cutfixed_pages/<pid>/', cutfixed_page_detail, name='cutfixed_page_detail'),
]
