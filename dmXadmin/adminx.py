import xadmin
from xadmin import views
from xadmin.views import BaseAdminPlugin
from xadmin.views import ListAdminView
from xadmin.plugins.actions import BaseActionView
from xadmin.views.base import filter_hook

from tdata.models import *
from tasks.models import Task
from rect.models import *
from jwt_auth.models import Staff
from tasks.task_controller import correct_update_async

# 龙泉经目 LQSutra


class LQSutraAdmin(object):
    list_display = ['sid', 'variant_code', 'name', 'author',
                    'total_reels', 'remark', 'showSutra']  # 自定义显示这两个字段

    def showSutra(self, obj):
        return '<a href="/xadmin/tdata/sutra/?_p_lqsutra__id__in='+str(obj.id)+'">查看版本</a>'
        # return '<a href="/xadmin/sutradata/sutra/?">查看版本</a>'
    showSutra.short_description = u'操作'
    showSutra.allow_tags = True

    search_fields = ['sid', 'name', 'author']
    list_filter = ['sid', 'name', 'author']
    ordering = ['sid', ]  # 按照倒序排列  -号是倒序

# 实体藏 Tripitaka


class TripitakaAdmin(object):
    list_display = ['id', 'name', 'code', 'operator', 'path1_char',
                    'path1_name', 'path2_char', 'path2_name', 'path3_char', 'path3_name']

    def operator(self, obj):
        edit = '<a href="/xadmin/sutradata/tripitaka/' + \
            str(obj.id)+'/update/">修改</a> '
        dele = '<a href="/xadmin/sutradata/tripitaka/' + \
            str(obj.id)+'/delete/">删除</a> '
        return edit+dele
    operator.short_description = u'操作'
    operator.allow_tags = True
    # search_fields = ['question_text','pub_date'] #可以搜索的字段
    # list_filter = ['question_text','pub_date']
    ordering = ['id', ]  # 按照倒序排列


# 实体经  Sutra
class SutraAdmin(object):
    list_display = ['tripitaka', 'name', 'total_reels', 'Real_reels', 'sid',
                    'lqsutra_name', 'lqsutra_sid', 'remark', 'operator']  # 自定义显示这两个字段

    def Real_reels(self, obj):
        return Reel.objects.filter(sutra=obj.id).count()

    def operator(self, obj):
        edit = '<a href="/xadmin/sutradata/sutra/' + \
            str(obj.id)+'/update/">修改</a> '
        dele = '<a href="/xadmin/sutradata/sutra/' + \
            str(obj.id)+'/delete/">删除</a> '
        return edit+dele
    operator.short_description = u'操作'
    operator.allow_tags = True

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
    # tripitaka.short_description=u'藏'
    list_select_related = False

    search_fields = ['name', 'tripitaka__name', 'lqsutra__id',
                     'sid', 'total_reels', 'remark']  # 可以搜索的字段
    free_query_filter = True
    list_filter = ['name', 'lqsutra__id', 'sid', 'remark']
    list_display_links = ('name')
    fields = ('tripitaka', 'sid', 'name', 'total_reels', 'remark')
    ordering = ['id', ]  # 按照倒序排列


class VolumeAdmin(object):
    list_display = ['tripitaka_name', 'vol_no', 'page_count']  # 自定义显示这两个字段

    def tripitaka_name(self, obj):  # 藏名
        t = Tripitaka.objects.get(code=obj.tripitaka.code)
        s = t.__str__()
        return t
    tripitaka_name.short_description = u'藏名'


