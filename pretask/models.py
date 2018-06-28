from rect.models import Schedule, RTask, OpStatus
from django.db import models

import uuid
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from jwt_auth.models import Staff
from django.utils.timezone import localtime, now
from functools import wraps
from django.db import connection, transaction
from django.db.models import Min, Sum, Case, When, Value, Count, F
from django_bulk_update.manager import BulkUpdateManager

from dotmap import DotMap
from PIL import Image, ImageFont, ImageDraw
import os, sys

from tdata.lib.fields import JSONField
from tdata.models import *

import inspect
class PrePage(models.Model):
    bar_info = JSONField(verbose_name='切分信息', default=list)
    text = models.TextField('文本信息', default='', blank=True)
    image_url = models.CharField('图片地址', max_length=128, blank=False)
    page_info = models.CharField('页面信息', max_length=128, blank=True)
    
class PrePageColVerifyTask(RTask):
    schedule = models.ForeignKey(Schedule, null=True, blank=True, related_name='pagecolverify_tasks', on_delete=models.SET_NULL,
                                 verbose_name=u'切分计划')
    current_x = models.IntegerField("当前块X坐标", default=0)
    current_y = models.IntegerField("当前块Y坐标", default=0)
    owner = models.ForeignKey(Staff, null=True, blank=True, related_name='pagecolverify_tasks', on_delete=models.SET_NULL)
    page = models.ForeignKey(PrePage, null=True, blank=True, on_delete=models.SET_NULL)
    column_count = models.IntegerField(null=True, blank=True, verbose_name=u'最大列数') # 最大文本长度
    rect_set = JSONField(default=list, verbose_name=u'切字列块JSON切分数据集')

    class Meta:
        verbose_name = u"切分预处理校对审定"
        verbose_name_plural = u"切分预处理校对审定"

    class Config:
        list_display_fields = ('number', 'result', 'created_at')
        list_form_fields = list_display_fields
        search_fields = ('number', 'page__reel__sutra__name', 'page__reel__sutra__tripitaka__name', 'page__reel__sutra__tripitaka__code', '=page__reel__reel_no')

class PrePageColTask(RTask):
    schedule = models.ForeignKey(Schedule, null=True, blank=True, related_name='pagecol_tasks', on_delete=models.SET_NULL,
                                 verbose_name=u'切分计划')
    current_x = models.IntegerField("当前块X坐标", default=0)
    current_y = models.IntegerField("当前块Y坐标", default=0)
    owner = models.ForeignKey(Staff, null=True, blank=True, related_name='pagecol_tasks', on_delete=models.SET_NULL)
    page = models.ForeignKey(PrePage, null=True, blank=True, on_delete=models.SET_NULL)
    column_count = models.IntegerField(null=True, blank=True, verbose_name=u'最大列数') # 最大文本长度
    rect_set = JSONField(default=list, verbose_name=u'切字列块JSON切分数据集')
    
    class Meta:
        verbose_name = u"切分预处理校对"
        verbose_name_plural = u"切分预处理校对"

    class Config:
        list_display_fields = ('number', 'result', 'created_at')
        list_form_fields = list_display_fields
        search_fields = ('number', 'page__reel__sutra__name', 'page__reel__sutra__tripitaka__name', 'page__reel__sutra__tripitaka__code', '=page__reel__reel_no')

    def task_id(self):
        cursor = connection.cursor()
        cursor.execute("select nextval('task_seq')")
        result = cursor.fetchone()
        return result[0]

    def roll_new_task(self):
        task_no = "%s_%s_%05X" % (self.number.split('_')[0], self.number.split('_')[1], self.task_id())
        task = PrePageColTask(number=task_no, schedule=self.schedule, ttype=SliceType.PPAGE, page=self.page, priority=PriorityLevel.HIGH,
                                rect_set=self.rect_set, status=TaskStatus.NOT_GOT,
                                redo_count=pagerect.pptask_count)
        task.save()
        pagerect.save(update_fields=['pptask_count'])
    
    def create_new_pagetask_verify(self):
        if not PrePageColVerifyTask.objects.filter(schedule=self.schedule, page=self.page).first():
            task_no = "%s_%s_%05X" % (self.number.split('_')[0], self.number.split('_')[1], self.task_id())
            task = PrePageColVerifyTask(number=task_no, schedule=self.schedule, ttype=SliceType.PPAGE, page=self.page,
                                    status=TaskStatus.NOT_GOT,
                                    rect_set=self.rect_set, redo_count=pagerect.pptask_count)
            task.save()
    

