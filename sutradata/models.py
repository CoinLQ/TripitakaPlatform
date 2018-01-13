from django.db import models
from django.utils import timezone

class TripiMixin(object):
    def __str__(self):
        return self.name

class Tripitaka(models.Model, TripiMixin):
    code = models.CharField(verbose_name='实体藏经版本编码', max_length=2, blank=False)
    name = models.CharField(verbose_name='实体藏经名称', max_length=32, blank=False)

    class Meta:
        verbose_name = '实体藏经'
        verbose_name_plural = '实体藏经管理'

    def __str__(self):
        return '{} ({})'.format(self.name, self.code)

class LQSutra(models.Model, TripiMixin):
    sid = models.CharField(verbose_name='龙泉经目经号编码', max_length=8) #（为"LQ"+ 经序号 + 别本号）
    name = models.CharField(verbose_name='龙泉经目名称', max_length=64, blank=False)
    total_reels = models.IntegerField(verbose_name='总卷数', blank=True, default=1)

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

    class Meta:
        verbose_name = '实体经目'
        verbose_name_plural = '实体经目管理'

    def __str__(self):
        return '%s: %s' % (self.sid, self.name)

class LQReel(models.Model):
    lqsutra = models.ForeignKey(LQSutra, verbose_name='龙泉经目编码', on_delete=models.CASCADE)
    reel_no = models.SmallIntegerField('卷序号')
    text = models.TextField('经文', default='')

    class Meta:
        verbose_name = '龙泉藏经卷'
        verbose_name_plural = '龙泉藏经卷'
        unique_together = (('lqsutra', 'reel_no'),)

class Reel(models.Model):
    sutra = models.ForeignKey(Sutra, verbose_name='实体藏经', on_delete=models.CASCADE)
    reel_no = models.SmallIntegerField('卷序号')
    start_vol = models.SmallIntegerField('起始册')
    start_vol_page = models.SmallIntegerField('起始册的页序号')
    end_vol = models.SmallIntegerField('终止册')
    end_vol_page = models.SmallIntegerField('终止册的页序号')
    text = models.TextField('经文', default='') #按实际行加了换行符，换页标记为p\n
    fixed = models.BooleanField('是否有调整', default=False)
    f_start_page = models.CharField('起始页ID', max_length=18, default='')
    f_start_line_no = models.IntegerField('起始页行序号', default=-1)
    f_start_char_no = models.IntegerField('起始页的行中字序号', default=-1)
    f_end_page = models.CharField('终止页ID', max_length=18, default='')
    f_end_line_no = models.IntegerField('终止页行序号', default=-1)
    f_end_char_no = models.IntegerField('终止页的行中字序号', default=-1)
    f_text = models.TextField('调整经文', default='', null=True)

    class Meta:
        verbose_name = '实体藏经卷'
        verbose_name_plural = '实体藏经卷'
        unique_together = (('sutra', 'reel_no'),)

    def __str__(self):
        return '%s (第%s卷)' % (self.sutra, self.reel_no)

    @classmethod
    def extract_page_line_separators(cls, text):
        if text == '':
            return None
        pages = text.split('\np\n')
        print(len(pages))
        if pages[0].startswith('p\n'):
            pages[0] = pages[0][2:]
        separators = []
        pos = 0
        page_index = 0
        page_count = len(pages)
        print(pages[0][0:20])
        while page_index < page_count:
            lines = pages[page_index].split('\n')
            line_cnt = len(lines)
            i = 0
            while i < line_cnt:
                pos += len(lines[i])
                if i == (line_cnt - 1) and page_index != (page_count - 1):
                    separators.append( (pos, 'p') )
                else:
                    separators.append( (pos, '\n') )
                i += 1
            page_index += 1
        return separators

class Page(models.Model):
    pid = models.CharField('页ID', editable=True, max_length=18) #YB000011v001p00010
    reel = models.ForeignKey(Reel, verbose_name='实体藏经卷', on_delete=models.CASCADE)
    vol_no = models.SmallIntegerField('册序号')
    page_no = models.SmallIntegerField('页序号') 
    text = models.TextField('经文')

    class Meta:
        verbose_name = '实体藏经页'
        verbose_name_plural = '实体藏经页'

    def __str__(self):
        return '第%s册第%s页' % (self.vol_no, self.page_no)


# class Character(models.Model):
#     cid = models.CharField('经字号', max_length=23, primary_key=True)
#     sutra = models.ForeignKey(Sutra, on_delete=models.CASCADE)
#     reel_no = models.SmallIntegerField('卷序号')
#     vol_no = models.SmallIntegerField('册序号')
#     page_no = models.SmallIntegerField('页序号') 
#     line_no = models.SmallIntegerField('行号')
#     char_no = models.SmallIntegerField('字号')
#     ch = models.CharField('文字', max_length=2)
#     c_conf = models.FloatField('识别置信度', default=0.0)
#     updated_at = models.DateTimeField('更新时间', default=timezone.now)

#     class Meta:
#         verbose_name = '字信息'
#         verbose_name_plural = '字信息'

