from django.conf import settings
from django.db import models
from django.utils import timezone

from sutradata.models import *

class TripiMixin(object):
    def __str__(self):
        return self.name

class CompareReel(models.Model):
    reel = models.ForeignKey(Reel, on_delete=models.CASCADE, related_name='compare_set')
    base_reel = models.ForeignKey(Reel, on_delete=models.CASCADE, verbose_name='底本')

    class Meta:
        verbose_name = '卷文字比对'
        verbose_name_plural = '卷文字比对'

class CompareSeg(models.Model):
    compare_reel = models.ForeignKey(CompareReel, on_delete=models.CASCADE)
    base_pos = models.IntegerField('基础本文本段位置') # pos=0表示在第1个字前，pos>0表示在第pos个字后
    ocr_text = models.TextField('识别文本', default='')
    base_text = models.TextField('基础本文本', default='')

    class Meta:
        verbose_name = '卷文本比对文本段'
        verbose_name_plural = '卷文本比对文本段'

# # class SutraStatus(models.Model):
# #     sutra = models.ForeignKey(LQSutra, on_delete=models.CASCADE)
# #     reel_no = models.SmallIntegerField('卷序号')
# #     text_correction = models.BooleanField('已发布文字校对任务', default=False)
# #     judgement = models.BooleanField('已发布校勘判取任务', default=False)
# #     punct = models.BooleanField('已发布标点任务', default=False)
# #     mark = models.BooleanField('已发布格式标注任务', default=False)

# #     class Meta:
# #         unique_together = (('sutra', 'reel_no'),)

class TaskBase(object):
    PRIORITY_CHOICES = (
        (1, '低'),
        (2, '中'),
        (3, '高'),
    )

class BatchTask(models.Model, TripiMixin):
    priority = models.SmallIntegerField('优先级', choices=TaskBase.PRIORITY_CHOICES, default=2) # 1,2,3分别表示低，中，高
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    publisher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
    verbose_name='发布用户')
    description = models.TextField('描述', blank=True)

    @property
    def batch_no(self):
        return '%d%02d%02d%02d%02d%02d%06d' % (self.created_at.year,
     self.created_at.month, self.created_at.day, self.created_at.hour,
     self.created_at.minute, self.created_at.second, self.created_at.microsecond)

class Task(models.Model, TripiMixin):
    TYPE_CORRECT = 1
    TYPE_CORRECT_VERIFY = 2
    TYPE_JUDGE = 3
    TYPE_JUDGE_VERIFY = 4
    TYPE_PUNCT = 5
    TYPE_PUNCT_VERIFY = 6
    TYPE_LQPUNCT = 7
    TYPE_LQPUNCT_VERIFY = 8
    TYPE_MARK = 9
    TYPE_MARK_VERIFY = 10
    TYPE_LQMARK = 11
    TYPE_LQMARK_VERIFY = 12
    TYPE_CHOICES = (
        (TYPE_CORRECT, '文字校对'),
        (TYPE_CORRECT_VERIFY, '文字校对审定'),
        (TYPE_JUDGE, '校勘判取'),
        (TYPE_JUDGE_VERIFY, '校勘判取审定'),
        (TYPE_PUNCT, '基础标点'),
        (TYPE_PUNCT_VERIFY, '基础标点审定'),
        (TYPE_LQPUNCT, '定本标点'),
        (TYPE_LQPUNCT_VERIFY, '定本标点审定'),
        (TYPE_MARK, '基础格式标注'),
        (TYPE_MARK_VERIFY, '基础格式标注审定'),
        (TYPE_LQMARK, '定本格式标注'),
        (TYPE_LQMARK_VERIFY, '定本格式标注审定'),
    )

    TASK_NO_CHOICES = (
        (0, '无序号'),
        (1, '甲'),
        (2, '乙'),
        (3, '丙'),
        (4, '丁'),
    )

    STATUS_NOT_READY = 1
    STATUS_READY = 2
    STATUS_PROCESSING = 3
    STATUS_FINISHED = 4
    STATUS_REMINDED = 5
    STATUS_REVOKED = 6
    STATUS_CHOICES = (
        (STATUS_NOT_READY, '未就绪'),
        (STATUS_READY, '待领取'),
        (STATUS_PROCESSING, '进行中'),
        (STATUS_FINISHED, '已完成'),
        (STATUS_REMINDED, '已催单'),
        (STATUS_REVOKED, '已回收'),
    )

    batch_task = models.ForeignKey(BatchTask, on_delete=models.CASCADE)
    reel = models.ForeignKey(Reel, on_delete=models.CASCADE, related_name='tasks',
    blank=True, null=True)
    lqreel = models.ForeignKey(LQReel, on_delete=models.CASCADE, blank=True, null=True)
    typ = models.SmallIntegerField('任务类型', choices=TYPE_CHOICES)
    base_reel = models.ForeignKey(Reel, on_delete=models.CASCADE, verbose_name='底本')
    task_no = models.SmallIntegerField('组合任务序号', choices=TASK_NO_CHOICES)
    status = models.SmallIntegerField('状态', choices=STATUS_CHOICES, default=1)
    
    compare_reel = models.ForeignKey(CompareReel, on_delete=models.SET_NULL, null=True)
    separators = models.TextField('页行分隔符')
    result = models.TextField('结果')
    
    started_at = models.DateTimeField('开始时间', blank=True, null=True)
    finished_at = models.DateTimeField('完成时间', blank=True, null=True)
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    picked_at = models.DateTimeField('领取时间', blank=True, null=True)
    picker = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='picked_tasks', on_delete=models.SET_NULL,
    verbose_name='领取用户', blank=True, null=True)
    publisher = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='published_tasks', on_delete=models.PROTECT,
    verbose_name='发布用户')
    priority = models.SmallIntegerField('优先级', choices=TaskBase.PRIORITY_CHOICES, default=2) # 1,2,3分别表示低，中，高
    progress = models.SmallIntegerField('进度', default=0)

