from django.conf import settings
from django.db import models
from django.utils import timezone
from jwt_auth.models import Staff
from tdata.models import *
from tdata.lib.image_name_encipher import get_image_url
import re, json

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

class BatchTask(models.Model):
    priority = models.SmallIntegerField('优先级', choices=TaskBase.PRIORITY_CHOICES, default=2) # 1,2,3分别表示低，中，高
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    publisher = models.ForeignKey(Staff, on_delete=models.PROTECT,
    verbose_name='发布用户')
    description = models.TextField('描述', blank=True)

    @property
    def batch_no(self):
        return '%d%02d%02d%02d%02d' % (self.created_at.year,
     self.created_at.month, self.created_at.day, self.created_at.hour,
     self.created_at.minute)

    def __str__(self):
        return self.batch_no

class Task(models.Model):
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
    TYPE_CORRECT_DIFFICULT = 11
    TYPE_JUDGE_DIFFICULT = 12
    TYPE_CHOICES = (
        (TYPE_CORRECT, '文字校对'),
        (TYPE_CORRECT_VERIFY, '文字校对审定'),
        (TYPE_JUDGE, '校勘判取'),
        (TYPE_JUDGE_VERIFY, '校勘判取审定'),
        (TYPE_PUNCT, '基础标点'),
        (TYPE_PUNCT_VERIFY, '基础标点审定'),
        (TYPE_LQPUNCT, '定本标点'),
        (TYPE_LQPUNCT_VERIFY, '定本标点审定'),
        (TYPE_MARK, '格式标注'),
        (TYPE_MARK_VERIFY, '格式标注审定'),
        (TYPE_CORRECT_DIFFICULT, '文字校对难字处理'),
        (TYPE_JUDGE_DIFFICULT, '校勘判取难字处理'),
    )

    TASK_NO_CHOICES = (
        (0, '无序号'),
        (1, '一'),
        (2, '二'),
        (3, '三'),
        (4, '四'),
    )

    STATUS_NOT_READY = 1
    STATUS_READY = 2
    STATUS_PROCESSING = 3
    STATUS_FINISHED = 4
    STATUS_PAUSED = 5
    STATUS_REMINDED = 6
    STATUS_REVOKED = 7
    STATUS_SYSTEM_PAUSED = 8
    STATUS_CHOICES = (
        (STATUS_NOT_READY, '未就绪'),
        (STATUS_READY, '待领取'),
        (STATUS_PROCESSING, '进行中'),
        (STATUS_PAUSED, '已暂停'),
        (STATUS_FINISHED, '已完成'),
        (STATUS_REMINDED, '已催单'),
        (STATUS_REVOKED, '已回收'),
        (STATUS_SYSTEM_PAUSED, '系统内暂停'),
    )

    TYPE_TO_URL_PREFIX = {
        TYPE_CORRECT: 'correct',
        TYPE_CORRECT_VERIFY: 'verify_correct',
        TYPE_CORRECT_DIFFICULT: 'correct_difficult',
        TYPE_JUDGE: 'judge',
        TYPE_JUDGE_VERIFY: 'verify_judge',
        TYPE_JUDGE_DIFFICULT: 'judge_difficult',
        TYPE_PUNCT: 'punct',
        TYPE_PUNCT_VERIFY: 'verify_punct',
        TYPE_LQPUNCT: 'lqpunct',
        TYPE_LQPUNCT_VERIFY: 'verify_lqpunct',
        TYPE_MARK: 'mark',
        TYPE_MARK_VERIFY: 'verify_mark',
    }

    batchtask = models.ForeignKey(BatchTask, on_delete=models.CASCADE, verbose_name='批次号')
    reel = models.ForeignKey(Reel, on_delete=models.CASCADE, related_name='tasks',
    blank=True, null=True)
    lqreel = models.ForeignKey(LQReel, on_delete=models.CASCADE, blank=True, null=True)
    typ = models.SmallIntegerField('任务类型', choices=TYPE_CHOICES, db_index=True)
    base_reel = models.ForeignKey(Reel, on_delete=models.CASCADE, verbose_name='底本', blank=True, null=True)
    task_no = models.SmallIntegerField('组合任务序号', choices=TASK_NO_CHOICES, default=0)
    status = models.SmallIntegerField('状态', choices=STATUS_CHOICES, default=1, db_index=True)

    # 用于记录当前工作的条目，下次用户进入任务时直接到此。
    # 文字校对，表示CorrectSeg的id；校勘判取表示page
    cur_focus = models.IntegerField('当前工作的条目', default=0)

    # 校勘判取相关
    reeldiff = models.ForeignKey('ReelDiff', on_delete=models.SET_NULL, blank=True, null=True)
    # 标点相关
    reeltext = models.ForeignKey('ReelCorrectText', related_name='punct_tasks', on_delete=models.SET_NULL, blank=True, null=True)
    lqtext = models.ForeignKey('LQReelText', related_name='lqpunct_tasks', verbose_name='龙泉藏经卷经文', on_delete=models.SET_NULL, blank=True, null=True)

    result = SutraTextField('结果', blank=True)
    started_at = models.DateTimeField('开始时间', blank=True, null=True)
    finished_at = models.DateTimeField('完成时间', blank=True, null=True)
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    picked_at = models.DateTimeField('领取时间', blank=True, null=True)
    picker = models.ForeignKey(Staff, related_name='picked_tasks', on_delete=models.SET_NULL,
    verbose_name='领取用户', blank=True, null=True)
    publisher = models.ForeignKey(Staff, related_name='published_tasks', on_delete=models.PROTECT,
    verbose_name='发布用户')
    priority = models.SmallIntegerField('优先级', choices=TaskBase.PRIORITY_CHOICES, default=2) # 1,2,3分别表示低，中，高
    progress = models.SmallIntegerField('进度', default=0)

    class Meta:
        verbose_name_plural = verbose_name = u'任务'

    class Config:
        list_display_fields = ('id', 'result', 'created_at')
        list_form_fields = list_display_fields
        search_fields = ('id', 'result', 'created_at')

    def __str__(self):
        type_map = dict(Task.TYPE_CHOICES)
        if self.typ in [Task.TYPE_CORRECT, Task.TYPE_CORRECT_VERIFY, Task.TYPE_PUNCT, \
            Task.TYPE_PUNCT_VERIFY, Task.TYPE_MARK, Task.TYPE_MARK_VERIFY]:
            s = '%s - %s' % (self.reel, type_map.get(self.typ))
        else:
            s = '%s - %s' % (self.lqreel, type_map.get(self.typ))
        return s

    @property
    def tripitaka_name(self):
        return self.reel.sutra.tripitaka.name
    tripitaka_name.fget.short_description = '藏'

    @property
    def sutra_name(self):
        return self.reel.sutra.name
    sutra_name.fget.short_description = '经'

    @property
    def lqsutra_name(self):
        return self.lqreel.lqsutra.name
    lqsutra_name.fget.short_description = '龙泉经名'

    @property
    def base_reel_name(self):
        return self.base_reel.sutra.tripitaka.name
    base_reel_name.fget.short_description = '底本'

    @property
    def reel_no(self):
        if self.reel:
            return self.reel.reel_no
        if self.lqreel:
            return self.lqreel.reel_no
    reel_no.fget.short_description = '第几卷'

    @property
    def realtime_progress(self):
        if self.status == Task.STATUS_FINISHED:
            return '100%'
        if self.status in [Task.STATUS_NOT_READY, Task.STATUS_READY]:
            return '0%'
        if self.typ in [Task.TYPE_CORRECT, Task.TYPE_CORRECT_VERIFY]:
            total = CorrectSeg.objects.filter(task_id=self.id, tag=CorrectSeg.TAG_DIFF).count()
            not_selected = CorrectSeg.objects.filter(task_id=self.id, tag=CorrectSeg.TAG_DIFF, selected_text=None).count()
            selected = total - not_selected
            ratio = '%.1f%%' % (selected * 100 / total)
            return ratio
        if self.typ in [Task.TYPE_JUDGE, Task.TYPE_JUDGE_VERIFY]:
            total = DiffSegResult.objects.filter(task_id=self.id).count()
            not_selected = DiffSegResult.objects.filter(task_id=self.id, selected_text=None).count()
            selected = total - not_selected
            ratio = '%.1f%%' % (selected * 100 / total)
            return ratio
    realtime_progress.fget.short_description = '进度'

