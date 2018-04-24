# -*- coding: UTF-8 -*-
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
from .lib.arrange_rect import ArrangeRect
from django.forms.models import model_to_dict
from django.conf import settings
from background_task import background

from dotmap import DotMap
from PIL import Image, ImageFont, ImageDraw
from celery import shared_task
from TripitakaPlatform import email_if_fails
from tasks.utils.cut_column import gene_new_col
import os, sys

from tdata.lib.fields import JSONField
from tdata.models import *

import inspect


def disable_for_create_cut_task(signal_handler):
    @wraps(signal_handler)
    def wrapper(*args, **kwargs):
        for fr in inspect.stack():
            if inspect.getmodulename(fr[1]) == 'create_cut_task':
                return
        signal_handler(*args, **kwargs)
    return wrapper

def iterable(cls):
    """
    model的迭代器并输出dict，且不包含内部__,_开头的key
    """
    @wraps(cls)
    def iterfn(self):
        iters = dict((k, v) for k, v in self.__dict__.items() if not k.startswith("_"))

        for k, v in iters.items():
            yield k, v

    cls.__iter__ = iterfn
    return cls

class SliceType(object):
    PPAGE = 1
    CC = 2
    CLASSIFY = 3
    CHECK = 4
    VDEL = 5
    REVIEW = 6
    CHOICES = (
        (CC, u'置信度'),
        (PPAGE, u'顺序校对'),
        (CLASSIFY, u'聚类'),
        (CHECK, u'差缺补漏'),
        (VDEL, u'删框'),
        (REVIEW, u'反馈审查'),
    )


class ScheduleStatus:
    NOT_ACTIVE = 0
    ACTIVE = 1
    EXPIRED = 2
    DISCARD = 3
    COMPLETED = 4
    CHOICES = (
        (NOT_ACTIVE, u'未激活'),
        (ACTIVE, u'已激活'),
        (EXPIRED, u'已过期'),
        (DISCARD, u'已作废'),
        (COMPLETED, u'已完成'),
    )

class TaskStatus:
    NOT_READY = 0
    NOT_GOT = 1
    EXPIRED = 2
    ABANDON = 3
    EMERGENCY = 4
    HANDLING = 5
    COMPLETED = 7
    DISCARD = 9

    CHOICES = (
        (NOT_READY, u'未就绪'),
        (NOT_GOT, u'未领取'),
        (EXPIRED, u'已过期'),
        (ABANDON, u'已放弃'),
        (EMERGENCY, u'加急'),
        (HANDLING, u'处理中'),
        (COMPLETED, u'已完成'),
        (DISCARD, u'已作废'),
    )
    #未完成状态.
    remain_status = [NOT_READY, NOT_GOT, EXPIRED, ABANDON, HANDLING]

class PriorityLevel:
    LOW = 1
    MIDDLE = 3
    HIGH = 5
    HIGHEST = 7

    CHOICES = (
        (LOW, u'低'),
        (MIDDLE, u'中'),
        (HIGH, u'高'),
        (HIGHEST, u'最高'),
    )

class OpStatus(object):
    NORMAL = 1
    CHANGED = 2
    DELETED = 3
    RECOG = 4
    COLLATE = 5
    CHOICES = (
        (NORMAL, u'正常'),
        (CHANGED, u'被更改'),
        (DELETED, u'被删除'),
        (RECOG, u'文字识别'),
        (COLLATE, u'文字校对')
    )

class ReviewResult(object):
    INITIAL = 0
    AGREE = 1
    DISAGREE = 2
    IGNORED = 3
    CHOICES = (
        (INITIAL, u'未审阅'),
        (AGREE, u'已同意'),
        (DISAGREE, u'未同意'),
        (IGNORED, u'被略过'),
    )

class ModelDiffMixin(object):
    """
    A model mixin that tracks model fields' values and provide some useful api
    to know what fields have been changed.
    """

    def __init__(self, *args, **kwargs):
        super(ModelDiffMixin, self).__init__(*args, **kwargs)
        self.__initial = self._dict

    @property
    def diff(self):
        d1 = self.__initial
        d2 = self._dict
        diffs = [(k, (v, d2[k])) for k, v in d1.items() if v != d2[k]]
        return dict(diffs)

    @property
    def has_changed(self):
        return bool(self.diff)

    @property
    def changed_fields(self):
        return self.diff.keys()

    def get_field_diff(self, field_name):
        """
        Returns a diff for field if it's changed and None otherwise.
        """
        return self.diff.get(field_name, None)

    def save(self, *args, **kwargs):
        """
        Saves model and set initial state.
        """
        super(ModelDiffMixin, self).save(*args, **kwargs)
        self.__initial = self._dict

    @property
    def _dict(self):
        return model_to_dict(self, fields=[field.name for field in
                             self._meta.fields])

class TripiMixin(object):
    def __str__(self):
        return self.name

