from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
import json

class SutraTextField(models.TextField):

    description = '存储经文内容，换行用\n，每页前有换页标记p\n'

    def __init__(self, *args, **kwargs):
        kwargs['blank'] = True
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        del kwargs["blank"]
        return name, path, args, kwargs

    def get_prep_value(self, value):
        value = value.replace('\r\n', '\n')
        value = super().get_prep_value(value)
        return self.to_python(value)

class TripiMixin(object):
    def __str__(self):
        return self.name

class Tripitaka(models.Model, TripiMixin):
    code = models.CharField(verbose_name='实体藏经版本编码', max_length=2, blank=False)
    name = models.CharField(verbose_name='实体藏经名称', max_length=32, blank=False)
    shortname = models.CharField(verbose_name='简称（用于校勘记）', max_length=32, blank=False)
    remark = models.TextField('备注', default='')

    class Meta:
        verbose_name = '实体藏经'
        verbose_name_plural = '实体藏经管理'

    def __str__(self):
        return '{} ({})'.format(self.name, self.code)

class Volume(models.Model):
    tripitaka = models.ForeignKey(Tripitaka, on_delete=models.CASCADE)
    vol_no = models.SmallIntegerField(verbose_name='册序号')
    page_count = models.IntegerField(verbose_name='册页数')
    remark = models.TextField('备注', default='')

    class Meta:
        verbose_name = u"实体册"
        verbose_name_plural = u"实体册"

    def __str__(self):
        return '%s: 第%s册' % (self.tripitaka.name, self.vol_no)

class LQSutra(models.Model, TripiMixin):
    sid = models.CharField(verbose_name='龙泉经目经号编码', max_length=8) #（为"LQ"+ 经序号 + 别本号）
    code = models.CharField(verbose_name='龙泉经目编码', max_length=5, blank=False)
    variant_code = models.CharField(verbose_name='龙泉经目别本编码', max_length=1, default='0')
    name = models.CharField(verbose_name='龙泉经目名称', max_length=64, blank=False)
    total_reels = models.IntegerField(verbose_name='总卷数', blank=True, default=1)
    remark = models.TextField('备注', default='')

    class Meta:
        verbose_name = u"龙泉经目"
        verbose_name_plural = u"龙泉经目"

    def __str__(self):
        return '%s: %s' % (self.sid, self.name)

class Sutra(models.Model, TripiMixin):
    sid = models.CharField(verbose_name='实体藏经|唯一经号编码', editable=True, max_length=8)
    tripitaka = models.ForeignKey(Tripitaka, on_delete=models.CASCADE)
    code = models.CharField(verbose_name='实体经目编码', max_length=5, blank=False)
    variant_code = models.CharField(verbose_name='别本编码', max_length=1, default='0')
    name = models.CharField(verbose_name='实体经目名称', max_length=64, blank=True)
    lqsutra = models.ForeignKey(LQSutra, verbose_name='龙泉经目编码', null=True, 
    blank=True, on_delete=models.SET_NULL) #（为"LQ"+ 经序号 + 别本号）
    total_reels = models.IntegerField(verbose_name='总卷数', blank=True, default=1)
    remark = models.TextField('备注', default='')
    author = models.CharField('作译者', max_length=32, default='')

    class Meta:
        verbose_name = '实体经目'
        verbose_name_plural = '实体经目管理'

    def __str__(self):
        return '%s: %s' % (self.sid, self.name)

class LQReel(models.Model):
    lqsutra = models.ForeignKey(LQSutra, verbose_name='龙泉经目编码', on_delete=models.CASCADE)
    reel_no = models.SmallIntegerField('卷序号')
    text = SutraTextField('经文', default='')
    remark = models.TextField('备注', default='')

    class Meta:
        verbose_name = '龙泉藏经卷'
        verbose_name_plural = '龙泉藏经卷'
        unique_together = (('lqsutra', 'reel_no'),)

    def __str__(self):
        return '%s (第%s卷)' % (self.lqsutra, self.reel_no)