class ReelAdmin(object):
    list_display = ['tripitaka_name', 'sutra_name', 'reel_no', 'longquan_Name', 'edition_type', 'remark',
                    'start_vol', 'start_vol_page', 'end_vol', 'end_vol_page',
                    'image_ready', 'cut_ready', 'column_ready']  # 自定义显示这两个字段

    def tripitaka_name(self, obj):  # 藏名
        t = Tripitaka.objects.get(code=obj.sutra.tripitaka.code)
        s = t.__str__()
        return t

    def longquan_Name(self, obj):  # 龙泉经名
        return obj.sutra.lqsutra.name

    def sutra_name(self, obj):
        return obj.sutra.name

    sutra_name.short_description = u'经名'
    tripitaka_name.short_description = u'藏名'
    longquan_Name.short_description = u'龙泉经名'
    search_fields = ['sutra__sid', 'sutra__name', 'sutra__tripitaka__name',
                     'reel_no', 'edition_type', 'remark']  # 可以搜索的字段
    list_filter = ['sutra__sid', 'sutra__name']
    ordering = ['id', 'reel_no']  # 按照倒序排列
    fields = ('sutra', 'reel_no', 'edition_type', 'remark',
              'start_vol', 'start_vol_page', 'end_vol', 'end_vol_page')
    list_display_links = ('sutra_name')


xadmin.site.register(LQSutra, LQSutraAdmin)
xadmin.site.register(Tripitaka, TripitakaAdmin)
xadmin.site.register(Volume, VolumeAdmin)
xadmin.site.register(Sutra, SutraAdmin)
xadmin.site.register(Reel, ReelAdmin)

#####################################################################################
# 校勘任务


class PauseSelectedTasksAction(BaseActionView):

    action_name = "pause_selected_tasks"
    description = '暂停所选的 任务'
    icon = 'fa fa-pause'

    @filter_hook
    def do_action(self, queryset):
        allowed_status = [Task.STATUS_READY, Task.STATUS_PROCESSING]
        n = queryset.filter(status__in=allowed_status).update(
            status=Task.STATUS_PAUSED)
        if n:
            self.message_user("成功暂停了%(count)d个任务。" % {
                "count": n,
            }, 'success')


class ContinueSelectedTasksAction(BaseActionView):

    action_name = "continue_selected_tasks"
    description = '继续所选的 任务'
    icon = 'fa fa-play'

    @filter_hook
    def do_action(self, queryset):
        n1 = queryset.filter(status=Task.STATUS_PAUSED,
                             picker=None).update(status=Task.STATUS_READY)
        n2 = queryset.filter(status=Task.STATUS_PAUSED).exclude(
            picker=None).update(status=Task.STATUS_PROCESSING)
        if n1 or n2:
            msg = "成功将%d个任务的状态变为待领取，将%d个任务的状态变为进行中。" % (n1, n2)
            self.message_user(msg, 'success')


class ReclaimSelectedTasksAction(BaseActionView):

    action_name = "reclaim_selected_tasks"
    description = '回收所选的 任务'
    icon = 'fa fa-unlink'

    @filter_hook
    def do_action(self, queryset):
        n = queryset.filter(status=Task.STATUS_PROCESSING).update(
            status=Task.STATUS_READY, picker=None, picked_at=None)
        if n:
            msg = "成功将%d个任务的状态变为待领取。" % n
            self.message_user(msg, 'success')


class SetPriorityActionBase(BaseActionView):
    icon = 'fa fa-tasks'

    @filter_hook
    def do_action(self, queryset):
        n = queryset.update(priority=self.priority)
        if n:
            self.message_user("成功将%(count)d个任务%(description)s。" % {
                "count": n,
                "description": self.description,
            }, 'success')


class SetHighPriorityAction(SetPriorityActionBase):
    action_name = "set_high_priority"
    description = '设为高优先级'
    priority = 3


class SetMiddlePriorityAction(SetPriorityActionBase):
    action_name = "set_middle_priority"
    description = '设为中优先级'
    priority = 2


class SetLowPriorityAction(SetPriorityActionBase):
    action_name = "set_low_priority"
    description = '设为低优先级'
    priority = 1


class UpdateTaskResultAction(BaseActionView):

    action_name = "update_task_result"
    description = '更新任务数据'
    icon = 'fa fa-refresh'

    @filter_hook
    def do_action(self, queryset):
        types = [Task.TYPE_CORRECT, Task.TYPE_CORRECT_VERIFY]
        task_lst = list(queryset.filter(
            typ__in=types, status=Task.STATUS_FINISHED))
        for task in task_lst:
            correct_update_async(task.id)
        if task_lst:
            self.message_user("成功对%(count)d个任务做了数据更新。" % {
                "count": len(task_lst),
            }, 'success')