class CorrectSeg(models.Model):
    TAG_EQUAL = 1
    TAG_DIFF = 2
    TAG_P = 3
    TAG_LINEFEED = 4

    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    tag = models.SmallIntegerField('差异Tag', default=1)
    position = models.IntegerField('在校正本中的位置', default=0)
    text1 = models.TextField('文本1', blank=True, null=True)
    text2 = models.TextField('文本2', blank=True, null=True)
    text3 = models.TextField('文本3', blank=True, null=True)
    text4 = models.TextField('文本4', blank=True, null=True)
    selected_text = models.TextField('修正文本', blank=True, null=True)
    page_no = models.SmallIntegerField('卷中页序号', default=-1)
    line_no = models.SmallIntegerField('页中行序号', default=-1)
    char_no = models.SmallIntegerField('行中字序号', default=-1)
    #存疑相关
    doubt_comment = models.TextField('存疑意见', default='', blank=True)

class DoubtSeg(models.Model):
    task = models.ForeignKey(Task, related_name='doubt_segs', on_delete=models.CASCADE)
    page_no = models.SmallIntegerField('Seg卷中页序号', default=-1)
    line_no = models.SmallIntegerField('Seg页中行序号', default=-1)
    char_no = models.SmallIntegerField('Seg行中字序号', default=-1)
    doubt_text = models.TextField('存疑文字段', default='', blank=True)
    doubt_char_no = models.SmallIntegerField('存疑行中字序号', default=-1)
    doubt_comment = models.TextField('存疑意见', default='', blank=True)
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    processed = models.BooleanField('是否处理', default=False)

