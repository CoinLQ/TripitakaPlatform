from rest_framework import serializers
from rect.serializers import TaskSerializer
from .models import PrePageColTask, PrePageColVerifyTask, ColRect

class PrePageColTaskSerializer(TaskSerializer):
    page_info = serializers.SerializerMethodField()
    
    def get_page_info(self, obj):
        return str(obj.page.page_info)
    
    class Meta:
        model = PrePageColTask
        fields = ("tid", "schedule_no", "page_info", "number", "desc", "status", "priority", "obtain_date", "update_date")

class PrePageColVerifyTaskSerializer(TaskSerializer):
    page_info = serializers.SerializerMethodField()
    
    def get_page_info(self, obj):
        return str(obj.page.page_info)
    
    class Meta:
        model = PrePageColVerifyTask
        fields = ("tid", "schedule_no", "page_info", "number", "desc", "status", "priority", "obtain_date", "update_date")


class ColRectSerializer(serializers.ModelSerializer):
    class Meta:
        model = ColRect
        can_write_fields = ('x', 'y', 'w', 'h', 'op', 'ch', 'id', 'page_id', 'line_no', 'char_no')
        fields = ('w', 'line_no', 'ch', 'wcc', 'op', 'cc',
                  'x', 'id', 'char_no', 'h', 'y', 'page_id')

class ColRectWriterSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(format='hex_verbose')
    class Meta:
        model = ColRect
        fields = ('x', 'y', 'w', 'h', 'op', 'ch', 'id', 'page_id', 'line_no', 'char_no')