class PageRect(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) # TODO: confirm
    page = models.ForeignKey(Page, null=True, blank=True, related_name='pagerects', on_delete=models.SET_NULL,
                             verbose_name=u'关联源页信息')
    reel = models.ForeignKey(Reel, null=True, blank=True, related_name='reels', on_delete=models.SET_NULL)
    op = models.PositiveSmallIntegerField(db_index=True, verbose_name=u'操作类型', default=OpStatus.NORMAL)
    line_count = models.IntegerField(null=True, blank=True, verbose_name=u'最大行数') # 最大文本行号
    column_count = models.IntegerField(null=True, blank=True, verbose_name=u'最大列数') # 最大文本长度
    rect_set = JSONField(default=list, verbose_name=u'切字块JSON切分数据集')
    created_at = models.DateTimeField(null=True, blank=True, verbose_name=u'创建时间', auto_now_add=True)
    primary = models.BooleanField(verbose_name="主切分方案", default=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = u"源页切分集"
        verbose_name_plural = u"源页切分集管理"
        ordering = ('id',)

    @property
    def serialize_set(self):
        return dict((k, v) for k, v in self.__dict__.items() if not k.startswith("_"))


    def rebuild_rect(self):
        if len(self.rect_set) == 0:
            return
        Rect.objects.filter(page_pid=self.page_id).all().delete()
        return PageRect.align_rects_bypage(self, self.rect_set)

    @classmethod
    def reformat_rects(cls, page_pid):
        ret = True
        rects = Rect.objects.filter(page_pid=page_pid).all()
        pagerect = PageRect.objects.filter(page_id=page_pid).first()
        if rects.count() == 0:
            return ret
        return PageRect.align_rects_bypage(pagerect, rects)

    @classmethod
    def align_rects_bypage(cls, pagerect, rects):
        tp = str(pagerect.reel)[0:2]
        ret = True
        columns = ArrangeRect.resort_rects_from_qs(rects, tp)
        page = pagerect.page
        image_name_prefix = page.reel.image_prefix() + str(page.page_no)
        flat_list = [item for sublist in columns for item in sublist]
        rect_list = list()
        for lin_n, line in enumerate(columns, start=1):
            for col_n, _r in enumerate(line, start=1):
                _rect = _r
                _rect['line_no'] = lin_n
                _rect['char_no'] = col_n
                _rect['page_pid'] = pagerect.page_id
                _rect['reel_id'] = pagerect.reel_id
                try :
                    # 这里以左上角坐标，落在哪个列数据为准
                    if not page.bar_info:
                        page.bar_info = gene_new_col(image_name_prefix, flat_list)
                        page.save()
                    column_dict = (item for item in page.bar_info if item["x"] <= _rect['x'] and _rect['x'] <= item["x1"] and
                                                item["y"] <= _rect['y'] and _rect['y'] <= item["y1"] ).__next__()
                    _rect['column_set'] = column_dict
                except:
                    ret = False
                _rect = Rect.normalize(_rect)
                rect_list.append(_rect)
        Rect.bulk_insert_or_replace(rect_list)
        pagerect.line_count = max(map(lambda Y: Y['line_no'], rect_list))
        pagerect.column_count = max(map(lambda Y: Y['char_no'], rect_list))
        pagerect.save()
        return ret

    def make_annotate(self):
        source_img = self.page._remote_image_stream().convert("RGBA")
        work_dir = "/tmp/annotations"
        try:
            os.stat(work_dir)
        except:
            os.makedirs(work_dir)
        out_file = "%s/%s.jpg" % (work_dir, self.page_id)
        # make a blank image for the rectangle, initialized to a completely transparent color
        tmp = Image.new('RGBA', source_img.size, (0, 0, 0, 0))
        # get a drawing context for it
        draw = ImageDraw.Draw(tmp)
        if sys.platform in ('linux2', 'linux'):
            myfont = ImageFont.truetype(settings.BASE_DIR + "/static/fonts/SourceHanSerifTC-Bold.otf", 11)
        elif sys.platform == 'darwin':
            myfont = ImageFont.truetype("/Library/Fonts/Songti.ttc", 12)
        tp = str(self.reel)[0:2]
        columns = ArrangeRect.resort_rects_from_qs(self.rect_set, tp)
        for lin_n, line in enumerate(columns, start=1):
            for col_n, _r in enumerate(line, start=1):
                rect = DotMap(_r)
                # draw a semi-transparent rect on the temporary image
                draw.rectangle(((rect.x, rect.y), (rect.x + int(rect.w), rect.y + int(rect.h))),
                                 fill=(0, 0, 0, 120))
                anno_str = u"%s-%s" % (lin_n, col_n)
                draw.text((rect.x, rect.y), anno_str, font=myfont, fill=(255, 0, 120))
        source_img = Image.alpha_composite(source_img, tmp)
        source_img.save(out_file, "JPEG")


@iterable
class Rect(models.Model):
    # https://github.com/aykut/django-bulk-update
    objects = BulkUpdateManager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    cid = models.CharField(verbose_name=u'经字号', max_length=32, db_index=True) # 字ID YB000860_001_01_0_01_01
    reel = models.ForeignKey(Reel, null=True, blank=True, related_name='rects', on_delete=models.SET_NULL)
    page_pid = models.CharField(max_length=23, blank=False, verbose_name=u'关联源页pid', db_index=True)
    column_set = JSONField(default=list, verbose_name=u'切字块所在切列JSON数据集')
    char_no = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name=u'字号', default=0)
    line_no = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name=u'行号', default=0)  # 对应图片的一列

    op = models.PositiveSmallIntegerField(verbose_name=u'操作类型', default=OpStatus.NORMAL)
    x = models.PositiveSmallIntegerField(verbose_name=u'X坐标', default=0)
    y = models.PositiveSmallIntegerField(verbose_name=u'Y坐标', default=0)
    w = models.IntegerField(verbose_name=u'宽度', default=1)
    h = models.IntegerField(verbose_name=u'高度', default=1)

    cc = models.FloatField(null=True, blank=True, verbose_name=u'切分置信度', db_index=True, default=1)
    ch = models.CharField(null=True, blank=True, verbose_name=u'文字', max_length=2, default='', db_index=True)
    wcc = models.FloatField(null=True, blank=True, verbose_name=u'识别置信度', default=1, db_index=True)
    ts = models.CharField(null=True, blank=True, verbose_name=u'标字', max_length=2, default='') #TODO: confirm
    s3_inset = models.FileField(max_length=256, blank=True, null=True, verbose_name=u's3地址', upload_to='tripitaka/hans',
                                  storage='storages.backends.s3boto.S3BotoStorage')
    updated_at = models.DateTimeField(verbose_name='更新时间1', auto_now=True)
    #s3_id = models.CharField(verbose_name='图片路径', max_length=128, default='', blank=False)

    class DefaultDict(dict):

        def __missing__(self, key):
            return None

    @property
    def rect_sn(self):
        return "%s_%02d_%02d" % (self.page_pid, self.line_no, self.char_no)

    def __str__(self):
        return self.ch

    def column_uri(self):
        return Rect.column_uri_path(self.column_set['col_id'])

    @staticmethod
    def column_uri_path(col_s3_id):
        col_id = str(col_s3_id)
        col_path = col_id.replace('_', '/')
        return '%s/%s/%s.jpg' % (settings.COL_IMAGE_URL_PREFIX, os.path.dirname(col_path), col_id)

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
        _dict = Rect.DefaultDict()
        for k, v in rect_dict.items():
            _dict[k] = v

        ## 此处处理重复添加，对于已有的exist_rects，将更新旧的Rect，不再生成新的Rect实例
        if type(_dict['id']).__name__ == "UUID":
            _dict['id'] = _dict['id'].hex
        try:
            el = list(filter(lambda x: x.id.hex == _dict['id'].replace('-', ''), exist_rects))
            rect = el[0]
        except:
            rect = Rect()

        ## 此处处理外部API提供的字典数据，过滤掉非model定义交集的部分。
        valid_keys = rect.serialize_set.keys()-['id']
        key_set = set(valid_keys).intersection(_dict.keys())
        for key in key_set:
            if key in valid_keys:
                setattr(rect, key, _dict[key])
        rect.updated_at = localtime(now())
        ## 此处根据已有的page_pid, line_no, char_no,生成新的cid
        rect.cid = rect.rect_sn
        ### 这里由于外部数据格式不规范，对char作为汉字的情况追加的。
        if _dict['char']:
            rect.ch = _dict['char']

        rect = Rect.normalize(rect)
        return rect

    @staticmethod
    def bulk_insert_or_replace(rects):
        updates = []
        news = []
        ids = [r['id'] for r in filter(lambda x: Rect.canonicalise_uuid(DotMap(x).id), rects)]
        exists = Rect.objects.filter(id__in=ids)
        for r in rects:
            rect = Rect.generate(r, exists)
            if (rect._state.adding):
                news.append(rect)
            else:
                updates.append(rect)
        Rect.objects.bulk_create(news)
        Rect.objects.bulk_update(updates)

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
        r = Rect._normalize(r)
        if isinstance(r, DotMap):
            r = r.toDict()
        return r

    class Meta:
        verbose_name = u"源-切字块"
        verbose_name_plural = u"源-切字块管理"
        ordering = ('-cc',)


