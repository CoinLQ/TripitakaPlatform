from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from .lib.fields import JSONField
from .lib.image_name_encipher import get_signed_path
from PIL import Image, ImageFont, ImageDraw
from io import BytesIO
import json
import urllib.request

class SutraTextField(models.TextField):
    '''
    格式说明：存储经文内容，换行用\n，每页前有换页标记p\n。读取处理原始数据\r\n为\n。
    '''

    description = '存储经文内容，换行用\n，每页前有换页标记p\n'

    def get_prep_value(self, value):
        value = value.replace('\r\n', '\n')
        value = super().get_prep_value(value)
        return self.to_python(value)

class Tripitaka(models.Model):
    code = models.CharField(verbose_name='编码', max_length=2, blank=False, unique=True)
    name = models.CharField(verbose_name='藏名', max_length=32, blank=False)
    shortname = models.CharField(verbose_name='简称（用于校勘记）', max_length=32, blank=False)
    ocr_with_nobar = models.BooleanField('识别所用的图片不分栏', default=True)
    bar_count = models.SmallIntegerField('识别所用的图片所用的分栏数', default=2)
    remark = models.TextField('备注', blank=True, default='')
    path1_char = models.CharField('存储层次1字母', max_length=1, blank=True, default='')
    path1_name = models.CharField('存储层次1中文名', max_length=16, blank=True, default='')
    path2_char = models.CharField('存储层次2字母', max_length=1, blank=True, default='')
    path2_name = models.CharField('存储层次2中文名', max_length=16, blank=True, default='')
    path3_char = models.CharField('存储层次3字母', max_length=1, blank=True, default='')
    path3_name = models.CharField('存储层次3中文名', max_length=16, blank=True, default='')
    cut_ready = models.BooleanField(verbose_name='切分数据状态', default=False)
    bar_line_count = models.CharField('每栏文本行数', max_length=256, default='0')
    use_original_cut = models.BooleanField(verbose_name='使用原始切分', default=False)

    class Meta:
        verbose_name = '实体藏'
        verbose_name_plural = '实体藏'

    def __str__(self):
        return '{} ({})'.format(self.name, self.code)

class Volume(models.Model):
    tripitaka = models.ForeignKey(Tripitaka, on_delete=models.CASCADE, verbose_name='藏名')
    vol_no = models.SmallIntegerField(verbose_name='册序号')
    page_count = models.IntegerField(verbose_name='册页数')
    remark = models.TextField('备注', default='')

    class Meta:
        verbose_name = u"实体册"
        verbose_name_plural = u"实体册"
        unique_together = (('tripitaka', 'vol_no'),)

    def __str__(self):
        return '%s: 第%s册' % (self.tripitaka.name, self.vol_no)

class LQSutra(models.Model):
    sid = models.CharField(verbose_name='龙泉经号', max_length=8, unique=True) #（为"LQ"+ 经序号 + 别本号）
    code = models.CharField(verbose_name='龙泉经目编码', max_length=5, blank=False)
    variant_code = models.CharField(verbose_name='别本号', max_length=1, default='0')
    name = models.CharField(verbose_name='龙泉经名', max_length=64, blank=False)
    total_reels = models.IntegerField(verbose_name='总卷数', blank=True, default=1)
    author = models.CharField(verbose_name='著译者', max_length=255, blank=True)
    remark = models.TextField('备注', blank=True, default='')

    class Meta:
        verbose_name = u"龙泉经目"
        verbose_name_plural = u"龙泉经目"

    def __str__(self):
        return '%s: %s' % (self.sid, self.name)

class Sutra(models.Model):
    sid = models.CharField(verbose_name='经编码', editable=True, max_length=8, unique=True)
    tripitaka = models.ForeignKey(Tripitaka, on_delete=models.CASCADE, verbose_name='藏名')
    code = models.CharField(verbose_name='实体经目编码', max_length=5, blank=False)
    variant_code = models.CharField(verbose_name='别本编码', max_length=1, default='0')
    name = models.CharField(verbose_name='经名', max_length=64, blank=True)
    lqsutra = models.ForeignKey(LQSutra, verbose_name='龙泉经目编码', null=True,
    blank=True, on_delete=models.SET_NULL) #（为"LQ"+ 经序号 + 别本号）
    total_reels = models.IntegerField(verbose_name='总卷数', blank=True, default=1)
    author = models.CharField('作译者', max_length=32, blank=True, default='')
    remark = models.TextField('备注', blank=True, default='')

    class Meta:
        verbose_name = '实体经'
        verbose_name_plural = '实体经'

    def __str__(self):
        return '%s / %s' % (self.tripitaka, self.name)