class Reel(models.Model):
    EDITION_TYPE_UNKNOWN = 0 # 未选择
    EDITION_TYPE_BASE = 1 # 底本
    EDITION_TYPE_CHECKED = 2 # 对校本
    EDITION_TYPE_PROOF = 3 # 参校本
    EDITION_TYPE_CHOICES = (
        (EDITION_TYPE_UNKNOWN, '未选择'),
        (EDITION_TYPE_BASE, '底本'),
        (EDITION_TYPE_CHECKED, '对校本'),
        (EDITION_TYPE_PROOF, '参校本'),
    )
    sutra = models.ForeignKey(Sutra, verbose_name='实体藏经', on_delete=models.CASCADE)
    reel_no = models.SmallIntegerField('卷序号')
    start_vol = models.SmallIntegerField('起始册')
    start_vol_page = models.SmallIntegerField('起始册的页序号')
    end_vol = models.SmallIntegerField('终止册')
    end_vol_page = models.SmallIntegerField('终止册的页序号')
    path1 = models.CharField('存储层次1', max_length=16, default='')
    path2 = models.CharField('存储层次2', max_length=16, default='')
    path3 = models.CharField('存储层次3', max_length=16, default='')
    text = SutraTextField('经文', default='') #按实际行加了换行符，换页标记为p\n
    fixed = models.BooleanField('是否有调整', default=False)
    f_start_page = models.CharField('起始页ID', max_length=18, default='', blank=True, null=True)
    f_start_line_no = models.IntegerField('起始页行序号', default=-1)
    f_start_char_no = models.IntegerField('起始页的行中字序号', default=-1)
    f_end_page = models.CharField('终止页ID', max_length=18, default='', blank=True, null=True)
    f_end_line_no = models.IntegerField('终止页行序号', default=-1)
    f_end_char_no = models.IntegerField('终止页的行中字序号', default=-1)
    f_text = SutraTextField('调整经文', default='', blank=True, null=True)
    correct_text = SutraTextField('文字校对后的经文', default='') #按实际行加了换行符，换页标记为p\n
    edition_type = models.SmallIntegerField('版本类型', choices=EDITION_TYPE_CHOICES, default=0)
    remark = models.TextField('备注', default='')

    class Meta:
        verbose_name = '实体藏经卷'
        verbose_name_plural = '实体藏经卷'
        unique_together = (('sutra', 'reel_no'),)

    def __str__(self):
        return '%s (第%s卷)' % (self.sutra, self.reel_no)

    def url_prefix(self):
        tcode = self.sutra.sid[0:2]
        path_lst = []
        if self.path1:
            path_lst.append(self.path1)
            if self.path2:
                path_lst.append(self.path2)
                if self.path3:
                    path_lst.append(self.path3)
        path_str = '/'.join(path_lst)
        filename_str = '_'.join(path_lst)
        s = '/%s/%s/%s_%s_' % (tcode, path_str, tcode, filename_str)
        return s

    def image_prefix(self):
        tcode = self.sutra.sid[0:2]
        path_lst = []
        if self.path1:
            path_lst.append(self.path1)
            if self.path2:
                path_lst.append(self.path2)
                if self.path3:
                    path_lst.append(self.path3)
        filename_str = '_'.join(path_lst)
        s = '%s_%s_' % (tcode, filename_str)
        return s

class Page(models.Model):
    pid = models.CharField('页ID', editable=True, max_length=13, primary_key=True) #sid + 3位卷号 + 2位页序号，页序号从1计数。如：YB00086000101
    reel = models.ForeignKey(Reel, verbose_name='实体藏经卷', on_delete=models.CASCADE)
    reel_page_no = models.SmallIntegerField('卷中页序号')
    vol_no = models.SmallIntegerField('册序号')
    page_no = models.SmallIntegerField('页序号') 
    text = SutraTextField('经文') # 文字校对后的经文
    cut_info = models.TextField('切分信息')
    cut_updated_at = models.DateTimeField('更新时间', null=True)
    cut_add_count = models.SmallIntegerField('切分信息增加字数', default=0)
    cut_wrong_count = models.SmallIntegerField('切分信息识别错的字数', default=0)
    cut_confirm_count = models.SmallIntegerField('切分信息需要确认的字数', default=0)
    cut_verify_count = models.SmallIntegerField('切分信息需要确认的字数', default=0)

    class Meta:
        verbose_name = '实体藏经页'
        verbose_name_plural = '实体藏经页'

    def __str__(self):
        return '%s第%s册第%s页' % (self.reel, self.vol_no, self.page_no)