@receiver(pre_save, sender=Rect)
def positive_w_h_fields(sender, instance, **kwargs):
    instance = Rect.normalize(instance)

class Patch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reel = models.ForeignKey(Reel, null=True, blank=True, related_name='patches', on_delete=models.CASCADE) # 注意：卷编码这里没有考虑余量
    op = models.PositiveSmallIntegerField(verbose_name=u'操作类型', default=OpStatus.NORMAL)
    x = models.PositiveSmallIntegerField(verbose_name=u'X坐标', default=0)
    y = models.PositiveSmallIntegerField(verbose_name=u'Y坐标', default=0)
    w = models.PositiveSmallIntegerField(verbose_name=u'宽度', default=1)
    h = models.PositiveSmallIntegerField(verbose_name=u'高度', default=1)
    ocolumn_uri = models.CharField(verbose_name='行图片路径', max_length=128, blank=False)
    ocolumn_x = models.PositiveSmallIntegerField(verbose_name=u'行图X坐标', default=0)
    ocolumn_y = models.PositiveSmallIntegerField(verbose_name=u'行图Y坐标', default=0)
    char_no = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name=u'字号', default=0)
    line_no = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name=u'行号', default=0)  # 对应图片的一列
    ch = models.CharField(null=True, blank=True, verbose_name=u'文字', max_length=2, default='')
    rect_id = models.CharField(verbose_name='字块CID', max_length=128, blank=False)
    rect_x = models.PositiveSmallIntegerField(verbose_name=u'原字块X坐标', default=0)
    rect_y = models.PositiveSmallIntegerField(verbose_name=u'原字块Y坐标', default=0)
    rect_w = models.PositiveSmallIntegerField(verbose_name=u'原字块宽度', default=1)
    rect_h = models.PositiveSmallIntegerField(verbose_name=u'原字块高度', default=1)
    ts = models.CharField(null=True, blank=True, verbose_name=u'修订文字', max_length=2, default='')
    result = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name=u'审定意见', default=ReviewResult.INITIAL)  # 1 同意 2 不同意
    modifier = models.ForeignKey(Staff, null=True, blank=True, related_name='modify_patches', verbose_name=u'修改人', on_delete=models.SET_NULL)
    verifier = models.ForeignKey(Staff, null=True, blank=True, related_name='verify_patches', verbose_name=u'审定人', on_delete=models.SET_NULL)

    submitted_at = models.DateTimeField(verbose_name='修订时间', auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True, verbose_name=u'更新时间', auto_now=True)

    def __str__(self):
        return self.ch

    class Meta:
        verbose_name = u"Patch"
        verbose_name_plural = u"Patch管理"
        ordering = ("ch",)