class LQReel(models.Model):
    lqsutra = models.ForeignKey(LQSutra, verbose_name='龙泉经目编码', on_delete=models.CASCADE, editable=False)
    reel_no = models.SmallIntegerField('卷序号')
    remark = models.TextField('备注', blank=True, default='')
    text_ready = models.BooleanField(verbose_name='是否有龙泉藏经经文', default=False)

    class Meta:
        verbose_name = '龙泉藏经卷'
        verbose_name_plural = '龙泉藏经卷'
        unique_together = (('lqsutra', 'reel_no'),)
        ordering = ('id',)

    def __str__(self):
        return '%s (第%s卷)' % (self.lqsutra, self.reel_no)

    def set_text_ready(self):
        if not self.text_ready:
            self.text_ready = True
            self.save(update_fields=['text_ready'])

class Reel(models.Model):
    sutra = models.ForeignKey(Sutra, verbose_name='实体经', on_delete=models.CASCADE, editable=False)
    reel_no = models.SmallIntegerField('卷序号')
    start_vol = models.SmallIntegerField('起始册')
    start_vol_page = models.SmallIntegerField('起始页码')
    end_vol = models.SmallIntegerField('终止册')
    end_vol_page = models.SmallIntegerField('终止页码')
    path1 = models.CharField('存储层次1', max_length=16, default='', blank=True)
    path2 = models.CharField('存储层次2', max_length=16, default='', blank=True)
    path3 = models.CharField('存储层次3', max_length=16, default='', blank=True)
    remark = models.TextField('备注', blank=True, default='')
    image_ready = models.BooleanField(verbose_name='图片状态', default=False)
    cut_ready = models.BooleanField(verbose_name='文字校对生成的切分数据状态', default=False)
    column_ready = models.BooleanField(verbose_name='切列图状态', default=False)
    ocr_ready = models.BooleanField(verbose_name='OCR数据状态', default=False)
    correct_ready = models.BooleanField(verbose_name='是否有文字校对经文', default=False)
    mark_ready = models.BooleanField(verbose_name='是否完成格式标注', default=False)
    used_in_collation = models.BooleanField(verbose_name='是否用于校勘', default=True)
    correct_1 = models.NullBooleanField('文字校对校一') # True: 已完成；False: 未完成；None: 无任务。以下同。
    correct_2 = models.NullBooleanField('文字校对校二')
    correct_3 = models.NullBooleanField('文字校对校三')
    correct_4 = models.NullBooleanField('文字校对校四')
    correct_verify = models.NullBooleanField('文字校对审定')
    correct_difficult = models.NullBooleanField('文字校对难字处理')
    mark_1 = models.NullBooleanField('格式标注一')
    mark_2 = models.NullBooleanField('格式标注二')
    mark_verify = models.NullBooleanField('格式标注审定')
    finished_cut_count = models.SmallIntegerField('切分完成的页数', default=0)

    class Meta:
        verbose_name = '实体卷'
        verbose_name_plural = '实体卷'
        unique_together = (('sutra', 'reel_no'),)        
        ordering = ('id',)

    @property
    def name(self):
        return u"第%s卷" %(self.reel_no,)

    @property
    def finished_cut_proportion(self):
        page_count = self.end_vol_page - self.start_vol_page + 1
        if page_count == 0:
            proportion = 0
        else:
            proportion = (self.finished_cut_count * 1.0 / page_count)
        return '%d%%' % (100 * proportion)
    finished_cut_proportion.fget.short_description = '切分完成百分比'

    def __str__(self):
        return '%s / 第%d卷' % (self.sutra, self.reel_no)

    def url_prefix(self):
        tcode = self.sutra.sid[0:2]
        filename_str = self.path_str()
        path = filename_str.replace('_', '/')
        s = '/%s/%s/%s_%s_' % (tcode, path, tcode, filename_str)
        return s

    def image_prefix(self):
        tcode = self.sutra.sid[0:2]
        filename_str = self.path_str()
        s = '%s_%s_' % (tcode, filename_str)
        return s

    def image_path(self):
        prefix = self.image_prefix()
        path = prefix.replace('_', '/')
        return path

    def path_str(self):
        path_lst = []
        if self.path1:
            path_lst.append(self.path1)
            if self.path2:
                path_lst.append(self.path2)
                if self.path3:
                    path_lst.append(self.path3)
        return '_'.join(path_lst)

    def set_correct_ready(self):
        if not self.correct_ready:
            self.correct_ready = True
            self.save(update_fields=['correct_ready'])

    @classmethod
    def is_overlapping(cls, reel1, reel2):
        if reel1.start_vol == reel2.start_vol and \
            reel1.end_vol_page >= reel2.start_vol_page:
            return True
        return False