@xadmin.sites.register(Task)
class TaskAdmin(object):
    def modify(self, instance):
        return '修改'
    modify.short_description = '操作'

    def task_link(self, instance):
        if instance.status in [Task.STATUS_PROCESSING, Task.STATUS_PAUSED, Task.STATUS_FINISHED]:
            return '<a target="_blank" href="/correct/%d/">查看</a>' % (instance.id)
        else:
            return ''
    task_link.allow_tags = True
    task_link.short_description = '查看任务'
    list_display = ['batchtask', 'tripitaka_name', 'sutra_name', 'lqsutra_name', 'base_reel_name',
                    'reel_no', 'typ', 'priority', 'task_no', 'realtime_progress', 'status',
                    'publisher', 'created_at', 'picker', 'picked_at', 'finished_at', 'task_link', 'modify']
    list_display_links = ("modify",)
    list_filter = ['typ', 'batchtask', 'picker', 'status', 'task_no']
    search_fields = ['reel__sutra__tripitaka__name',
                     'reel__sutra__name', 'reel__reel_no', 'lqreel__lqsutra__name']
    fields = ['status', 'result', 'picked_at', 'picker', 'priority']
    remove_permissions = ['add']
    actions = [PauseSelectedTasksAction, ContinueSelectedTasksAction, ReclaimSelectedTasksAction,
               SetHighPriorityAction, SetMiddlePriorityAction, SetLowPriorityAction,
               UpdateTaskResultAction]

#####################################################################################
# 切分数据配置


@xadmin.sites.register(Reel_Task_Statistical)
class Reel_Task_StatisticalAdmin(object):
    def resume_pptask(self, instance):
        task_header = "%s_%s" % (
            instance.schedule.schedule_no, instance.reel_id)
        count = PageTask.objects.filter(
            number__regex=r'^' + task_header + r'.*', status=TaskStatus.NOT_READY).count()
        if count > 0:
            return """<a class='btn btn-success' href='/xadmin/rect/reel_pptask/open/?schedule_no=%s&reel_id=%s&pk=%s'>%s</a>""" % (instance.schedule.schedule_no,  instance.reel_id, instance.pk,  u"打开逐字校对")
        return '已打开'
    resume_pptask.short_description = "打开逐字校对"
    resume_pptask.allow_tags = True
    resume_pptask.is_column = True

    list_display = ('schedule', 'reel', 'amount_of_cctasks', 'completed_cctasks',
                    'amount_of_absenttasks', 'completed_absenttasks', 'amount_of_pptasks',
                    'completed_pptasks', 'updated_at', 'resume_pptask')
    list_display_links = ('completed_cctasks', 'reel')
    search_fields = ('amount_of_cctasks', 'completed_cctasks')
    list_filter = ('completed_cctasks',)


# 1
@xadmin.sites.register(Schedule)
class ScheduleAdmin(object):
    browser_details = {'name': {'title': u'置信度阀值预览', 'load_url': 'detail2'}}

    def remain_task_count(self, instance):
        count = CCTask.objects.filter(
            schedule=instance.id, status__in=TaskStatus.remain_status).count()
        if count > 0:
            return """<a href='/xadmin/rect/cctask/?schedule_id__exact=%s'>%s</a>""" % (instance.id, count)
        return count
    remain_task_count.short_description = "未完置信任务数"
    remain_task_count.allow_tags = True
    remain_task_count.is_column = True

    list_display = ("name", "cc_threshold", "status", "due_at",
                    'created_at', 'remain_task_count')
    list_display_links = ("name", )
    list_filter = ('status', 'due_at', 'created_at')
    search_fields = ["name"]
    list_editable = ("cc_threshold",)
    date_hierarchy = 'due_at'
    relfield_style = "fk-select"
    reversion_enable = True
    style_fields = {'reels': 'm2m_transfer'}

