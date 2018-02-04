from rest_framework import serializers
from rect.models import Rect, PageRect, DeletionCheckItem

class RectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rect
        can_write_fields = ('x', 'y', 'w', 'h', 'op', 'ch', 'id', 'page_code', 'line_no', 'char_no')
        fields = ('w', 'line_no', 'ch', 'wcc', 'op', 'cc',
                  'x', 'id', 'ts', 'char_no', 'h', 'y', 'column_set', 'cid', 'page_code',
                  'reel_id')

class RectWriterSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(format='hex_verbose')
    class Meta:
        model = Rect
        fields = ('x', 'y', 'w', 'h', 'op', 'ch', 'id', 'page_code', 'line_no', 'char_no')

# TODO: check fields
class PageRectSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageRect
        fields = '__all__'

class DeletionCheckItemSerializer(serializers.ModelSerializer):
    cid = serializers.SerializerMethodField()
    modifier = serializers.SerializerMethodField()
    verifier = serializers.SerializerMethodField()

    def get_cid(self, obj):
        try:
            rect = Rect.objects.get(pk=obj.rect_id)
            return rect.cid
        except:
            return ''

    def get_modifier(self, obj):
        return obj.modifier.email

    def get_verifier(self, obj):
        return obj.verifier and obj.verifier.email

    class Meta:
        model = DeletionCheckItem
        can_write_fields = ['id', 'result']
        fields = ("id", "op", "x", "y", "w", "h", "ocolumn_uri", "ocolumn_x", "ocolumn_y", "ch", "rect_id", "result", "created_at", "updated_at", "modifier", "verifier", "del_task")