class Schedule(models.Model, ModelDiffMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reels = models.ManyToManyField(Reel, limit_choices_to={'image_ready': True,'cut_ready': False}, blank=True )
    name = models.CharField(verbose_name='计划名称', max_length=64)

    cc_threshold = models.FloatField("切分置信度阈值", default=0.65, blank=True)

    # todo 设置总任务的优先级时, 子任务包的优先级凡是小于总任务优先级的都提升优先级, 高于或等于的不处理. 保持原优先级.
    priority = models.PositiveSmallIntegerField(
        choices=PriorityLevel.CHOICES,
        default=PriorityLevel.MIDDLE,
        verbose_name=u'任务计划优先级',
    )
    status = models.PositiveSmallIntegerField(
        db_index=True,
        null=True,
        blank=True,
        choices=ScheduleStatus.CHOICES,
        default=ScheduleStatus.NOT_ACTIVE,
        verbose_name=u'计划状态',
    )
    due_at = models.DateField(null=True, blank=True, verbose_name=u'截止日期')
    created_at = models.DateTimeField(null=True, blank=True, verbose_name=u'创建日期', auto_now_add=True)
    remark = models.TextField(max_length=256, null=True, blank=True, verbose_name=u'备注')
    schedule_no = models.CharField(max_length=64, verbose_name=u'切分计划批次', default='', help_text=u'自动生成', blank=True)

    def __str__(self):
        return self.name
    
    @classmethod
    def create_reels_pptasks(cls, reel):
        schedule_name = "计划任务: %s" % ( str(reel), )
        schedule = Schedule.objects.create(name=schedule_name, status=ScheduleStatus.ACTIVE, schedule_no="schedule1", cc_threshold=0)
        schedule.refresh_from_db()
        schedule.reels.add(reel)
        schedule.reels.update(cut_ready=True)

        # NOTICE: 实际这里不必执行，多重关联这时并未创建成功。
        # 在数据库层用存储过程在关联表记录创建后，创建卷任务。
        # 为逻辑必要，留此函数
        # tasks = []
        # for reel in self.reels.all():
        #     tasks.append(Reel_Task_Statistical(schedule=self, reel=reel))
        # Reel_Task_Statistical.objects.bulk_create(tasks)

    class Meta:
        verbose_name = u"切分计划"
        verbose_name_plural = u"切分计划"
        ordering = ('due_at', "status")


def activity_log(func):
    @wraps(func)
    def tmp(*args, **kwargs):
        result = func(*args, **kwargs)
        self = args[0]
        # 暂无任务跟踪记录需求
        # ActivityLog(user=self.owner, object_pk=self.pk,
        #                                 object_type=type(self).__name__,
        #                                 action=func.__name__).save()
        return result
    return tmp


class Schedule_Task_Statistical(models.Model):
    schedule = models.ForeignKey(Schedule, null=True, blank=True, related_name='schedule_task_statis', on_delete=models.SET_NULL,
                                 verbose_name=u'切分计划')
    amount_of_cctasks = models.IntegerField(verbose_name=u'置信任务总数', default=-1)
    completed_cctasks = models.IntegerField(verbose_name=u'置信任务完成数', default=0)
    amount_of_classifytasks = models.IntegerField(verbose_name=u'聚类任务总数', default=-1)
    completed_classifytasks = models.IntegerField(verbose_name=u'聚类任务完成数', default=0)
    amount_of_absenttasks = models.IntegerField(verbose_name=u'查漏任务总数', default=-1)
    completed_absenttasks = models.IntegerField(verbose_name=u'查漏任务完成数', default=0)
    amount_of_pptasks = models.IntegerField(verbose_name=u'逐字任务总数', default=-1)
    completed_pptasks = models.IntegerField(verbose_name=u'逐字任务完成数', default=0)
    amount_of_vdeltasks = models.IntegerField(verbose_name=u'删框任务总数', default=-1)
    completed_vdeltasks = models.IntegerField(verbose_name=u'删框任务完成数', default=0)
    amount_of_reviewtasks = models.IntegerField(verbose_name=u'审定任务总数', default=-1)
    completed_reviewtasks = models.IntegerField(verbose_name=u'审定任务完成数', default=0)
    remark = models.TextField(max_length=256, null=True, blank=True, verbose_name=u'备注', default= '')
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = u"切分计划任务统计"
        verbose_name_plural = u"切分计划任务统计管理"
        ordering = ('schedule', )

class Reel_Task_Statistical(models.Model):
    schedule = models.ForeignKey(Schedule, null=True, blank=True, related_name='schedule_reel_task_statis',
                                 on_delete=models.SET_NULL, verbose_name=u'切分计划')
    reel = models.ForeignKey(Reel, related_name='reel_tasks_statis', on_delete=models.SET_NULL, null=True)
    amount_of_cctasks = models.IntegerField(verbose_name=u'置信任务总数', default=-1)
    completed_cctasks = models.IntegerField(verbose_name=u'置信任务完成数', default=0)
    amount_of_absenttasks = models.IntegerField(verbose_name=u'查漏任务总数', default=-1)
    completed_absenttasks = models.IntegerField(verbose_name=u'查漏任务完成数', default=0)
    amount_of_pptasks = models.IntegerField(verbose_name=u'逐字任务总数', default=-1)
    completed_pptasks = models.IntegerField(verbose_name=u'逐字任务完成数', default=0)

    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = u"总体进度"
        verbose_name_plural = u"总体进度"
        ordering = ('schedule', '-updated_at')

    #@shared_task
    @background(schedule=60)
    @email_if_fails
    def gen_pptask_by_plan():
        with transaction.atomic():
            for stask in Schedule_Task_Statistical.objects.filter(amount_of_pptasks=-1):
                # 逐卷创建任务
                for rtask in Reel_Task_Statistical.objects.filter(schedule=stask.schedule).prefetch_related('reel'):
                    if rtask.amount_of_pptasks != -1:
                        continue
                    count = allocateTasks(stask.schedule, rtask.reel, SliceType.PPAGE)
                    rtask.amount_of_pptasks = count * 2
                    rtask.save(update_fields=['amount_of_pptasks'])
                # 检查每卷大于-1，开启总计划，更新任务数。
                quertset = Reel_Task_Statistical.objects.filter(schedule=stask.schedule)
                result = quertset.aggregate(Min('amount_of_pptasks'))
                # 只有所有卷都开启任务，计划表的总任务数才更新。
                if result['amount_of_pptasks__min'] and result['amount_of_pptasks__min'] != -1:
                    count = quertset.aggregate(Sum('amount_of_pptasks'))['amount_of_pptasks__sum']
                    stask.amount_of_pptasks = count * 2
                    stask.save(update_fields=['amount_of_pptasks'])


    @shared_task
    @email_if_fails
    def gen_cctask_by_plan():
        with transaction.atomic():
            for stask in Schedule_Task_Statistical.objects.filter(amount_of_cctasks=-1):
                # 未激活说明，第一步的CC阈值没有填写
                if stask.schedule.status == ScheduleStatus.NOT_ACTIVE:
                    continue
                # 逐卷创建任务
                for rtask in Reel_Task_Statistical.objects.filter(schedule=stask.schedule).prefetch_related('reel'):
                    if rtask.amount_of_cctasks != -1:
                        continue
                    count = allocateTasks(stask.schedule, rtask.reel, SliceType.CC)
                    rtask.amount_of_cctasks = count
                    rtask.save(update_fields=['amount_of_cctasks'])
                # 检查每卷大于-1，开启总计划，更新任务数。
                quertset = Reel_Task_Statistical.objects.filter(schedule=stask.schedule)
                result = quertset.aggregate(Min('amount_of_cctasks'))
                # 只有所有卷都开启任务，计划表的总任务数才更新。
                if result['amount_of_cctasks__min'] != -1:
                    count = quertset.aggregate(Sum('amount_of_cctasks'))['amount_of_cctasks__sum']
                    stask.amount_of_cctasks = count
                    stask.save(update_fields=['amount_of_cctasks'])

class RTask(models.Model):
    '''
    切分校对计划的任务实例
    估计划激活后, 即后台自动据校对类型分配任务列表.
    '''
    number = models.CharField(primary_key=True, max_length=64, verbose_name='任务编号')
    ttype = models.PositiveSmallIntegerField(
        db_index=True,
        choices=SliceType.CHOICES,
        default=SliceType.PPAGE,
        verbose_name=u'切分方式',
    )
    desc = models.TextField(null=True, blank=True, verbose_name=u'任务格式化描述')
    status = models.PositiveSmallIntegerField(
        db_index=True,
        choices=TaskStatus.CHOICES,
        default=TaskStatus.NOT_GOT,
        verbose_name=u'任务状态',
    )
    priority = models.PositiveSmallIntegerField(
        choices=PriorityLevel.CHOICES,
        default=PriorityLevel.MIDDLE,
        verbose_name=u'任务优先级',
        db_index=True,
    )
    update_date = models.DateField(null=True, verbose_name=u'最近处理时间')
    obtain_date = models.DateField(null=True, verbose_name=u'领取时间')
    def __str__(self):
        return self.number

    @classmethod
    def serialize_set(cls, dataset):
        return ";".join(dataset)

    # 六种不同任务有不同的统计模式
    def tasks_increment(self):
        stask = Schedule_Task_Statistical.objects.filter(schedule=self.schedule)
        if self.ttype == SliceType.CC:
            stask.update(completed_cctasks = F('completed_cctasks')+1)
            reel_id = self.rect_set[0]['reel_id']
            rtask = Reel_Task_Statistical.objects.filter(schedule=self.schedule, reel_id=reel_id)
            rtask.update(completed_cctasks = F('completed_cctasks')+1)
        elif self.ttype == SliceType.CLASSIFY:
            stask.update(completed_classifytasks = F('completed_classifytasks')+1)
        elif self.ttype == SliceType.PPAGE:
            stask.update(completed_pptasks = F('completed_pptasks')+1)
            reel_id = self.page_set[0]['reel_id']
            rtask = Reel_Task_Statistical.objects.filter(schedule=self.schedule, reel_id=reel_id)
            rtask.update(completed_cctasks = F('completed_pptasks')+1)
        elif self.ttype == SliceType.CHECK:
            stask.update(completed_absenttasks = F('completed_absenttasks')+1)
            reel_id = self.page_set[0]['reel_id']
            rtask = Reel_Task_Statistical.objects.filter(schedule=self.schedule, reel_id=reel_id)
            rtask.update(completed_cctasks = F('completed_absenttasks')+1)
        elif self.ttype == SliceType.VDEL:
            stask.update(completed_absenttasks = F('completed_vdeltasks')+1)
        elif self.ttype == SliceType.REVIEW:
            stask.update(completed_absenttasks = F('completed_reviewtasks')+1)

    @activity_log
    def done(self):
        self.update_date = localtime(now()).date()
        self.tasks_increment()
        self.status = TaskStatus.COMPLETED
        return self.save(update_fields=["status", "update_date"])

    @activity_log
    def emergen(self):
        self.status = TaskStatus.EMERGENCY
        return self.save(update_fields=["status"])

    @activity_log
    def expire(self):
        self.status = TaskStatus.EXPIRED
        return self.save(update_fields=["status"])

    @activity_log
    def obtain(self, user):
        self.obtain_date = localtime(now()).date()
        self.status = TaskStatus.HANDLING
        self.owner = user
        self.save()

    class Meta:
        abstract = True
        verbose_name = u"切分任务"
        verbose_name_plural = u"切分任务管理"
        ordering = ("priority", "status")
        indexes = [
            models.Index(fields=['priority', 'status']),
        ]

# 暂不使用
class CCTask(RTask):
    schedule = models.ForeignKey(Schedule, null=True, blank=True, related_name='cc_tasks', on_delete=models.SET_NULL,
                                 verbose_name=u'切分计划')
    count = models.IntegerField("任务字块数", default=20)
    cc_threshold = models.FloatField("最高置信度")
    owner = models.ForeignKey(Staff, null=True, blank=True, related_name='cc_tasks', on_delete=models.SET_NULL)
    rect_set = JSONField(default=list, verbose_name=u'字块集') # [rect_json]

    class Meta:
        verbose_name = u"置信校对"
        verbose_name_plural = u"置信校对"

# 暂不使用
class ClassifyTask(RTask):
    schedule = models.ForeignKey(Schedule, null=True, blank=True, related_name='classify_tasks', on_delete=models.SET_NULL,
                                 verbose_name=u'切分计划')
    count = models.IntegerField("任务字块数", default=10)
    char_set = models.TextField(null=True, blank=True, verbose_name=u'字符集')
    owner = models.ForeignKey(Staff, null=True, blank=True, related_name='classify_tasks', on_delete=models.SET_NULL)
    rect_set = JSONField(default=list, verbose_name=u'字块集') # [rect_json]

    class Meta:
        verbose_name = u"聚类校对"
        verbose_name_plural = u"聚类校对"


class PageTask(RTask):
    schedule = models.ForeignKey(Schedule, null=True, blank=True, related_name='page_tasks', on_delete=models.SET_NULL,
                                 verbose_name=u'切分计划')
    count = models.IntegerField("任务页的数量", default=1)
    owner = models.ForeignKey(Staff, null=True, blank=True, related_name='page_tasks', on_delete=models.SET_NULL)
    page_set = JSONField(default=list, verbose_name=u'页的集合') # [page_json]
    redo_count =  models.PositiveSmallIntegerField(default=1, verbose_name=u'任务重作数')

    class Meta:
        verbose_name = u"逐字校对"
        verbose_name_plural = u"逐字校对"


    def task_id(self):
        cursor = connection.cursor()
        cursor.execute("select nextval('task_seq')")
        result = cursor.fetchone()
        return result[0]

    def roll_new_task(self):
        task_no = "%s_%d_%05X" % (self.schedule.schedule_no, self.task_no.split('_')[1], self.task_id())
        task = PageTask(number=task_no, schedule=self.schedule, ttype=SliceType.PPAGE, count=1,
                                  status=TaskStatus.NOT_GOT,
                                  page_set=self.page_set, redo_count=task.redo_count + 1)
        task.save()
        return task

#暂不使用
class AbsentTask(RTask):
    schedule = models.ForeignKey(Schedule, null=True, blank=True, related_name='absent_tasks', on_delete=models.SET_NULL,
                                 verbose_name=u'切分计划')
    count = models.IntegerField("任务页的数量", default=1)
    owner = models.ForeignKey(Staff, null=True, blank=True, related_name='absent_tasks', on_delete=models.SET_NULL)
    page_set = JSONField(default=list, verbose_name=u'页的集合') # [page_id, page_id]

    class Meta:
        verbose_name = u"查漏校对"
        verbose_name_plural = u"查漏校对"

#暂不使用
class DelTask(RTask):
    schedule = models.ForeignKey(Schedule, null=True, blank=True, related_name='del_tasks', on_delete=models.SET_NULL,
                                 verbose_name=u'切分计划')
    count = models.IntegerField("任务字块数", default=10)
    owner = models.ForeignKey(Staff, null=True, blank=True, related_name='del_tasks', on_delete=models.SET_NULL)
    rect_set = JSONField(default=list, verbose_name=u'字块集') # [deletion_item_id, deletion_item_id]

    class Meta:
        verbose_name = u"删框审定"
        verbose_name_plural = u"删框审定"

    def execute(self):
        for item in self.del_task_items.all():
            if item.result == ReviewResult.AGREE:
                item.confirm()
            else:
                item.undo()

#暂不使用
class ReviewTask(RTask):
    schedule = models.ForeignKey(Schedule, null=True, blank=True, related_name='review_tasks', on_delete=models.SET_NULL,
                                 verbose_name=u'切分计划')
    count = models.IntegerField("任务字块数", default=10)
    owner = models.ForeignKey(Staff, null=True, blank=True, related_name='review_tasks', on_delete=models.SET_NULL)
    rect_set = JSONField(default=list, verbose_name=u'字块补丁集') # [patch_id, patch_id]

    class Meta:
        verbose_name = u"审定任务"
        verbose_name_plural = u"审定任务管理"

#暂不使用
class DeletionCheckItem(models.Model):
    objects = BulkUpdateManager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    op = models.PositiveSmallIntegerField(verbose_name=u'操作类型', default=OpStatus.DELETED)
    x = models.PositiveSmallIntegerField(verbose_name=u'X坐标', default=0)
    y = models.PositiveSmallIntegerField(verbose_name=u'Y坐标', default=0)
    w = models.PositiveSmallIntegerField(verbose_name=u'宽度', default=1)
    h = models.PositiveSmallIntegerField(verbose_name=u'高度', default=1)
    ocolumn_uri = models.CharField(verbose_name='行图片路径', max_length=128, blank=False)
    ocolumn_x = models.PositiveSmallIntegerField(verbose_name=u'行图X坐标', default=0)
    ocolumn_y = models.PositiveSmallIntegerField(verbose_name=u'行图Y坐标', default=0)
    ch = models.CharField(null=True, blank=True, verbose_name=u'文字', max_length=2, default='')

    rect_id = models.CharField(verbose_name='字块CID', max_length=128, blank=False)
    modifier = models.ForeignKey(Staff, null=True, blank=True, related_name='modify_deletions', verbose_name=u'修改人', on_delete=models.SET_NULL)
    verifier = models.ForeignKey(Staff, null=True, blank=True, related_name='verify_deletions', verbose_name=u'审定人', on_delete=models.SET_NULL)
    result = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name=u'审定意见', default=ReviewResult.INITIAL)  # 1 同意 2 不同意
    del_task = models.ForeignKey(DelTask, null=True, blank=True, related_name='del_task_items', on_delete=models.SET_NULL,
                                 verbose_name=u'删框任务')
    created_at = models.DateTimeField(verbose_name='删框时间', auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True, verbose_name=u'更新时间', auto_now=True)

    @classmethod
    def create_from_rect(cls, rects, t):
        rect_ids = [rect ['id'] for rect in filter(lambda x: x['op'] == 3, rects)]
        # 不再創建該任務，直接刪框
        Rect.objects.filter(id__in=rect_ids).delete()
        # for r in Rect.objects.filter(id__in=rect_ids):
        #     # 对于空列添加框的删除，column_uri异常要忽略
        #     try:
        #         DeletionCheckItem(x=r.x, y=r.y, w=r.w, h=r.h, ocolumn_uri=r.column_uri(),
        #                         ocolumn_x=r.column_set['x'], ocolumn_y=r.column_set['y'], ch=r.ch,
        #                         rect_id=r.id, modifier=t.owner).save()
        #     except:
        #         r.delete()
                
    @classmethod
    def direct_delete_rects(cls, rects, t):
        rect_ids = [rect ['id'] for rect in filter(lambda x: x['op'] == 3, rects)]
        Rect.objects.filter(id__in=rect_ids).delete()

    def undo(self):
        Rect.objects.filter(pk=self.rect_id).update(op=2)

    def confirm(self):
        Rect.objects.filter(pk=self.rect_id).all().delete()


    class Meta:
        verbose_name = u"删框记录"
        verbose_name_plural = u"删框记录管理"

