from django.db import models
from tsdata.models import Page,Tripitaka,Reel,LQReel,Sutra

from tdata.lib.fields import JSONField
from tdata.lib.image_name_encipher import get_signed_path


#Create your models here.

class data_tripitaka_description(models.Model):
    tripitaka = models.ForeignKey(Tripitaka, on_delete=models.CASCADE, verbose_name='藏名')
    store_description = models.CharField(verbose_name='存储描述', max_length=255, blank=False)# json :path1、path2、path3        

    class Meta:
        verbose_name = '实体藏描述'
        verbose_name_plural = '实体藏描述'
    
class data_lqreel(models.Model):
    lqreel = models.ForeignKey(LQReel, on_delete=models.CASCADE, verbose_name='龙泉经卷')
    base_reel = models.ForeignKey(Reel, on_delete=models.CASCADE, verbose_name='底本卷')
    collate_txt =  models.TextField('校对文本', blank=True, default='') 
    punct_txt = models.TextField('标点文本', blank=True, default='') 

    class Meta:
        verbose_name = u"龙泉卷经文"
        verbose_name_plural = u"龙泉卷经文"

class data_reel(models.Model):    
    reel = models.ForeignKey(Reel, on_delete=models.CASCADE, verbose_name='龙泉经卷')    
    txt  = models.TextField('经文', blank=True, default='') 

    class Meta:
        verbose_name = u"实体卷经文"
        verbose_name_plural = u"实体卷经文"

class data_page(models.Model):    
    page = models.ForeignKey(Page, verbose_name='实体藏经页', on_delete=models.CASCADE, editable=False)
    #page_code page 上面有这个值

    reel = models.ForeignKey(Reel, on_delete=models.CASCADE, verbose_name='龙泉经卷')    
    txt  = models.TextField('经文', blank=True, default='') 
    image_path = models.CharField(verbose_name='图片路径', max_length=255, blank=False) 
    ocr_char_cut = JSONField(verbose_name='文字切分', default=dict)
    ocr_col_cut = JSONField(verbose_name='列切分', default=dict)
    ocr_block_cut = JSONField(verbose_name='区块切分', default=dict)
    ocr_txt  = models.TextField('ocr识别文字', blank=True, default='') 
    confirm_char_cut = JSONField(verbose_name='确认文字切分', default=dict)
    confirm_col_cut = JSONField(verbose_name='确认列切分', default=dict)
    confirm_block_cut = JSONField(verbose_name='确认区块切分', default=dict)
    confirm_txt  = models.TextField('确认ocr识别文字', blank=True, default='') 
    mark_txt = models.TextField('格式标注文本', blank=True, default='')#跨页格式，拆分两份

    class Meta:
        verbose_name = u"实体经页数据"
        verbose_name_plural = u"实体经页数据"
    
class data_column(models.Model):    
    page = models.ForeignKey(Page, verbose_name='实体藏经页', on_delete=models.CASCADE, editable=False)    
    #page_code page 上面有这个值
    column_code = models.CharField(max_length=23, blank=False)
    column_no = models.CharField(max_length=23, blank=False)
    
    image_path = models.CharField(verbose_name='图片路径', max_length=255, blank=False) 
        
    x = models.SmallIntegerField('X坐标', default=0)
    y = models.SmallIntegerField('Y坐标', default=0)
    x1 = models.SmallIntegerField('X1坐标', default=0)
    y1 = models.SmallIntegerField('Y1坐标', default=0)
    

    class Meta:
        verbose_name = u"列切分数据"
        verbose_name_plural = u"列切分数据"

class data_char(models.Model):    
    tripitaka = models.ForeignKey(Tripitaka, on_delete=models.CASCADE, verbose_name='藏名')    #page_code page 上面有这个值
    char_code = models.CharField(max_length=23, blank=False)
    sutra = models.ForeignKey(Sutra, verbose_name='实体经', on_delete=models.CASCADE, editable=False)
    reel = models.ForeignKey(Reel, verbose_name='实体藏经卷', on_delete=models.CASCADE, editable=False)
    page = models.ForeignKey(Page, verbose_name='实体藏经页', on_delete=models.CASCADE, editable=False)    
    char = models.CharField(max_length=2, blank=False)    
    similarity = models.FloatField(null=True, blank=True, verbose_name=u'相似度', default=1)
    
    image_path = models.CharField(verbose_name='图片路径', max_length=255, blank=False)
    x = models.SmallIntegerField('X坐标', default=0)
    y = models.SmallIntegerField('Y坐标', default=0)
    x1 = models.SmallIntegerField('X1坐标', default=0)
    y1 = models.SmallIntegerField('Y1坐标', default=0)    

    class Meta:
        verbose_name = u"列切分数据"
        verbose_name_plural = u"列切分数据"        