# 2目前不需要显示
# @xadmin.sites.register(Schedule_Task_Statistical)
# class Schedule_Task_StatisticalAdmin(object):
#     list_display = ('schedule', 'amount_of_cctasks', 'completed_cctasks', 'amount_of_classifytasks',
#         'completed_classifytasks', 'amount_of_absenttasks', 'completed_absenttasks', 'amount_of_pptasks',
#         'completed_pptasks', 'amount_of_vdeltasks', 'completed_vdeltasks', 'amount_of_reviewtasks',
#         'completed_reviewtasks', 'remark', 'updated_at')
#     list_display_links = ('completed_cctasks',)
#     search_fields = ('amount_of_cctasks',)
#     list_editable = ('remark',)
#     list_filter = ('completed_cctasks',)

# 3


@xadmin.sites.register(CCTask)
class CCTaskAdmin(object):
    list_display = ("number", "schedule", "ttype", "status",
                    "update_date", "rect_set", "owner")
    list_display_links = ("number",)
    list_filter = ("number", 'update_date')
    search_fields = ["owner__email", "status"]
    list_editable = ('owner', "status")
    date_hierarchy = 'update_date'  # 详细时间分层筛选
    relfield_style = "fk-select"


@xadmin.sites.register(CharClassifyPlan)
class CharClassifyPlanAdmin(object):

    browser_details = {'ch': {'title': u'聚类字块详情页', 'load_url': 'detail2'}}

    list_display = ("schedule", "ch", "total_cnt",
                    "needcheck_cnt", "wcc_threshold", )
    list_display_links = ("total_cnt",)
    list_filter = ("ch", 'total_cnt')
    search_fields = ["ch", "total_cnt"]
    list_editable = ('wcc_threshold',)
    date_hierarchy = 'wcc_threshold'  # 详细时间分层筛选
    relfield_style = "fk-select"


@xadmin.sites.register(ClassifyTask)
class ClassifyTaskAdmin(object):
    list_display = ("number", "schedule", "ttype", "status",
                    "update_date", "rect_set", "owner")
    list_display_links = ("number",)
    list_filter = ("number", 'update_date')
    search_fields = ["owner__email", "status"]
    list_editable = ('owner', "status")
    date_hierarchy = 'update_date'  # 详细时间分层筛选
    relfield_style = "fk-select"


@xadmin.sites.register(DelTask)
class DelTaskAdmin(object):
    list_display = ("number", "schedule", "ttype", "status",
                    "update_date", "rect_set", "owner")
    list_display_links = ("number",)
    list_filter = ("number", 'update_date')
    search_fields = ["owner__email", "status"]
    list_editable = ('owner', "status")
    date_hierarchy = 'update_date'  # 详细时间分层筛选
    relfield_style = "fk-select"


@xadmin.sites.register(PageTask)
class PageTaskAdmin(object):
    list_display = ("number", "schedule", "ttype", "status",
                    "update_date", "page_set", "owner")
    list_display_links = ("number",)
    list_filter = ("number", 'update_date')
    search_fields = ["owner__email", "status"]
    list_editable = ('owner', "status")
    date_hierarchy = 'update_date'  # 详细时间分层筛选
    relfield_style = "fk-select"


@xadmin.sites.register(AbsentTask)
class AbsentTaskAdmin(object):
    list_display = ("number", "schedule", "ttype", "status",
                    "update_date", "page_set", "owner")
    list_display_links = ("number",)
    list_filter = ("number", 'update_date')
    search_fields = ["owner__email", "status"]
    list_editable = ('owner', "status")
    date_hierarchy = 'update_date'  # 详细时间分层筛选
    relfield_style = "fk-select"

# @xadmin.sites.register(Permission)
# class PermissionAdmin(object):
#     list_display = ('id', 'name', 'menu', 'get_roles', 'is_active')
#     fields = ('is_active', 'roles', 'menu')

#     def get_roles(self, obj):
#         return ",".join([r.name for r in obj.roles.all()])

