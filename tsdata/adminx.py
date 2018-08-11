import xadmin
from xadmin import views
from xadmin.sites import site
from xadmin.views import BaseAdminPlugin, ListAdminView
from xadmin.plugins.actions import BaseActionView
from xadmin.views.base import filter_hook
from xadmin.views.list import COL_LIST_VAR
from django.template.response import TemplateResponse
from django.template import loader
from django.conf import settings

from tsdata.models import * 


##########################################################
# 龙泉经目 LQSutra
class LQSutraAdmin(object):

    modelName = "lqsutra"
    buttonName = '导入龙泉经'

    def modify(self, instance):
        return '修改'
    modify.short_description = '操作'
    list_display = ['sid', 'sutra_variant_no', 'name', 'author',
                    'total_reels', 'remark', 'modify']  # 自定义显示这两个字段
    list_display_links = ('modify',)
    search_fields = ['sid', 'name', 'author']
    list_filter = ['sid', 'name', 'author']
    ordering = ['sid', ]  # 按照倒序排列  -号是倒序

# 实体藏 Tripitaka


class TripitakaAdmin(object):
    list_display = ['name', 'shortname', 'tid', 'modify']

    modelName = "tripitaka"
    buttonName = '导入实体藏'

    def modify(self, instance):
        return '修改'
    modify.short_description = '操作'
    list_display_links = ('modify',)
    search_fields = ['name'] #可以搜索的字段
    list_filter = ['name']
    ordering = ['id', ]
    use_related_menu = False


# 实体经  Sutra
class SutraAdmin(object):
    list_display = ['tripitaka', 'name', 'total_reels', 'Real_reels', 'sid',
                    'lqsutra_name', 'lqsutra_sid', 'remark', 'modify']  # 自定义显示这两个字段
    modelName = "Sutra"
    buttonName = '导入实体经'
    def Real_reels(self, obj):
        return Reel.objects.filter(sutra=obj.id).count()

    def lqsutra_sid(self, obj):
        if obj == None:
            return
        line = obj.lqsutra.__str__()
        line_list = line.split(':')
        return line_list[0]

    def lqsutra_name(self, obj):
        line = obj.lqsutra.__str__()
        line_list = line.split(':')
        if len(line_list) < 2:
            return
        return line_list[1]
    lqsutra_sid.short_description = u'龙泉编码'
    lqsutra_name.short_description = u'龙泉经名'
    Real_reels.short_description = u'实存卷数'
    list_select_related = False

    def modify(self, instance):
        return '修改'
    modify.short_description = '操作'
    list_display_links = ('modify',)
    search_fields = ['name', 'tripitaka__name', 'tripitaka__tid',
                     'sid', 'total_reels', 'remark']  # 可以搜索的字段
    free_query_filter = True
    list_filter = ['name', 'sid']
    fields = ('tripitaka', 'sid', 'name', 'total_reels', 'remark')
    ordering = ['id', ]  # 按照倒序排列


class VolumeAdmin(object):
    modelName = 'Volume'
    buttonName = '导入实体册'

    def modify(self, instance):
        return '修改'
    modify.short_description = '操作'
    list_display_links = ('modify',)
    list_display = ['tripitaka', 'vol_no',  'modify']  # 自定义显示这两个字段
    search_fields = ['tripitaka__name', 'tripitaka__code', 'vol_no']  # 可以搜索的字段
    list_filter = ['tripitaka__code']
    ordering = ['id', ]
 

class ReelAdmin(object):
    modelName = "Reel"
    def tripitaka_name(self, obj):  # 藏名
        t = Tripitaka.objects.get(tid=obj.sutra.tripitaka.tid)
        s = t.__str__()
        return t

    def longquan_name(self, obj):  # 龙泉经名
        return obj.sutra.lqsutra.name

    def sutra_name(self, obj):
        return obj.sutra.name

    sutra_name.short_description = u'经名'
    tripitaka_name.short_description = u'藏名'
    longquan_name.short_description = u'龙泉经名'
    def modify(self, instance):
        return '修改'
    modify.short_description = '操作'
    list_display_links = ('modify',)
    list_display = ['tripitaka_name', 'sutra_name', 'reel_no', 'longquan_name', 'remark',
                    'start_vol', 'start_vol_page', 'end_vol', 'end_vol_page',
                    'modify']  # 自定义显示这两个字段
    search_fields = ['sutra__sid', 'sutra__name', 'sutra__tripitaka__name',  'sutra__tripitaka__code',
                     '=reel_no', 'remark']  # 可以搜索的字段
    list_filter = ['sutra__sid', 'sutra__name', ]
    ordering = ['id', 'reel_no']  # 按照倒序排列
    fields = ('remark',
              'start_vol', 'start_vol_page', 'end_vol', 'end_vol_page')
    use_related_menu = False
    
#
class PageAdmin(object):
    modelName = 'Page'

    def modify(self, instance):
        return '修改'
    modify.short_description = '操作'
    list_display_links = ('modify',)
    list_display = ['pid', 'page_code', 'volume', 'reel','reel_page_no', 'volume_page_no', 'is_existed']  # 自定义显示这两个字段
    search_fields = ['reel']  # 可以搜索的字段
    list_filter = ['volume']
    ordering = ['pid', ]


class LQReelAdmin(object):
    # 龙泉卷不需要导入功能，自动生成。
    enableImport = False

    def modify(self, instance):
        return '修改'

    modify.short_description = '操作'
    list_display_links = ('modify',)
    list_display = ['lqsutra', 'reel_no', 'start_vol', 'start_vol_page', 'end_vol', 'is_existed',
                    'remark']  # 自定义显示这两个字段
    search_fields = ['lqsutra__name', ]  # 可以搜索的字段
    list_filter = ['lqsutra__name']
    ordering = ['id', ] 


xadmin.site.register(Tripitaka, TripitakaAdmin)
xadmin.site.register(Volume, VolumeAdmin)

xadmin.site.register(Sutra, SutraAdmin)
xadmin.site.register(Reel, ReelAdmin)
xadmin.site.register(Page,PageAdmin)

xadmin.site.register(LQSutra, LQSutraAdmin)
xadmin.site.register(LQReel, LQReelAdmin)
  
# ########################################################  
