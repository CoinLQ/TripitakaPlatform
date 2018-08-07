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
   
from jwt_auth.models import Staff, UserManagement, UserAuthentication
import dmXadmin.auth
from tasks.task_controller import correct_update_async, regenerate_correctseg_async
from tsdata.models import *

class GlobalSetting(object):
    site_title = '龙泉.大藏经'  # 设置头标题
    site_footer = '北京龙泉寺---人工智能与信息技术中心'  # 设置脚标题

    def data_mana_menu(self):
        return [{
                'title': u'藏经数据管理',
                'icon': 'fa fa-cloud',
                'menus': [                    
                    {'title': u'龙泉经目','url': self.get_model_url(LQSutra, 'changelist'), 'icon': 'fa fa-book', },
                    {'title': u'龙泉经卷',  'url': self.get_model_url(LQReel, 'changelist'), 'icon': 'fa fa-book', },
                    {'title': u'实体藏', 'url': self.get_model_url(Tripitaka, 'changelist'), 'icon': 'fa fa-book', },
                    {'title': u'实体册',  'url': self.get_model_url(Volume, 'changelist'), 'icon': 'fa fa-book', },
                    {'title': u'实体经',  'url': self.get_model_url(Sutra, 'changelist'), 'icon': 'fa fa-book', },
                    {'title': u'实体卷',  'url': self.get_model_url(Reel, 'changelist'), 'icon': 'fa fa-book', },
                    {'title': u'实体经页',  'url': self.get_model_url(Page, 'changelist'), 'icon': 'fa fa-book', },                    
                ]}, ]

 
    def add_nav_menu(self, menus, nav_menu):
        need_admin = (lambda u: u.is_admin)
        for menu in nav_menu:
            menu['perm'] = need_admin
            if 'menus' in menu:
                for app_menu in menu['menus']:
                    app_menu['perm'] = need_admin
        menus.extend(nav_menu)

    def get_site_menu(self):
        menus = []
#         #self.add_nav_menu(menus, self.collation_menu())
        self.add_nav_menu(menus, self.data_mana_menu())
#         #self.add_nav_menu(menus, self.user_mana_menu())
#         #self.add_nav_menu(menus, self.prepocess_task_menu())
#         #self.add_nav_menu(menus, self.s3_mana_menu())
        return menus

    menu_style = 'accordion'

xadmin.site.register(views.CommAdminView, GlobalSetting)

#####################################################################################