# @xadmin.sites.register(Resource)
# class ResourceAdmin(object):
#     pass

# @xadmin.sites.register(Role)
# class RoleAdmin(object):
#     list_display = ('id', 'name')


# @xadmin.sites.register(Menu)
# class MenuAdmin(object):
#     list_display = ('id', 'name', 'menu_paths', 'is_active')
#     fields = ('menu_paths', 'is_active' )


#####################################################################################


class GlobalSetting(object):
    site_title = '龙泉大藏经'  # 设置头标题
    site_footer = '北京 龙泉寺-AIITC.inc'  # 设置脚标题

    def rect_data_menu(self):
        return [{
                # 'perm': self.get_model_perm(Reel_Task_Statistical, 'view'),
                'title': u'藏经切分管理',
                'icon': 'fa fa-cut',
                'menus': (
                    {'title': u'总体进度', 'url': self.get_model_url(
                        Reel_Task_Statistical, 'changelist'), 'icon': 'fa fa-tasks', },
                    {'title': u'切分计划',  'url': self.get_model_url(
                        Schedule, 'changelist'), 'icon': 'fa fa-calendar', },
                    {'title': u'置信校对',  'url': self.get_model_url(
                        CCTask, 'changelist'), 'icon': 'fa fa-edit', },
                    {'title': u'聚类校对',  'url': self.get_model_url(
                        ClassifyTask, 'changelist'), 'icon': 'fa fa-edit', },
                    {'title': u'查漏校对',  'url': self.get_model_url(
                        AbsentTask, 'changelist'), 'icon': 'fa fa-edit', },
                    {'title': u'逐字校对',  'url': self.get_model_url(
                        PageTask, 'changelist'), 'icon': 'fa fa-edit', },
                    {'title': u'删框审定',  'url': self.get_model_url(
                        DelTask, 'changelist'), 'icon': 'fa fa-stethoscope', },
                    {'title': u'反馈检查',   'icon': 'fa fa-ban', },
                    {'title': u'聚类阈值',  'url': self.get_model_url(
                        CharClassifyPlan, 'changelist'),   'icon': 'fa fa-circle'},
                )}, ]

    def data_mana_menu(self):
        return [{
                'title': u'藏经数据管理',
                'icon': 'fa fa-book',
                'menus': (
                    {'title': u'龙泉经目', 'url': self.get_model_url(
                        LQSutra, 'changelist'), 'icon': 'fa fa-book', },
                    {'title': u'实体藏',  'url': self.get_model_url(
                        Tripitaka, 'changelist'), 'icon': 'fa fa-book', },
                    {'title': u'实体册',  'url': self.get_model_url(
                        Volume, 'changelist'), 'icon': 'fa fa-book', },
                    {'title': u'实体经',  'url': self.get_model_url(
                        Sutra, 'changelist'), 'icon': 'fa fa-book', },
                    {'title': u'实体卷',  'url': self.get_model_url(
                        Reel, 'changelist'), 'icon': 'fa fa-book', },
                )}, ]

    def user_mana_menu(self):
        return [{
                # 'perm': self.get_model_perm(LQSutra, 'view'),
                'title': u'用户中心',
                'icon': 'fa fa-book',
                'menus': (
                    {'title': u'用户维护', 'url': self.get_model_url(
                        Staff, 'changelist'), 'icon': 'fa fa-book', },
                    # {'title': u'角色维护', 'url': self.get_model_url(Role, 'changelist'),'icon':'fa fa-book',},
                    # {'title': u'菜单管理', 'url': self.get_model_url(Menu, 'changelist'),'icon':'fa fa-book',},
                    # {'title': u'权限管理', 'url': self.get_model_url(Permission, 'changelist'),'icon':'fa fa-book',},
                )}, ]

    def get_site_menu(self):
        menus = []
        menus.extend(self.rect_data_menu())
        menus.extend(self.data_mana_menu())
        menus.extend(self.user_mana_menu())
        return menus

    menu_style = 'accordion'


xadmin.site.register(views.CommAdminView, GlobalSetting)

#####################################################################################