class ReelCorrectText(models.Model):
    BODY_START_PATTERN = re.compile('品(第[一二三四五六七八九十百]*(之[一二三四五六七八九十百]*)*)|(品之[一二三四五六七八九十百]*)$')
    BODY_END_PATTERN = re.compile('卷第[一二三四五六七八九十百]*$')
    SEPARATORS_PATTERN = re.compile('[pb\n]')

    reel = models.ForeignKey(Reel, related_name='reel_correct_texts' ,verbose_name='实体藏经卷', on_delete=models.CASCADE)
    text = SutraTextField('经文', blank=True) # 文字校对或文字校对审定后得到的经文
    head = SutraTextField('经文正文前文本', blank=True, default='')
    body = SutraTextField('经文正文', blank=True, default='')
    tail = SutraTextField('经文正文后文本', blank=True, default='')
    task = models.OneToOneField(Task, verbose_name='发布任务', on_delete=models.SET_NULL, blank=True, null=True, default=None)
    publisher = models.ForeignKey(Staff, on_delete=models.SET_NULL, blank=True, null=True, verbose_name='发布用户')
    created_at = models.DateTimeField('创建时间', default=timezone.now)

    class Meta:
        verbose_name = '文字校对得到的卷经文'
        verbose_name_plural = '文字校对得到的卷经文'

    def __str__(self):
        return '%s (%s)' % (self.reel, self.created_at.strftime('%F %T'))

    def set_text(self, text):
        self.text = text
        lines = text.split('\n')
        line_cnt = len(lines)
        start_line_index = min(10, line_cnt-1)
        for i in range(start_line_index):
            if ReelCorrectText.BODY_START_PATTERN.search(lines[i]):
                start_line_index = i
                break
        author_line_index = -1
        for i in range(start_line_index-1, -1, -1):
            if lines[i].endswith('譯'):
                author_line_index = i
                break
        tail_line_index = line_cnt
        line_index = max(line_cnt-20, 0)
        for i in range(line_cnt-1, line_index, -1):
            if ReelCorrectText.BODY_END_PATTERN.search(lines[i]):
                tail_line_index = i
                break
        self.head = ''.join(map(lambda x: (x + '\n'), lines[0 : author_line_index+1]))
        self.body = ''.join(map(lambda x: (x + '\n'), lines[author_line_index+1 : tail_line_index]))
        self.tail = '\n'.join(lines[tail_line_index:])

class LQReelText(models.Model):
    lqreel = models.ForeignKey(LQReel, verbose_name='龙泉藏经卷', on_delete=models.CASCADE)
    text = SutraTextField('经文', blank=True) # 校勘判取审定后得到的经文
    head = SutraTextField('经文正文前文本', blank=True, default='')
    body = SutraTextField('经文正文', blank=True, default='')
    tail = SutraTextField('经文正文后文本', blank=True, default='')
    task = models.OneToOneField(Task, verbose_name='发布任务', on_delete=models.SET_NULL, blank=True, null=True, default=None)
    publisher = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, verbose_name='发布用户')
    created_at = models.DateTimeField('创建时间', default=timezone.now)

    class Meta:
        verbose_name = '校勘判取审定得到的卷经文'
        verbose_name_plural = '校勘判取审定得到的卷经文'

    def __str__(self):
        return '%s (%s)' % (self.lqreel, self.created_at.strftime('%F %T'))

    def set_text(self, text):
        self.text = text
        self.body = text
        self.head = ''
        self.tail = ''

