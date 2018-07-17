# -*- coding: UTF-8 -*-

from .models import *
from rest_framework import serializers
from tasks.serializers import DateTimeTzAwareField

class TaskSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    priority = serializers.SerializerMethodField()
    schedule_no = serializers.SerializerMethodField()
    number = serializers.SerializerMethodField()
    tid = serializers.SerializerMethodField()
    obtain_date = DateTimeTzAwareField(format=settings.DATETIME_FORMAT)
    update_date = DateTimeTzAwareField(format=settings.DATETIME_FORMAT)

    def get_status(self, obj):
        return obj.get_status_display()

    def get_priority(self, obj):
        return obj.get_priority_display()

    def get_schedule_no(self, obj):
        return obj.number.split('_')[0]

    def get_number(self, obj):
        no = obj.number.split('_')[1]
        return no[:-5]

    def get_tid(self, obj):
        return obj.number

class CCTaskSerializer(TaskSerializer):


    class Meta:
        model = CCTask
        fields =  ("tid", "schedule_no", "number", "desc", "status", "priority", "obtain_date", "update_date", "count")


class PageTaskSerializer(TaskSerializer):
    page_info = serializers.SerializerMethodField()
    
    def get_page_info(self, obj):
        return str(obj.pagerect.page)
    
    class Meta:
        model = PageTask
        fields = ("tid", "schedule_no", "page_info", "number", "desc", "status", "priority", "obtain_date", "update_date", "count")

class PageVerifyTaskSerializer(TaskSerializer):
    page_info = serializers.SerializerMethodField()
    
    def get_page_info(self, obj):
        return str(obj.pagerect.page)
    
    class Meta:
        model = PageVerifyTask
        fields = ("tid", "schedule_no", "page_info", "number", "desc", "status", "priority", "obtain_date", "update_date", "count")


class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = '__all__'