class CorrectSeg(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    compare_seg = models.ForeignKey(CompareSeg, on_delete=models.CASCADE)
    selected_text = models.TextField('修正文本', default='', blank=True)
    position = models.IntegerField('在校正本中的位置', default=0)
    page_no = models.SmallIntegerField('卷中页序号', default=-1)
    line_no = models.SmallIntegerField('页中行序号', default=-1)
    char_no = models.SmallIntegerField('行中字序号', default=-1)
    #用于文字校对审定，0表示甲乙结果一致并且选择了此一致的结果，1表示选择甲的结果，2表示选择乙的结果，-1表示新结果
    diff_flag = models.SmallIntegerField('甲乙差异标记', default=-1)

# 校勘判取相关
class ReelDiff(models.Model):
    lqreel = models.ForeignKey(LQReel, on_delete=models.CASCADE, blank=True, null=True)
    task = models.OneToOneField(Task, on_delete=models.SET_NULL, blank=True, null=True) # Task=null表示原始比对结果，不为null表示校勘判取任务和校勘判取审定任务的结果
    published_at = models.DateTimeField('发布时间', blank=True, null=True)
    publisher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
    verbose_name='发布用户')

class DiffSeg(models.Model):
    """
    各版本比对结果的差异文本段
    """
    reel_diff = models.ForeignKey(ReelDiff, on_delete=models.CASCADE)
    selected_text = models.TextField('判取文本', default='', blank=True)

class DiffSegText(models.Model):
    """
    各版本比对结果的差异文本段中各版本的文本
    """
    diff_seg = models.ForeignKey(DiffSeg, on_delete=models.CASCADE)
    tripitaka = models.ForeignKey(Tripitaka, on_delete=models.CASCADE)
    text = models.TextField('文本', default='', blank=True)
    start_cid = models.CharField('起始经字号', max_length=23)
    end_cid = models.CharField('结束经字号', max_length=23)

# 标点相关
class PunctResultBase(object):
    POSITION_CHOICES = (
        (1, '在后'),
        (2, '在前'),
    )
    class Meta:
        abstract = True

class Punct(models.Model):
    reel = models.ForeignKey(Reel, on_delete=models.CASCADE)
    task = models.OneToOneField(Task, on_delete=models.SET_NULL, blank=True, null=True) # Task=null表示原始标点结果，不为null表示标点任务和标点审定任务的结果
    published_at = models.DateTimeField('发布时间', blank=True, null=True)
    publisher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
    verbose_name='发布用户')

class PunctResult(models.Model):
    punct = models.ForeignKey(Punct, on_delete=models.CASCADE)
    cid = models.CharField('经字号', max_length=23)
    punct_ch = models.CharField('标点字符', max_length=2)
    position = models.SmallIntegerField('位置', choices=PunctResultBase.POSITION_CHOICES, default=1)