# 校勘判取相关
class ReelDiff(models.Model):
    lqsutra = models.ForeignKey(LQSutra, on_delete=models.CASCADE, blank=True, null=True)
    reel_no = models.SmallIntegerField('卷序号')
    base_text = models.ForeignKey(ReelCorrectText, related_name='reeldiffs', verbose_name='基准文本', on_delete=models.CASCADE)
    published_at = models.DateTimeField('发布时间', blank=True, null=True)
    publisher = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True,
    verbose_name='发布用户')
    diffseg_pos_lst = models.TextField('DiffSeg位置信息')

class DiffSeg(models.Model):
    """
    各版本比对结果的差异文本段
    """
    reeldiff = models.ForeignKey(ReelDiff, on_delete=models.CASCADE, null=True)
    base_pos = models.IntegerField('在基准文本中位置', default=0) # base_pos=0表示在第1个字前，base_pos>0表示在第base_pos个字后
    base_length = models.IntegerField('基准文本中对应文本段长度', default=0)
    recheck = models.BooleanField('待复查', default=False)
    recheck_desc = models.TextField('待复查说明', default='')

class DiffSegText(models.Model):
    """
    各版本比对结果的差异文本段中各版本的文本
    """
    diffseg = models.ForeignKey(DiffSeg, on_delete=models.CASCADE, related_name='diffsegtexts')
    tripitaka = models.ForeignKey(Tripitaka, on_delete=models.CASCADE)
    text = models.TextField('文本', blank=True, null=True)
    position = models.IntegerField('在卷文本中的位置（前有几个字）', default=0)
    offset = models.IntegerField('所在卷文本在整部经文中位置', default=0)
    start_char_pos = models.CharField('起始经字位置', max_length=32, default='', null=True)
    end_char_pos = models.CharField('结束经字位置', max_length=32, default='', null=True)

    @property
    def column_url(self):
        try:
            pid = self.start_char_pos[0:17]
            line_no = self.start_char_pos[18:20]
            line_no = int(line_no)
            page = Page.objects.get(pid=pid)
            url = '%s%sc%d0%02d.jpg' % (settings.COL_IMAGE_URL_PREFIX, page.reel.url_prefix(), page.page_no, line_no)
            return url
        except:
            pass

    @property
    def page_url(self):
        try:
            pid = self.start_char_pos[0:17]
            page = Page.objects.get(pid=pid)
            url = get_image_url(page.reel, page.page_no)
            return url
        except:
            pass

    @property
    def rect(self):
        try:
            pid = self.start_char_pos[0:17]
            line_no = self.start_char_pos[18:20]
            char_no = self.start_char_pos[21:23]
            start_line_no = int(line_no)
            start_char_no = int(char_no)
            line_no = self.end_char_pos[18:20]
            char_no = self.end_char_pos[21:23]
            end_line_no = int(line_no)
            end_char_no = int(char_no)
            page = Page.objects.get(pid=pid)
            cut_info = json.loads(page.cut_info)
            for ch in cut_info['char_data']:
                if (ch['line_no'] == start_line_no and ch['char_no'] == start_char_no):
                    rectx1 = ch['x']
                    recty1 = ch['y']
                    w1 = ch['w']
                if start_line_no == end_line_no:
                    if (ch['line_no'] == end_line_no and ch['char_no'] == end_char_no):
                        recty2 = ch['y']
                        h2 = ch['h']
                        break
                else:
                    if ch['line_no'] == start_line_no:
                        recty2 = ch['y']
                        h2 = ch['h']
                    elif ch['line_no'] > start_line_no:
                        break

            col_id = '%sc%d0%02d' % (page.reel.image_prefix(), page.page_no, start_line_no)
            column = Column.objects.get(id=col_id)
            x = rectx1 - column.x
            y = recty1 - column.y
            x1 = x + w1
            y1 = recty2 - column.y + h2
            return (x, y, x1, y1)
        except:
            pass