#暂不使用
class ActivityLog(models.Model):
    user = models.ForeignKey(Staff, related_name='activities', on_delete=models.SET_NULL, null=True)
    log = models.CharField(verbose_name=u'记录', max_length=128, default='')
    object_type = models.CharField(verbose_name=u'对象类型', max_length=32)
    object_pk = models.CharField(verbose_name=u'对象主键', max_length=64)
    action = models.CharField(verbose_name=u'行为', max_length=16)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    def log_message(self):
        return "User:%s %s to %s(%s) at %s" % (self.user.id,
                                               self.action, self.object_type,
                                               self.object_pk, self.created_at)

#暂不使用
class CharClassifyPlan(models.Model):
    schedule = models.ForeignKey(Schedule, null=True, blank=True, related_name='char_clsfy_plan',
                                 on_delete=models.SET_NULL, verbose_name=u'切分计划')
    ch = models.CharField(null=True, blank=True, verbose_name=u'文字', max_length=2, default='', db_index=True)
    total_cnt = models.IntegerField(verbose_name=u'总数', default=0, db_index=True)
    needcheck_cnt = models.IntegerField(verbose_name=u'待检查数', default=0)
    done_cnt = models.IntegerField(verbose_name=u'已完成数', default=0)
    wcc_threshold = models.DecimalField(verbose_name=u'识别置信阈值',max_digits=4, decimal_places=3, default=0)


    class Meta:
        verbose_name = u"聚类阈值"
        verbose_name_plural = u"聚类阈值"

    @shared_task
    @email_if_fails
    def create_charplan(schedule_id):
        schedule = Schedule.objects.get(pk=schedule_id)
        CharClassifyPlan.objects.filter(schedule=schedule).all().delete()
        cursor = connection.cursor()
        raw_sql = '''
        SET SEARCH_PATH TO public;
        INSERT INTO public.rect_charclassifyplan (ch, total_cnt, needcheck_cnt, done_cnt, wcc_threshold, schedule_id)
        SELECT
        ch,
        count(rect_rect."ch") as total_cnt,
        0,0,0,
        '%s'
        FROM public.rect_rect
        where reel_id IN (%s)
        group by ch
        ''' % (schedule.id, ','.join([str(r_id) for r_id in schedule.reels.values_list('id', flat=True)]))
        cursor.execute(raw_sql)
        CharClassifyPlan.objects.filter(schedule=schedule, total_cnt__lt=10).all().delete()


    def measure_charplan(self, wcc_threshold):
        result = Rect.objects.filter(ch=self.ch, reel_id__in=self.schedule.reels.values_list('id', flat=True)).aggregate(
            needcheck_cnt=Sum(Case(When(wcc__lte=wcc_threshold, then=Value(1)),
            default=Value(0),
            output_field=models.    IntegerField())),
            total_cnt=Count('id'))
        self.total_cnt=result['total_cnt']
        self.needcheck_cnt=result['needcheck_cnt']
        self.wcc_threshold=wcc_threshold
        self.save()