class LQPunct(models.Model):
    lqreel = models.ForeignKey(LQReel, on_delete=models.CASCADE)
    task = models.OneToOneField(Task, on_delete=models.SET_NULL, blank=True, null=True) # Task=null表示原始标点结果，不为null表示标点任务和标点审定任务的结果
    published_at = models.DateTimeField('发布时间', blank=True, null=True)
    publisher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
    verbose_name='发布用户')

class LQPunctResult(models.Model):
    lqpunct = models.ForeignKey(LQPunct, on_delete=models.CASCADE)
    cid = models.CharField('经字号', max_length=23)
    punct_ch = models.CharField('标点字符', max_length=2)
    position = models.SmallIntegerField('位置', choices=PunctResultBase.POSITION_CHOICES, default=1)

# 格式标注相关
class MarkUnitBase(models.Model):
    typ = models.SmallIntegerField('类型', default=0)
    start_cid = models.CharField('起始经字号', max_length=23)
    end_cid = models.CharField('结束经字号', max_length=23)
    text = models.TextField('文本', default='')
    
    class Meta:
        abstract = True

class Mark(models.Model):
    reel = models.ForeignKey(Reel, on_delete=models.CASCADE)
    task = models.OneToOneField(Task, on_delete=models.SET_NULL, blank=True, null=True) # Task=null表示原始格式标注结果，不为null表示格式标注任务和格式标注审定任务的结果
    published_at = models.DateTimeField('发布时间', blank=True, null=True)
    publisher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
    verbose_name='发布用户')

class MarkUnit(MarkUnitBase):
    mark = models.ForeignKey(Mark, on_delete=models.CASCADE)
    
class LQMark(models.Model):
    lqreel = models.ForeignKey(LQReel, on_delete=models.CASCADE)
    task = models.OneToOneField(Task, on_delete=models.SET_NULL, blank=True, null=True) # Task=null表示原始格式标注结果，不为null表示格式标注任务和格式标注审定任务的结果
    published_at = models.DateTimeField('发布时间', blank=True, null=True)
    publisher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
    verbose_name='发布用户')

class LQMarkUnit(MarkUnitBase):
    lqmark = models.ForeignKey(LQMark, on_delete=models.CASCADE)

class DoubtBase(models.Model):
    STATUS_CHOICES = (
        (1, '未处理'),
        (2, '同意'),
        (3, '不同意'),
    )

    comment = models.TextField('意见')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
    verbose_name='用户')
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    processor = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='processed_%(class)s', on_delete=models.SET_NULL, null=True,
    verbose_name='处理用户')
    processed_at = models.DateTimeField('处理时间', default=timezone.now)
    status = models.SmallIntegerField('状态', choices=STATUS_CHOICES)

    class Meta:
        abstract = True

class CorrectDoubt(DoubtBase):
    correct_seg = models.ForeignKey(CorrectSeg, on_delete=models.CASCADE)

    class Meta:
        verbose_name = '文字校对存疑'
        verbose_name_plural = '文字校对存疑'

class JudgeDoubt(DoubtBase):
    diff_seg = models.ForeignKey(DiffSeg, on_delete=models.CASCADE)

    class Meta:
        verbose_name = '校勘判取存疑'
        verbose_name_plural = '校勘判取存疑'

class PunctDoubt(DoubtBase):
    reel = models.ForeignKey(Reel, on_delete=models.CASCADE)
    start_cid = models.CharField('起始经字号', max_length=23)
    end_cid = models.CharField('结束经字号', max_length=23)

    class Meta:
        verbose_name = '基础标点存疑'
        verbose_name_plural = '基础标点存疑'

class LQPunctDoubt(DoubtBase):
    lqreel = models.ForeignKey(LQReel, on_delete=models.CASCADE)
    start_cid = models.CharField('起始经字号', max_length=23) # 底本的cid
    end_cid = models.CharField('结束经字号', max_length=23)

    class Meta:
        verbose_name = '定本标点存疑'
        verbose_name_plural = '定本标点存疑'

class MarkDoubt(DoubtBase):
    markunit = models.ForeignKey(MarkUnit, on_delete=models.CASCADE)

    class Meta:
        verbose_name = '基础格式标注存疑'
        verbose_name_plural = '基础格式标注存疑'

class LQMarkDoubt(DoubtBase):
    lqmarkunit = models.ForeignKey(LQMarkUnit, on_delete=models.CASCADE)

    class Meta:
        verbose_name = '定本格式标注存疑'
        verbose_name_plural = '定本格式标注存疑'