#@iterable
class ColRect(models.Model):
    # https://github.com/aykut/django-bulk-update
    objects = BulkUpdateManager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    cid = models.CharField(verbose_name=u'经字号', max_length=32, db_index=True) # 字ID YB000860_001_01_0_01_01
    page = models.ForeignKey(PrePage, null=True, blank=True, on_delete=models.SET_NULL)
    char_no = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name=u'字号', default=0)
    line_no = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name=u'行号', default=0)  # 对应图片的一列

    op = models.PositiveSmallIntegerField(verbose_name=u'操作类型', default=OpStatus.NORMAL)
    x = models.PositiveSmallIntegerField(verbose_name=u'X坐标', default=0)
    y = models.PositiveSmallIntegerField(verbose_name=u'Y坐标', default=0)
    w = models.IntegerField(verbose_name=u'宽度', default=1)
    h = models.IntegerField(verbose_name=u'高度', default=1)

    cc = models.FloatField(null=True, blank=True, verbose_name=u'切分置信度', default=1)
    ch = models.CharField(null=True, blank=True, verbose_name=u'文字', max_length=16, default='')
    wcc = models.FloatField(null=True, blank=True, verbose_name=u'识别置信度', default=1)

    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)


    class DefaultDict(dict):

        def __missing__(self, key):
            return None

    @property
    def rect_sn(self):
        return "%s_L%02d" % (self.page_pid, self.line_no)

    def __str__(self):
        return self.ch

    @staticmethod
    def canonicalise_uuid(uuid):
        import re
        uuid = str(uuid)
        _uuid_re = re.compile(r'^[0-9A-Fa-f]{8}-(?:[0-9A-Fa-f]{4}-){3}[0-9A-Fa-f]{12}$')
        _hex_re = re.compile(r'^[0-9A-Fa-f]{32}$')
        if _uuid_re.match(uuid):
            return uuid.upper()
        if _hex_re.match(uuid):
            return '-'.join([uuid[0:8], uuid[8:12], uuid[12:16],
                            uuid[16:20], uuid[20:]]).upper()
        return None

    @property
    def serialize_set(self):
        return dict((k, v) for k, v in self.__dict__.items() if not k.startswith("_"))

    @staticmethod
    def generate(rect_dict={}, exist_rects=[]):
        _dict = ColRect.DefaultDict()
        for k, v in rect_dict.items():
            _dict[k] = v

        ## 此处处理重复添加，对于已有的exist_rects，将更新旧的Rect，不再生成新的Rect实例
        if type(_dict['id']).__name__ == "UUID":
            _dict['id'] = _dict['id'].hex
        try:
            el = list(filter(lambda x: x.id.hex == _dict['id'].replace('-', ''), exist_rects))
            rect = el[0]
        except:
            rect = ColRect()

        ## 此处处理外部API提供的字典数据，过滤掉非model定义交集的部分。
        valid_keys = rect.serialize_set.keys()-['id']
        key_set = set(valid_keys).intersection(_dict.keys())
        for key in key_set:
            if key in valid_keys:
                setattr(rect, key, _dict[key])
        rect.updated_at = localtime(now())
        ## 此处根据已有的page_pid, line_no, char_no,生成新的cid
        rect.cid = rect.rect_sn

        rect = ColRect.normalize(rect)
        return rect

    @staticmethod
    def bulk_insert_or_replace(rects):
        updates = []
        news = []
        ids = [r['id'] for r in filter(lambda x: ColRect.canonicalise_uuid(DotMap(x).id), rects)]
        exists = ColRect.objects.filter(id__in=ids)
        for r in rects:
            rect = ColRect.generate(r, exists)
            if (rect._state.adding):
                news.append(rect)
            else:
                updates.append(rect)
        ColRect.objects.bulk_create(news)
        ColRect.objects.bulk_update(updates)

    @staticmethod
    def _normalize(r):
        if (not r.w):
            r.w = 1
        if (not r.h):
            r.h = 1

        if (r.w < 0):
            r.x = r.x + r.w
            r.w = abs(r.w)
        if (r.h < 0):
            r.y = r.y + r.h
            r.h = abs(r.h)
        return r

    @staticmethod
    def normalize(r):
        if isinstance(r, dict):
            r = DotMap(r)
        r = ColRect._normalize(r)
        if isinstance(r, DotMap):
            r = r.toDict()
        return r

    @staticmethod
    def direct_delete_rects(rects, t):
        rect_ids = [rect ['id'] for rect in filter(lambda x: x['op'] == 3, rects)]
        ColRect.objects.filter(id__in=rect_ids).delete()

    class Meta:
        verbose_name = u"源-切字列区"
        verbose_name_plural = u"源-切字列区管理"
        ordering = ('-cc',)


@receiver(pre_save, sender=ColRect)
def positive_w_h_fields(sender, instance, **kwargs):
    instance = ColRect.normalize(instance)