class AllocateTask(object):
    class Config:
        CCTASK_COUNT = 20
        DEFAULT_COUNT = 20
        BULK_TASK_COUNT = 30
        PAGETASK_COUNT = 1

    def __init__(self, schedule, reel = None):
        self.schedule = schedule
        self.reel = reel

    def allocate(self):
        pass

    def task_id(self):
        cursor = connection.cursor()
        cursor.execute("select nextval('task_seq')")
        result = cursor.fetchone()
        return result[0]

class CCAllocateTask(AllocateTask):
    def allocate(self):
        reel = self.reel
        query_set = reel.rects.filter(cc__lte=self.schedule.cc_threshold)
        count = AllocateTask.Config.CCTASK_COUNT
        rect_set = []
        task_set = []
        total_tasks = 0
        for no, rect in enumerate(query_set, start=1):
            # rect_set.append(rect.id.hex)
            rect_set.append(rect.serialize_set)
            if len(rect_set) == count:
                # 268,435,455可容纳一部大藏经17，280，000个字
                task_no = "%s_%d_%05X" % (self.schedule.schedule_no, reel.id, self.task_id())
                task = CCTask(number=task_no, schedule=self.schedule, ttype=SliceType.CC, count=count, status=TaskStatus.NOT_GOT,
                              rect_set=list(rect_set), cc_threshold=rect.cc)
                rect_set.clear()
                task_set.append(task)
                if len(task_set) == AllocateTask.Config.BULK_TASK_COUNT:
                    CCTask.objects.bulk_create(task_set)
                    total_tasks += len(task_set)
                    task_set.clear()
        if len(rect_set) > 0:
            task_no = "%s_%d_%05X" % (self.schedule.schedule_no, reel.id, self.task_id())
            task = CCTask(number=task_no, schedule=self.schedule, ttype=SliceType.CC, count=count, status=TaskStatus.NOT_GOT,
                            rect_set=list(rect_set), cc_threshold=rect.cc)
            rect_set.clear()
            task_set.append(task)
        CCTask.objects.bulk_create(task_set)
        total_tasks += len(task_set)
        return total_tasks

