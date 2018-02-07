# -*- coding:utf-8 -*-
import xadmin
from xadmin.views import BaseAdminPlugin, ListAdminView
from xadmin.views.edit import ModelFormAdminUtil
from xadmin.util import label_for_field
from django.utils.translation import ugettext as _

class ListBrowserPlugin(BaseAdminPlugin):
    browser_details={}

    def __init__(self, admin_view):
        super(ListBrowserPlugin, self).__init__(admin_view)
        self.browserable_need_fields = {}

    def init_request(self, *args, **kwargs):
        active = bool(self.request.method == 'GET' and self.admin_view.has_view_permission() and self.browser_details)
        if active:
            self.model_form = self.get_model_view(ModelFormAdminUtil, self.model).form_obj
        return active

    def result_item(self, item, obj, field_name, row):
        if self.browser_details and item.field and (field_name in self.browser_details.keys()):
            pk = getattr(obj, obj._meta.pk.attname)
            field_label = label_for_field(field_name, obj,
                        model_admin=self.admin_view,
                        return_attr=False)

            item.wraps.insert(0, '<span class="browserable-field">%s</span>')
            title=self.browser_details.get(field_name,{}).get('title',_(u"Details of %s") % field_label)
            default_load_url=self.admin_view.model_admin_url('patch', pk) + '?fields=' + field_name
            load_url = self.browser_details.get(field_name,{}).get('load_url',default_load_url)
            if load_url!=default_load_url:
                concator='?' if load_url.find('?')==-1 else '&'
                load_url=load_url+ '/' +concator+'pk='+str(pk)
            item.btns.append((
                '<a class="browserable-handler" title="%s" data-browserable-field="%s" data-browserable-loadurl="%s">'+
                '<i class="fa fa-search"></i></a>') %
                 (title, field_name,load_url) )

            if field_name not in self.browserable_need_fields:
                self.browserable_need_fields[field_name] = item.field
        return item

    # Media
    def get_media(self, media):
        if self.browserable_need_fields:
            media = media + self.model_form.media + \
                self.vendor(
                    'xadmin.plugin.browser.js')
        return media
xadmin.site.register_plugin(ListBrowserPlugin, ListAdminView)