class DiffSegResult(models.Model):
    '''
    校勘判取用户对每个DiffSeg操作后得到的结果
    '''
    TYPE_SELECT = 1
    TYPE_SPLIT = 2
    TYPE_CHOICES = (
        (TYPE_SELECT, '选择'),
        (TYPE_SPLIT, '拆分'),
    )
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    diffseg = models.ForeignKey(DiffSeg, on_delete=models.CASCADE, related_name='diffsegresults')
    typ = models.SmallIntegerField('结果类型', choices=TYPE_CHOICES, default=1, editable=True)
    selected_text = models.TextField('判取文本', blank=True, null=True, default='')
    merged_diffsegresults = models.ManyToManyField("self", blank=True)
    split_info = models.TextField('拆分信息', blank=True, null=True, default='{}')
    selected = models.SmallIntegerField('是否判取', blank=True, default=0) #　0, 1 -- 未判取，已判取
    doubt = models.SmallIntegerField('是否存疑', blank=True, default=0) # 0, 1 -- 无存疑，有存疑
    #存疑相关
    doubt_comment = models.TextField('存疑意见', default='', blank=True)
    all_equal = models.BooleanField('校勘判取结果都一致', default=False)

    class Meta:
        verbose_name = '校勘判取结果'
        verbose_name_plural = '校勘判取结果'
        unique_together = (('task', 'diffseg'),)

    def is_equal(self, obj):
        if self.doubt or obj.doubt:
            return False
        if self.diffseg_id != obj.diffseg_id:
            return False
        if self.typ != obj.typ:
            return False
        if self.selected_text != obj.selected_text:
            return False
        if len(list(self.merged_diffsegresults.all())) or len(list(obj.merged_diffsegresults.all())):
            return False
        if self.split_info != obj.split_info:
            return False
        return True

class Punct(models.Model):
    reel = models.ForeignKey(Reel, verbose_name='实体藏经卷', on_delete=models.CASCADE)
    reeltext = models.ForeignKey(ReelCorrectText, verbose_name='实体藏经卷经文', on_delete=models.CASCADE)
    punctuation = models.TextField('标点', blank=True, null=True) # [[5,'，'], [15,'。']]
    body_punctuation = models.TextField('文本标点', blank=True, null=True)
    task = models.OneToOneField(Task, verbose_name='发布任务', on_delete=models.SET_NULL, blank=True, null=True) # Task=null表示原始标点结果，不为null表示标点任务和标点审定任务的结果
    publisher = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, verbose_name='发布用户')
    created_at = models.DateTimeField('创建时间', blank=True, null=True, auto_now_add=True)

    class Meta:
        verbose_name = '基础标点结果'
        verbose_name_plural = '基础标点结果'

    def __str__(self):
        return '%s' % self.reeltext

class LQPunct(models.Model):
    lqreel = models.ForeignKey(LQReel, verbose_name='龙泉藏经卷', on_delete=models.CASCADE)
    reeltext = models.ForeignKey(LQReelText, verbose_name='龙泉藏经卷经文', on_delete=models.CASCADE)
    punctuation = models.TextField('标点', blank=True, null=True) # [[5,'，'], [15,'。']]
    body_punctuation = models.TextField('文本标点', blank=True, null=True)
    task = models.OneToOneField(Task, verbose_name='发布任务', on_delete=models.SET_NULL, blank=True, null=True) # Task=null表示原始标点结果，不为null表示标点任务和标点审定任务的结果
    publisher = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, verbose_name='发布用户')
    created_at = models.DateTimeField('创建时间', blank=True, null=True)

    class Meta:
        verbose_name = '定本标点结果'
        verbose_name_plural = '定本标点结果'

    def __str__(self):
        return '%s' % self.reeltext

# 格式标注相关
class MarkUnitBase(models.Model):
    typ = models.SmallIntegerField('类型', default=0)
    start = models.IntegerField('起始字index', default=0)
    end = models.IntegerField('结束字下一个index', default=0)
    text = models.TextField('文本', default='')

    class Meta:
        abstract = True

class Mark(models.Model):
    reel = models.ForeignKey(Reel, on_delete=models.CASCADE)
    reeltext = models.ForeignKey(ReelCorrectText, verbose_name='实体藏经卷经文', on_delete=models.CASCADE)
    task = models.OneToOneField(Task, verbose_name='发布任务', on_delete=models.SET_NULL, blank=True, null=True) # Task=null表示原始格式标注结果，不为null表示格式标注任务和格式标注审定任务的结果
    publisher = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, verbose_name='发布用户')
    created_at = models.DateTimeField('创建时间', blank=True, null=True)

