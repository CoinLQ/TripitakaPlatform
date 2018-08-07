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
    creator = models.ForeignKey(Staff, verbose_name='创建人', blank=True, null=True,on_delete=models.CASCADE)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    updater = models.ForeignKey(Staff, null=True, blank=True, on_delete=models.SET_NULL, related_name='updater')
    update_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    class Meta:
        abstract = True


class Tripitaka(BaseData):
    code = models.CharField(verbose_name='编码', max_length=2, blank=False, unique=True)
    name = models.CharField(verbose_name='藏名', max_length=32, blank=False)
    shortname = models.CharField(verbose_name='简称（用于校勘记）', max_length=32, blank=False)
    remark = models.TextField('备注', blank=True, default='')

    class Meta:
        verbose_name = '实体藏'
        verbose_name_plural = '实体藏'

    def __str__(self):
        return '{} ({})'.format(self.name, self.code)


class Volume(BaseData):
    tripitaka = models.ForeignKey(Tripitaka, on_delete=models.CASCADE, verbose_name='藏名')
    vol_no = models.SmallIntegerField(verbose_name='册序号')
    total_pages = models.IntegerField(verbose_name='册页数')
    cur_pages = models.IntegerField(verbose_name='实际页数')
    remark = models.TextField('备注', default='')

    class Meta:
        verbose_name = u"实体册"
        verbose_name_plural = u"实体册"
        unique_together = (('tripitaka', 'vol_no'),)

    def __str__(self):
        return '%s: 第%s册' % (self.tripitaka.name, self.vol_no)
 

class LQSutra(BaseData):
    sid = models.CharField(verbose_name='龙泉经号', max_length=8, unique=True)  # （为"LQ"+ 经序号 + 别本号）
    code = models.CharField(verbose_name='龙泉经目编码', max_length=5, blank=False)
    variant_code = models.CharField(verbose_name='别本号', max_length=1, default='0')
    name = models.CharField(verbose_name='龙泉经名', max_length=64, blank=False)
    total_reels = models.IntegerField(verbose_name='总卷数', blank=True, default=1)
    cur_reels = models.IntegerField(verbose_name='实际卷数', blank=True, default=1)
    author = models.CharField(verbose_name='著译者', max_length=255, blank=True)
    remark = models.TextField('备注', blank=True, default='')

    class Meta:
        verbose_name = u"龙泉经目"
        verbose_name_plural = u"龙泉经目"

    def __str__(self):
        return '%s: %s' % (self.sid, self.name)


class LQReel(BaseData):
    lqsutra = models.ForeignKey(LQSutra, verbose_name='龙泉经目编码', on_delete=models.CASCADE)
    reel_no = models.SmallIntegerField('卷序号')
    start_vol = models.SmallIntegerField('起始册')
    start_vol_page = models.SmallIntegerField('起始页码')
    end_vol = models.SmallIntegerField('终止册')
    end_vol_page = models.SmallIntegerField('终止页码')    
    is_existed= models.BooleanField(verbose_name='卷是否存在', default=True)
    remark = models.TextField('备注', blank=True, default='')

    class Meta:
        verbose_name = '龙泉藏经卷'
        verbose_name_plural = '龙泉藏经卷'
        unique_together = (('lqsutra', 'reel_no'),)
        ordering = ('id',)

    def __str__(self):
        return '%s (第%s卷)' % (self.lqsutra, self.reel_no)


class Sutra(BaseData):
    sid = models.CharField(verbose_name='经编码', editable=True, max_length=8, unique=True)
    tripitaka = models.ForeignKey(Tripitaka, on_delete=models.CASCADE, verbose_name='藏名')
    lqsutra = models.ForeignKey(LQSutra, verbose_name='龙泉经目编码', null=True,
                                blank=True, on_delete=models.SET_NULL)  # （为"LQ"+ 经序号 + 别本号）
    code = models.CharField(verbose_name='实体经目编码', max_length=5, blank=False)
    variant_code = models.CharField(verbose_name='别本编码', max_length=1, default='0')
    name = models.CharField(verbose_name='经名', max_length=64, blank=True)
    total_reels = models.IntegerField(verbose_name='总卷数', blank=True, default=1)
    cur_reels = models.IntegerField(verbose_name='实际卷数', blank=True, default=1)
    author = models.CharField('作译者', max_length=32, blank=True, default='')
    remark = models.TextField('备注', blank=True, default='')

    class Meta:
        verbose_name = '实体经'
        verbose_name_plural = '实体经'

    def __str__(self):
        return '%s / %s' % (self.tripitaka, self.name)


class Reel(BaseData):
    sutra = models.ForeignKey(Sutra, verbose_name='实体经', on_delete=models.CASCADE, editable=False)
    reel_no = models.SmallIntegerField('卷序号')
    start_vol = models.SmallIntegerField('起始册')
    start_vol_page = models.SmallIntegerField('起始页码')
    end_vol = models.SmallIntegerField('终止册')
    end_vol_page = models.SmallIntegerField('终止页码')
    remark = models.TextField('备注', blank=True, default='')

    class Meta:
        verbose_name = '实体卷'
        verbose_name_plural = '实体卷'
        unique_together = (('sutra', 'reel_no'),)
        ordering = ('id',)

    @property
    def name(self):
        return u"第%s卷" % (self.reel_no,)

    def __str__(self):
        return '%s / 第%d卷' % (self.sutra, self.reel_no)

    @classmethod
    def is_overlapping(cls, reel1, reel2):
        if reel1.start_vol == reel2.start_vol and \
                        reel1.end_vol_page >= reel2.start_vol_page:
            return True
        return False


class Page(BaseData):
    pid = models.CharField(verbose_name='实体藏经页级总编码', max_length=21, blank=False, primary_key=True)
    page_code = models.CharField(max_length=23, blank=False)
    volumn = models.ForeignKey(Volume, verbose_name='实体藏经册', on_delete=models.CASCADE, editable=False)
    reel = models.ForeignKey(Reel, verbose_name='实体藏经卷', on_delete=models.CASCADE, editable=False)
    reel_page_no = models.SmallIntegerField('卷中页序号')
    volume_page_no = models.SmallIntegerField('页序号')
    is_existed = models.BooleanField(verbose_name='页是否存在', default=True)

    class Meta:
        verbose_name = '实体藏经页'
        verbose_name_plural = '实体藏经页'

    def __str__(self):
        return '%s / 第%s页' % (self.reel, self.reel_page_no)