def batch(iterable, n = 1):
    current_batch = []
    for item in iterable:
        current_batch.append(item)
        if len(current_batch) == n:
            yield current_batch
            current_batch = []
    if current_batch:
        yield current_batch


class ClassifyAllocateTask(AllocateTask):

    def allocate(self):
        rect_set = []
        word_set = {}
        task_set = []
        count = AllocateTask.Config.DEFAULT_COUNT
        reel_ids = self.schedule.reels.values_list('id', flat=True)
        base_queryset = Rect.objects.filter(reel_id__in=reel_ids)
        total_tasks = 0
        # 首先找出这些计划准备表
        for plans in batch(CharClassifyPlan.objects.filter(schedule=self.schedule), 3):
            # 然后把分组的计划变成，不同分片的queryset组拼接
            questsets = [base_queryset.filter(ch=_plan.ch, wcc__lte=_plan.wcc_threshold) for _plan in plans]
            if len(questsets) > 1:
                queryset = questsets[0].union(*questsets[1:])
            else:
                queryset = questsets[0]
            # 每组去递归补足每queryset下不足20单位的情况
            for no, rect in enumerate(queryset, start=1):
                rect_set.append(rect.serialize_set)
                word_set[rect.ch] = 1

                if len(rect_set) == count:
                    task_no = "%s_%07X" % (self.schedule.schedule_no, self.task_id())
                    task = ClassifyTask(number=task_no, schedule=self.schedule, ttype=SliceType.CLASSIFY, count=count,
                                        status=TaskStatus.NOT_GOT,
                                        rect_set=list(rect_set),
                                        char_set=ClassifyTask.serialize_set(word_set.keys()))
                    rect_set.clear()
                    word_set = {}
                    task_set.append(task)
                    if len(task_set) == AllocateTask.Config.BULK_TASK_COUNT:
                        ClassifyTask.objects.bulk_create(task_set)
                        total_tasks += len(task_set)
                        task_set.clear()
        if len(rect_set) > 0:
            task_no = "%s_%07X" % (self.schedule.schedule_no, self.task_id())
            task = ClassifyTask(number=task_no, schedule=self.schedule, ttype=SliceType.CLASSIFY, count=count,
                                status=TaskStatus.NOT_GOT,
                                rect_set=list(rect_set),
                                char_set=ClassifyTask.serialize_set(word_set.keys()))
            rect_set.clear()
            task_set.append(task)
        ClassifyTask.objects.bulk_create(task_set)
        total_tasks += len(task_set)
        return total_tasks


