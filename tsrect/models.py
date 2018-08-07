from django.db import models
from tsdata.models import Page,Tripitaka,Reel,LQReel,Sutra
from tdata.lib.fields import JSONField
from tdata.lib.image_name_encipher import get_signed_path

# Create your models here.

#切分进度表
class Pagestatus(models.Model):
    page = models.ForeignKey(Page, verbose_name='实体藏经页', on_delete=models.CASCADE, editable=False)
    #page_code page 上面有这个值
    col_cut_initial = models.SmallIntegerField(verbose_name='切列校对')
    col_cut_confirm = models.SmallIntegerField(verbose_name='切列审定')
    char_cut_initial = models.SmallIntegerField(verbose_name='切字校对')
    char_cut_confirm = models.SmallIntegerField(verbose_name='切字审定')
    remark = models.TextField('备注', blank=True, default='')    

    class Meta:
        verbose_name = u"切分进度"
        verbose_name_plural = u"切分进度"

#切分进度表
#colcutinitialtask 标记: 切列初校  
#   page  实体页的外键  page_code  
# status  priority  origin_cut  cut_result  json  
# creator  created_at  executor  picked_at  finished_at  
class CutTask(models.Model):
    page = models.ForeignKey(Page, verbose_name='实体藏经页', on_delete=models.CASCADE, editable=False)
    #page_code page 上面有这个值
    type  = models.SmallIntegerField(verbose_name='类型')
    status  = models.SmallIntegerField(verbose_name='状态')
    priority  = models.SmallIntegerField(verbose_name='优先级')
    origin_cut  = JSONField(verbose_name='原始切分', default=dict)
    cut_result  = JSONField(verbose_name='切分结果', default=dict)
    creator = models.CharField(verbose_name='创建人', max_length=255, blank=True)
    created_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)      

    executor = models.CharField(verbose_name='执行人', max_length=255, blank=True)
    picked_at = models.DateTimeField(verbose_name='执行时间', auto_now=True)      
    finished_at = models.DateTimeField(verbose_name='完成时间', auto_now=True)

    class Meta:
        verbose_name = u"切分任务"
        verbose_name_plural = u"切分任务"