class ReelInfo(Reel):
    class Meta:
        proxy = True
        verbose_name = '实体卷'
        verbose_name_plural = '实体卷'

class ReelTaskProgress(Reel):
    class Meta:
        proxy = True
        verbose_name = '实体卷任务进度'
        verbose_name_plural = '实体卷任务进度'

class ReelOCRText(models.Model):
    reel = models.OneToOneField(Reel, verbose_name='实体藏经卷', on_delete=models.CASCADE, primary_key=True, editable=False)
    text = SutraTextField('经文', blank=True, default='') #按实际行加了换行符，换页标记为p\n

    class Meta:
        verbose_name = '实体藏经卷OCR经文'
        verbose_name_plural = '实体藏经卷OCR经文'

    def __str__(self):
        return '%s' % self.reel

class PageStatus:
    INITIAL = 0
    RECT_NOTFOUND = 1
    PARSE_FAILED = 2
    RECT_NOTREADY = 3
    CUT_PIC_NOTFOUND = 4
    COL_PIC_NOTFOUND = 5
    COL_POS_NOTFOUND = 6
    RECT_COL_NOTREADY = 7
    RECT_COL_NOTFOUND = 8
    READY = 9
    MARKED = 10

    CHOICES = (
        (INITIAL, u'初始化'),
        (RECT_NOTFOUND, u'切分数据未上传'),
        (PARSE_FAILED, u'数据解析失败'),
        (RECT_NOTREADY, u'字块数据未展开'),
        (CUT_PIC_NOTFOUND, u'图片不存在'),
        (COL_PIC_NOTFOUND, u'列图不存在'),
        (COL_POS_NOTFOUND, u'列图坐标不存在'),
        (RECT_COL_NOTREADY, u'字块对应列图未准备'),
        (RECT_COL_NOTFOUND, u'字块对应列图不存在'),
        (READY, u'已准备好'),
        (MARKED, u'已入卷标记'),
    )

