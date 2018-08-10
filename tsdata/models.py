from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
# from .lib.fields import JSONField
# from .lib.image_name_encipher import get_signed_path
from PIL import Image, ImageFont, ImageDraw
from io import BytesIO
import json
import urllib.request
from jwt_auth.models import Staff


class BaseData(models.Model):
    creator = models.ForeignKey(Staff, verbose_name='创建人', blank=True, null=True, on_delete=models.SET_NULL,
                                related_name='%(app_label)s_%(class)s_creator')
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    updater = models.ForeignKey(Staff, verbose_name='更新人', null=True, blank=True, on_delete=models.SET_NULL,
                                related_name='%(app_label)s_%(class)s_updater')
    update_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        abstract = True


class Tripitaka(BaseData):
    tid = models.CharField(verbose_name='编码', max_length=2, blank=False, unique=True)
    name = models.CharField(verbose_name='藏名', max_length=16, blank=False)
    shortname = models.CharField(verbose_name='简称', max_length=32, blank=False)
    remark = models.TextField('备注', blank=True, default='')

    class Meta:
        verbose_name = '实体藏'
        verbose_name_plural = '实体藏'

    def __str__(self):
        return self.name


class Volume(BaseData):
    tripitaka = models.ForeignKey(Tripitaka, on_delete=models.CASCADE, verbose_name='藏名')
    vid = models.CharField(verbose_name='册编码', max_length=12, blank=True, null=True)
    vol_no = models.SmallIntegerField(verbose_name='册序号')
    total_pages = models.IntegerField(verbose_name='总页数')
    cur_pages = models.IntegerField(verbose_name='实际页数')
    remark = models.TextField('备注', default='')

    class Meta:
        verbose_name = u"实体册"
        verbose_name_plural = u"实体册"
        unique_together = (('tripitaka', 'vol_no'),)

    def __str__(self):
        return '%s/第%s册' % (self.tripitaka.name, self.vol_no)


class LQSutra(BaseData):
    sid = models.CharField(verbose_name='编码', max_length=8, unique=True)  # （为"LQ"+ 经序号 + 别本号）
    sutra_no = models.CharField(verbose_name='经序号', max_length=5, blank=False)
    sutra_variant_no = models.CharField(verbose_name='别本号', max_length=1, default='0')
    name = models.CharField(verbose_name='经名', max_length=64, blank=False)
    total_reels = models.IntegerField(verbose_name='总卷数', blank=True, default=1)
    cur_reels = models.IntegerField(verbose_name='实际卷数', blank=True, default=1)
    author = models.CharField(verbose_name='著译者', max_length=255, blank=True)
    remark = models.TextField('备注', blank=True, default='')

    class Meta:
        verbose_name = u"龙泉经"
        verbose_name_plural = u"龙泉经"

    def __str__(self):
        return self.name


class LQReel(BaseData):
    lqsutra = models.ForeignKey(LQSutra, verbose_name='龙泉经编码', on_delete=models.CASCADE)
    # LQ000010_2
    rid = models.CharField(verbose_name='编码', editable=True, max_length=20, unique=True)
    reel_no = models.SmallIntegerField('卷序号')
    start_vol = models.SmallIntegerField('起始册')
    start_vol_page = models.SmallIntegerField('起始页')
    end_vol = models.SmallIntegerField('终止册')
    end_vol_page = models.SmallIntegerField('终止页')
    is_existed = models.BooleanField(verbose_name='是否存在', default=True)
    remark = models.TextField('备注', blank=True, default='')

    class Meta:
        verbose_name = '龙泉卷'
        verbose_name_plural = '龙泉卷'
        unique_together = (('lqsutra', 'reel_no'),)
        ordering = ('id',)

    def __str__(self):
        return '%s (第%s卷)' % (self.lqsutra, self.reel_no)


class Sutra(BaseData):
    sid = models.CharField(verbose_name='编码', editable=True, max_length=8, unique=True)
    tripitaka = models.ForeignKey(Tripitaka, on_delete=models.CASCADE, verbose_name='藏名')
    lqsutra = models.ForeignKey(LQSutra, verbose_name='龙泉经编码', null=True,
                                blank=True, on_delete=models.SET_NULL)  # （为"LQ"+ 经序号 + 别本号）
    sutra_no = models.CharField(verbose_name='经序号', max_length=5, blank=False)
    variant_variant_no = models.CharField(verbose_name='别本号', max_length=1, default='0')
    name = models.CharField(verbose_name='经名', max_length=64, blank=True)
    total_reels = models.IntegerField(verbose_name='总卷数', blank=True, default=1)
    cur_reels = models.IntegerField(verbose_name='实际卷数', blank=True, default=1)
    author = models.CharField('著译者', max_length=32, blank=True, default='')
    remark = models.TextField('备注', blank=True, default='')

    class Meta:
        verbose_name = '实体经'
        verbose_name_plural = '实体经'

    def __str__(self):
        return self.name


