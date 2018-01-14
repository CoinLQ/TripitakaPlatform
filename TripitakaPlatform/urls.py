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

urlpatterns = [
    path('accounts/', include('django.contrib.auth.urls')),
    path('admin/', admin.site.urls),
    path('batchtasks/', batchtask_list),
    path('batchtasks/create', BatchTaskCreate.as_view(), name='batchtasks_create'),
    path('correct/<int:task_id>/', do_correct_task, name='do_correct_task'),
    path('correct/<int:task_id>/reeltext', update_correct_task_result, name='update_correct_task_result'),
    path('correct_verify/<int:task_id>/', do_correct_verify_task, name='do_correct_verify_task'),
]