class Page(models.Model):
    pid = models.CharField(verbose_name='实体藏经页级总编码', max_length=21, blank=False, primary_key=True)
    reel = models.ForeignKey(Reel, verbose_name='实体藏经卷', on_delete=models.CASCADE, editable=False)
    reel_page_no = models.SmallIntegerField('卷中页序号')
    page_no = models.SmallIntegerField('页序号')
    bar_no = models.CharField('栏序号', max_length=1, default='0') # TODO: confirm
    status = models.PositiveSmallIntegerField(db_index=True, verbose_name=u'操作类型',
                                              choices=PageStatus.CHOICES, default=PageStatus.INITIAL)
    bar_info = JSONField(verbose_name='栏列图信息', default=dict)
    text = SutraTextField('经文', blank=True) # 文字审定后的经文
    cut_info = models.TextField('切分信息')
    cut_updated_at = models.DateTimeField('更新时间', null=True)
    cut_add_count = models.SmallIntegerField('切分信息增加字数', default=0)
    cut_wrong_count = models.SmallIntegerField('切分信息识别错的字数', default=0)
    cut_confirm_count = models.SmallIntegerField('切分信息需要确认的字数', default=0)
    cut_verify_count = models.SmallIntegerField('切分信息需要确认的字数', default=0)
    page_code = models.CharField(max_length=23, blank=False)
    char_count_lst = models.TextField('每行字数列表', default='[]')

    class Meta:
        verbose_name = '实体藏经页'
        verbose_name_plural = '实体藏经页'

    def __str__(self):
        return '%s / 第%s页' % (self.reel, self.reel_page_no)

    @property
    def s3_uri(self):
        path = '%s%d.jpg' % (self.reel.url_prefix(), self.page_no)
        signed_path = get_signed_path(path)
        url = settings.PAGE_MAGE_URL_PREFIX + signed_path
        return url

    def _remote_image_stream(self):
        opener = urllib.request.build_opener()
        # AWS S3 Private Resource snippet, someday here should to be.
        # opener.addheaders = [('Authorization', 'AWS AKIAIOSFODNN7EXAMPLE:02236Q3V0RonhpaBX5sCYVf1bNRuU=')]
        reader = opener.open(self.s3_uri)
        return Image.open(BytesIO(reader.read()))

    def down_col_pos(self):
        cut_file = self.s3_uri[0:-3] + "col"
        opener = urllib.request.build_opener()
        try:
            response = opener.open(cut_file)
        except urllib.error.HTTPError as e:
            # 下载失败
            print(self.pid + ": col download failed")
            return
        try:
            body = response.read().decode('utf8')
            json_data = json.loads(body)
            if type(json_data['col_data']) == list :
                self.status = PageStatus.RECT_COL_NOTREADY
                self.bar_info = json_data['col_data']
                self.save()
        except:
            print(self.pid + ": col parse failed")
            print("CONTENT:" + body)
            self.bar_info = {"content": body}
            self.status = PageStatus.COL_POS_NOTFOUND
            self.save(update_fields=['status', 'json'])
            return

    def down_pagerect(self):
        cut_file = self.s3_uri[0:-3] + "cut"
        opener = urllib.request.build_opener()
        try:
            response = opener.open(cut_file)
        except urllib.error.HTTPError as e:
            # 下载失败
            print(self.pid + ": rect download failed")
            self.status = PageStatus.RECT_NOTFOUND
            self.save(update_fields=['status'])
            return
        try:
            body = response.read().decode('utf8')
            json_data = json.loads(body)
            K, ext = os.path.splitext(os.path.basename(Page.sid_to_uri(self.s3_id)))
            image_code = "%s.%s" % (K, ext)
            if json_data['img_code'] == image_code and type(json_data['char_data'])==list :
                pass
        except:
            print(self.pid + ": rect parse failed")
            print("CONTENT:" + body)
            self.bar_info = {"content": body}
            self.status = PageStatus.PARSE_FAILED
            self.save(update_fields=['status', 'json'])
            return
        self.pagerects.all().delete()
        PageRect(page=self, reel=self.reel, line_count=0, column_count=0, rect_set=json_data['char_data']).save()
        self.status = PageStatus.RECT_NOTREADY
        self.save(update_fields=['status'])
        print(self.pid + ": pagerect saved")

class Column(models.Model):
    id = models.CharField('列图ID', max_length=32, primary_key=True)
    page = models.ForeignKey(Page, verbose_name='实体藏经页', on_delete=models.CASCADE, editable=False)
    x = models.SmallIntegerField('X坐标', default=0)
    y = models.SmallIntegerField('Y坐标', default=0)
    x1 = models.SmallIntegerField('X1坐标', default=0)
    y1 = models.SmallIntegerField('Y1坐标', default=0)

class Configuration(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, editable=False)
    variant = models.TextField('异体字列表', default='')
    task_timeout = models.IntegerField('校勘任务自动回收时间（秒）', default=86400*7)

    class Meta:
        verbose_name = '系统配置'
        verbose_name_plural = '系统配置'

    def __str__(self):
        return '当前配置'

class EmailVerifycode(models.Model):
    # 验证码
    code = models.CharField(max_length=20, verbose_name=u"验证码")
    email = models.EmailField(max_length=50, verbose_name=u"邮箱")
    username = models.CharField(max_length=100, verbose_name=u"用户名",default='')
    # 包含注册验证和找回验证
    send_type = models.CharField(verbose_name=u"验证码类型", max_length=10, choices=(("register",u"注册"), ("forget",u"找回密码")))
    send_time = models.DateTimeField(verbose_name=u"发送时间", default=timezone.now)
    class Meta:
        verbose_name = u"邮箱验证码"
        verbose_name_plural = verbose_name
    def __unicode__(self):
        return '{0}({1})'.format(self.code, self.email)