class PerpageAllocateTask(AllocateTask):

    def allocate(self):
        reel = self.reel
        query_set = filter(lambda x: x.primary, PageRect.objects.filter(reel=reel))

        page_set = []
        task_set = []
        count = AllocateTask.Config.PAGETASK_COUNT
        total_tasks = 0
        for no, pagerect in enumerate(query_set, start=1):
            page_set.append(pagerect.serialize_set)
            if len(page_set) == count:
                task_no = "%s_%d_%05X" % (self.schedule.schedule_no, reel.id, self.task_id())
                task = PageTask(number=task_no, schedule=self.schedule, ttype=SliceType.PPAGE, count=1,
                                  status=TaskStatus.NOT_GOT,
                                  page_set=list(page_set))
                page_set.clear()
                task_set.append(task)
                if len(task_set) == AllocateTask.Config.BULK_TASK_COUNT:
                    PageTask.objects.bulk_create(task_set)
                    total_tasks += len(task_set)
                    task_set.clear()

        PageTask.objects.bulk_create(task_set)
        total_tasks += len(task_set)
        return total_tasks


class AbsentpageAllocateTask(AllocateTask):

    def allocate(self):
        reel = self.reel
        # TODO: 缺少缺页查找页面
        queryset = PageRect.objects.filter(reel=reel)
        query_set = filter(lambda x: x.primary, queryset)

        page_set = []
        task_set = []
        count = AllocateTask.Config.PAGETASK_COUNT
        total_tasks = 0
        for no, pagerect in enumerate(query_set, start=1):
            page_set.append(pagerect.serialize_set)
            if len(page_set) == count:
                task_no = "%s_%d_%05X" % (self.schedule.schedule_no, reel.id, self.task_id())
                task = AbsentTask(number=task_no, schedule=self.schedule, ttype=SliceType.CHECK, count=1,
                                page_set=list(page_set))
                page_set.clear()
                task_set.append(task)
                if len(task_set) == AllocateTask.Config.BULK_TASK_COUNT:
                    PageTask.objects.bulk_create(task_set)
                    total_tasks += len(task_set)
                    task_set.clear()

        PageTask.objects.bulk_create(task_set)
        total_tasks += len(task_set)
        return total_tasks


class DelAllocateTask(AllocateTask):

    def allocate(self):
        rect_set = []
        task_set = []
        count = AllocateTask.Config.PAGETASK_COUNT
        total_tasks = 0
        for items in batch(DeletionCheckItem.objects.filter(del_task_id=None), 10):
            if len(items) == 10:
                rect_set = list(map(lambda x:x.pk.hex, items))
                task_no = "%s_%07X" % ('DelTask', self.task_id())
                task = DelTask(number=task_no,  ttype=SliceType.VDEL,
                                rect_set=rect_set)
                rect_set.clear()
                ids = [_item.pk for _item in items]
                DeletionCheckItem.objects.filter(id__in=ids).update(del_task_id=task_no)
                task_set.append(task)
                if len(task_set) == AllocateTask.Config.BULK_TASK_COUNT:
                    DelTask.objects.bulk_create(task_set)
                    total_tasks += len(task_set)
                    task_set.clear()
        DelTask.objects.bulk_create(task_set)
        total_tasks += len(task_set)
        task_set.clear()
        return total_tasks

def allocateTasks(schedule, reel, type):
    allocator = None
    count = -1
    if type == SliceType.CC: # 置信度
        allocator = CCAllocateTask(schedule, reel)
    elif type == SliceType.CLASSIFY: # 聚类
        allocator = ClassifyAllocateTask(schedule)
    elif type == SliceType.PPAGE: # 逐字
        allocator = PerpageAllocateTask(schedule, reel)
    elif type == SliceType.CHECK: # 查漏
        allocator = PerpageAllocateTask(schedule, reel)
    elif type == SliceType.VDEL: # 删框
        allocator = DelAllocateTask(schedule, reel)
    if allocator:
        count = allocator.allocate()
    return count



@receiver(post_save, sender=Schedule)
@disable_for_create_cut_task
def post_schedule_create_pretables(sender, instance, created, **kwargs):
    if created:
        Schedule_Task_Statistical(schedule=instance).save()
        # Schedule刚被创建，就建立聚类字符准备表，创建逐字校对的任务，任务为未就绪状态
        # CharClassifyPlan.create_charplan.s(instance.pk.hex).apply_async(countdown=20)
        Reel_Task_Statistical.gen_pptask_by_plan()
    else:
        # update
        if (instance.has_changed) and ( 'status' in instance.changed_fields):
            before, now = instance.get_field_diff('status')
            if now == ScheduleStatus.ACTIVE and before == ScheduleStatus.NOT_ACTIVE:
                # Schedule被激活，创建置信校对的任务
                # Reel_Task_Statistical.gen_cctask_by_plan.delay()
                # 暂不生成置信校对任务
                pass

