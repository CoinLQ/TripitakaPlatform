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
from tasks.views.mark import *
from tasks.views import lqtripitaka
from tasks.views import tripitaka
from tools.views import *
from tdata.views import email_vericode
import xadmin
import tdata

urlpatterns = [
    path('accounts/', include('django.contrib.auth.urls')),
    path('backend/', admin.site.urls),
    path('manage/', xadmin.site.urls),
    url(r'^auth/', include("jwt_auth.urls", namespace="api-auth")),
    url(r'^api/', include('api.urls')),
    url(r'^auth/api-vericode/', email_vericode),
    url(r'^activate/(?P<token>[0-9a-zA-Z@.*$]+)/$', tdata.views.active_user, name='index'),
    path('correct/<int:task_id>/', do_correct_task, name='do_correct_task'),
    path('verify_correct/<int:task_id>/', do_correct_task, name='do_correct_verify_task'),
    path('correct_difficult/<int:task_id>/', do_correct_task, name='do_correct_task'),
    path('sutra_pages/<pid>/view', sutra_page_detail, name='sutra_page_detail'),
    path('judge/<int:task_id>/', do_judge_task, name='do_judge_task'),
    path('verify_judge/<int:task_id>/', do_judge_task, name='do_judge_verify_task'),
    path('judge_difficult/<int:task_id>/', do_judge_task, name='do_judge_difficult_task'),
    path('punct/<int:task_id>/', do_punct_task, name='do_punct_task'),
    path('verify_punct/<int:task_id>/', do_punct_task, name='do_punct_verify_task'),
    path('lqpunct/<int:task_id>/', do_punct_task, name='do_lqpunct_task'),
    path('verify_lqpunct/<int:task_id>/', do_punct_task, name='do_lqpunct_verify_task'),
    path('lqtripitaka/', lqtripitaka.index, name='lqtripitaka_index'),
    path('tripitaka/<tcode>/', tripitaka.index, name='tripitaka_index'),
    path('tripitakareel/<int:reelid>/', tripitaka.reel, name='tripitaka_reel'),
    path('tripitaka/', tripitaka.tripitakalist, name='tripitaka_list'),
    path('ebook/', tripitaka.ebook, name='tripitaka_ebook'),
    path('do_generate_task/', lqtripitaka.do_generate_task, name='lqtripitaka_index'),
    path('mark/<int:task_id>/', do_mark_task, name='do_mark_task'),
    path('verify_mark/<int:task_id>/', do_mark_task, name='do_mark_verify_task'),
    path('judgefeedback/<int:judgefeedback_id>/', lqtripitaka.process_judgefeedback, name='process_judgefeedback'),
    path('my_judgefeedback/<int:judgefeedback_id>/', lqtripitaka.view_judgefeedback, name='view_judgefeedback'),
    path('lqpunctfeedback/<int:lqpunctfeedback_id>/', lqtripitaka.process_lqpunctfeedback, name='process_lqpunctfeedback'),
    path('my_lqpunctfeedback/<int:lqpunctfeedback_id>/', lqtripitaka.view_lqpunctfeedback, name='view_lqpunctfeedback'),
    path('abnormal_line_count/<int:task_id>/', process_abnormal_line_count, name='process_abnormal_line_count'),

    path('tools/cutfixed_pages/', cutfixed_pages, name='cutfixed_pages'),
    path('tools/cutfixed_pages/<pid>/', cutfixed_page_detail, name='cutfixed_page_detail'),
    path('correctfeedback/<int:pk>/', tripitaka.correct_feedback, name='correct_feedback'),
]

# # 通用URL映射，必须放在最后
urlpatterns += [
    # 通用页面URL映射，必须放在最后
    url(r'^api/v1', include('api.common_urls',
                            namespace='common_api')),
]
