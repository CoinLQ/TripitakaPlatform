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
from django.urls import include, path, re_path
from django.conf.urls import url
from tasks.views.correct import *
from tasks.views.judge import *
from tasks.views.punct import *
from tasks.views import lqtripitaka
from tools.views import *
import xadmin

urlpatterns = [
    path('accounts/', include('django.contrib.auth.urls')),
    path('backend/', admin.site.urls),
    path('manage/', xadmin.site.urls),
    url(r'^auth/', include("jwt_auth.urls", namespace="api-auth")),
    url(r'^api/', include('api.urls')),
    path('correct/<int:task_id>/', do_correct_task, name='do_correct_task'),
    path('verify_correct/<int:task_id>/', do_correct_task, name='do_correct_task'),
    path('sutra_pages/<pid>/view', sutra_page_detail, name='sutra_page_detail'),
    path('judge/<int:task_id>/', do_judge_task, name='do_judge_task'),
    path('verify_judge/<int:task_id>/', do_judge_task, name='do_judge_verify_task'),
    path('punct/<int:task_id>/', do_punct_task, name='do_punct_task'),
    path('verify_punct/<int:task_id>/', do_punct_task, name='do_punct_task'),
    path('lqpunct/<int:task_id>/', do_punct_task, name='do_punct_task'),
    path('verify_lqpunct/<int:task_id>/', do_punct_task, name='do_punct_task'),
    path('lqtripitaka/', lqtripitaka.index, name='lqtripitaka_index'),

    path('tools/cutfixed_pages/', cutfixed_pages, name='cutfixed_pages'),
    path('tools/cutfixed_pages/<pid>/', cutfixed_page_detail, name='cutfixed_page_detail'),
]

# # 通用URL映射，必须放在最后
urlpatterns += [
    # 通用页面URL映射，必须放在最后
    url(r'^api/v1', include('api.common_urls',
                             namespace='common_api')),
]