class MarkUnit(MarkUnitBase):
    mark = models.ForeignKey(Mark, on_delete=models.CASCADE)

####
class FeedbackBase(models.Model):
    RESPONSE_UNPROCESSED = 1
    RESPONSE_APPROVED = 2
    RESPONSE_DISAPPROVED = 3
    RESPONSE_CHOICES = (
        (RESPONSE_UNPROCESSED, '未处理'),
        (RESPONSE_APPROVED, '同意'),
        (RESPONSE_DISAPPROVED, '不同意'),
    )

    original_text = models.TextField('原始文本', blank=True, null=True, default='')
    fb_text = models.TextField('反馈文本', blank=True, null=True, default='')
    fb_comment = models.TextField('反馈说明')
    fb_user = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True,
    verbose_name='反馈用户')
    created_at = models.DateTimeField('反馈时间', default=timezone.now)
    processor = models.ForeignKey(Staff, related_name='processed_%(class)s', on_delete=models.SET_NULL, null=True,
    verbose_name='审查用户')
    processed_at = models.DateTimeField('审查时间', null=True)
    response = models.SmallIntegerField('审查意见', choices=RESPONSE_CHOICES, default=RESPONSE_UNPROCESSED)

    class Meta:
        abstract = True

    @property
    def fb_user_display(self):
        return self.fb_user.username
    fb_user_display.fget.short_description = '反馈用户'

class CorrectFeedback(FeedbackBase):
    correct_text = models.ForeignKey(ReelCorrectText, on_delete=models.CASCADE)
    position = models.IntegerField('在卷文本中的位置（前有几个字）', default=0)

    class Meta:
        verbose_name = '文字校对反馈'
        verbose_name_plural = '文字校对反馈'

class JudgeFeedback(FeedbackBase):
    diffsegresult = models.ForeignKey(DiffSegResult, on_delete=models.CASCADE, related_name='feedbacks')

    @property
    def lqsutra_name(self):
        return self.diffsegresult.task.lqreel.lqsutra.name
    lqsutra_name.fget.short_description = '龙泉经名'

    @property
    def reel_no(self):
        lqreel = self.diffsegresult.task.lqreel
        if lqreel:
            return lqreel.reel_no
    reel_no.fget.short_description = '第几卷'

    class Meta:
        verbose_name = '校勘反馈'
        verbose_name_plural = '校勘反馈'

    class Config:
        search_fields = ('original_text', 'fb_text', 'fb_user__username')

class LQPunctFeedback(models.Model):
    STATUS_READY = 2
    STATUS_PROCESSING = 3
    STATUS_FINISHED = 4
    STATUS_CHOICES = (
        (STATUS_READY, '待领取'),
        (STATUS_PROCESSING, '进行中'),
        (STATUS_FINISHED, '已完成'),
    )

    lqpunct = models.ForeignKey(LQPunct, verbose_name='定本标点', on_delete=models.CASCADE)
    start = models.IntegerField('起始字index', default=0)
    end = models.IntegerField('结束字下一个index', default=0)
    fb_punctuation = models.TextField('反馈标点', blank=True, null=True) # 包含整卷文本段的标点，格式：[[5,'，'], [15,'。']]
    fb_user = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True,
    verbose_name='反馈用户')
    created_at = models.DateTimeField('反馈时间', default=timezone.now)
    status = models.SmallIntegerField('状态', choices=STATUS_CHOICES, default=2, db_index=True)
    punctuation = models.TextField('审查标点', blank=True, null=True) # 包含整卷文本段的标点，格式：[[5,'，'], [15,'。']]
    processor = models.ForeignKey(Staff, related_name='processed_%(class)s', on_delete=models.SET_NULL, blank=True, null=True,
    verbose_name='审查用户')
    processed_at = models.DateTimeField('审查时间', blank=True, null=True)

    @property
    def lqsutra_name(self):
        return self.lqpunct.lqreel.lqsutra.name
    lqsutra_name.fget.short_description = '龙泉经名'

    @property
    def reel_no(self):
        lqreel = self.lqpunct.lqreel
        if lqreel:
            return lqreel.reel_no
    reel_no.fget.short_description = '第几卷'

    @property
    def fb_user_display(self):
        return self.fb_user.username
    fb_user_display.fget.short_description = '反馈用户'

    class Meta:
        verbose_name = '定本标点反馈'
        verbose_name_plural = '定本标点反馈'

    class Config:
        search_fields = ('fb_user__username',)