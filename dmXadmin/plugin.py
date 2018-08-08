from django.template import loader

from xadmin.views import BaseAdminPlugin

REFRESH_VAR = '_refresh'

# 该插件：加了一个导入按钮
class ImportDataFromFilePlugin(BaseAdminPlugin):

    enableImport = True
    modelName = ''
    buttonName = '导入XX'

    def init_request(self, *args, **kwargs):
        return bool(self.enableImport)

    # 插件拦截了返回 Media 的方法，加入自己需要的 js 文件。
    def get_media(self, media):
        # if self.request.GET.get(REFRESH_VAR):
            # 放页面处于自动刷新状态时，加入自己的 js 制定刷新逻辑
        for jsFile in [
            self.static('js/element-ui.js'),
            self.static('js/vue.js'),
            self.static('js/xadmin/import_data.js'),]:
            media._js.insert(0, jsFile)
        # for cssFile in [
        #     self.static('css/element-ui.css'),
        # ]:
        #     media._css.insert(0, jsFile)
        return media

    # Block Views
    # 在页面中插入 HTML 片段，显示导入按钮。
    def block_top_toolbar(self, context, nodes):
        # current_refresh = self.request.GET.get(REFRESH_VAR)
        # context.update({})
        # 可以将 HTML 片段加入 nodes 参数中
        # context.update({'modelName':self.modelName})
        if self.modelName:
            self.modelName = self.modelName.lower()
        nodes.insert(0, loader.render_to_string('xadmin/import_btnv2.html', context={'modelName': self.modelName, 'buttonName': self.buttonName}))
# 注册插件