class Reel(BaseData):
    sutra = models.ForeignKey(Sutra, verbose_name='实体经', on_delete=models.CASCADE, editable=False)
    # YB000860_1
    rid = models.CharField(verbose_name='卷编码', editable=True, max_length=20, unique=True)
    reel_no = models.SmallIntegerField('卷序号')
    start_vol = models.SmallIntegerField('起始册')
    start_vol_page = models.SmallIntegerField('起始页')
    end_vol = models.SmallIntegerField('终止册')
    end_vol_page = models.SmallIntegerField('终止页')
    remark = models.TextField('备注', blank=True, default='')
    has_extra = models.BooleanField(verbose_name='是否有内部结构', default=False)

    class Meta:
        verbose_name = '实体卷'
        verbose_name_plural = '实体卷'
        unique_together = (('sutra', 'reel_no'),)
        ordering = ('id',)

    @property
    def name(self):
        return u"第%s卷" % (self.reel_no,)

    def __str__(self):
        return '%s/第%d卷' % (self.sutra, self.reel_no)

    @classmethod
    def is_overlapping(cls, reel1, reel2):
        if reel1.start_vol == reel2.start_vol and \
                reel1.end_vol_page >= reel2.start_vol_page:
            return True
        return False


class ReelExtraType:
    # 正文
    TYPE_BODY = 0
    # 序
    TYPE_PREFACE = 1
    # 跋
    TYPE_EPILOGUE = 2

    CHOICES = ((TYPE_BODY, "正文"), (TYPE_PREFACE, "序"), (TYPE_EPILOGUE, "跋"))

    value_to_desc = {
        TYPE_BODY: '正文',
        TYPE_PREFACE: '序',
        TYPE_EPILOGUE: '跋'
    }

    @classmethod
    def get_type_desc(cls, type):
        cls.value_to_desc.get(type, '无效类型')


class ReelExtra(BaseData):
    reel = models.ForeignKey(Reel, verbose_name='实体卷', on_delete=models.CASCADE, editable=False)
    typ = models.SmallIntegerField(verbose_name='卷内类型', choices=ReelExtraType.CHOICES, default=ReelExtraType.TYPE_BODY)
    inner_no = models.IntegerField('内部序号')
    name = models.CharField(verbose_name='标题', max_length=100)
    start_vol = models.SmallIntegerField('起始册')
    start_vol_page = models.SmallIntegerField('起始页')
    end_vol = models.SmallIntegerField('终止册')
    end_vol_page = models.SmallIntegerField('终止页')
    remark = models.TextField('备注', blank=True, default='')

    class Meta:
        verbose_name = '实体卷内部结构'
        verbose_name_plural = '实体卷内部结构'
        unique_together = (('reel', 'typ', 'inner_no'),)
        ordering = ('id',)

    def __str__(self):
        return '%s/%s/%d' % (self.reel, ReelExtraType.get_type_desc(self.typ), self.inner_no)


class PageTyp(object):
    COVER = 1
    BODY = 2
    BACK = 3
    PAGETYPCHOICES = (
        (COVER, '封面'),
        (BODY, '经文'),
        (BACK, '封底')
    )

class Page(BaseData):
    pid = models.CharField(verbose_name='编码', max_length=30, blank=True, null=True)
    page_code = models.CharField(max_length=24, blank=False, verbose_name='页代码')
    typ = models.SmallIntegerField(verbose_name='页类型', choices=PageTyp.PAGETYPCHOICES, default=PageTyp.BODY)
    reel = models.ForeignKey(Reel, verbose_name='实体卷', on_delete=models.CASCADE, editable=False, null=True, blank=True)
    reel_page_no = models.SmallIntegerField('卷页序号', null=True, blank=True)
    volume = models.ForeignKey(Volume, verbose_name='实体册', on_delete=models.CASCADE, editable=False)
    volume_page_no = models.SmallIntegerField('册页序号')
    is_existed = models.BooleanField(verbose_name='页是否存在', default=True)

    class Meta:
        verbose_name = '实体页'
        verbose_name_plural = '实体页'

    def __str__(self):
        return '%s/第%s页' % (self.reel, self.reel_page_no)
