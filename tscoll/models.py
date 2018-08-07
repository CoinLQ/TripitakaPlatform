from django.db import models
from tsdata.models import Page,Tripitaka,Reel,LQReel,Sutra,LQSutra
from jwt_auth.models import Staff

class TaskStatus(object):
    STATUS_NOT_READY = 1
    STATUS_READY = 2
    STATUS_PROCESSING = 3
    STATUS_FINISHED = 4
    STATUS_PAUSED = 5
    STATUS_REMINDED = 6
    STATUS_REVOKED = 7
    STATUS_SYSTEM_PAUSED = 8
    CHOICES = (
        (STATUS_NOT_READY, '未就绪'),
        (STATUS_READY, '待领取'),
        (STATUS_PROCESSING, '进行中'),
        (STATUS_PAUSED, '已暂停'),
        (STATUS_FINISHED, '已完成'),
        (STATUS_REMINDED, '已催单'),
        (STATUS_REVOKED, '已回收'),
        (STATUS_SYSTEM_PAUSED, '系统内暂停'),
    )

class PriorityLevel(object):
    LOW = 1
    MIDDLE = 2
    HIGH = 3

    CHOICES = (
        (LOW, u'低'),
        (MIDDLE, u'中'),
        (HIGH, u'高'),
    )

class BaseTask(models.Model):
    status = models.SmallIntegerField(verbose_name='状态', choices=TaskStatus.CHOICES, default=TaskStatus.STATUS_NOT_READY)
    priority = models.SmallIntegerField(verbose_name='优先级', choices=PriorityLevel.CHOICES, default=PriorityLevel.LOW)
    executor = models.ForeignKey(Staff, null=True, blank=True, on_delete=models.SET_NULL, related_name='executor')
    picked_at = models.DateTimeField(verbose_name='执行时间', null=True, blank=True)
    finished_at = models.DateTimeField(verbose_name='完成时间', null=True, blank=True)
    creator = models.ForeignKey(Staff, verbose_name='创建人', blank=True, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    class Meta:
       abstract = True

# Create your models here.

#【proofread】 标记: 文字校对
class proofread_reelstatus(models.Model):
    reel = models.ForeignKey(Reel, verbose_name='实体藏经卷', on_delete=models.CASCADE, editable=False)
    initial_1st_status = models.SmallIntegerField(verbose_name='初较状态')
    initial_2nd_status = models.SmallIntegerField(verbose_name='二较状态')
    initial_3rd_status = models.SmallIntegerField(verbose_name='三较状态')
    initial_4th_status = models.SmallIntegerField(verbose_name='四较状态')
    confirm_status  = models.SmallIntegerField(verbose_name='审定状态')
    is_reel_images_ready =   models.BooleanField(verbose_name='卷图片就绪', default=True)
    page_images_check =   models.SmallIntegerField(verbose_name='页图检查')
    page_images_check_time = models.DateTimeField(verbose_name='页图检查时间', auto_now=True)      

    is_reel_cut_ready =   models.BooleanField(verbose_name='切分就绪', default=True)
    page_cut_check =   models.SmallIntegerField(verbose_name='页切分检查')
    page_cut_check_time =   models.DateTimeField(verbose_name='页图检查时间', auto_now=True)

    is_compare_reel_text_ready =   models.BooleanField(verbose_name='比较卷文本就绪', default=True)
    compare_reel_text_check_time =   models.DateTimeField(verbose_name='比较卷文本检查时间', auto_now=True)

    is_reel_text_ready =   models.BooleanField(verbose_name='卷文本就绪', default=True)
    page_text_check =   models.SmallIntegerField(verbose_name='页文本检查')
    reel_text_check_time =   models.DateTimeField(verbose_name='卷文本检查时间', auto_now=True)    

    remark = models.TextField('备注', blank=True, default='')    

    class Meta:
        verbose_name = u"卷状态"
        verbose_name_plural = u"卷状态"
 
#*proofread_comparetxt  id  lqsutra  source  txt  remark  
class proofread_comparetxt(models.Model):
    lqstura = models.ForeignKey(LQSutra, verbose_name='龙泉经', on_delete=models.CASCADE, editable=False)        
    source = models.TextField('源文本', blank=True, default='') 
    txt = models.TextField('目标文本', blank=True, default='') 
    remark = models.TextField('备注', blank=True, default='')    

    class Meta:
        verbose_name = u"比较文本"
        verbose_name_plural = u"比较文本"

#*proofread_task
class proofread_task(models.Model):
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

    reel = models.ForeignKey(Reel, verbose_name='实体藏经卷', on_delete=models.CASCADE, editable=False)        
    stage = models.SmallIntegerField(verbose_name='阶段') #stage  0表示初校，1表示审定  
    initial_task_no = models.SmallIntegerField(verbose_name='阶段') #initial_task_no  1表示初校校一，2表示初校校二，3表示初校校三，4表示初校校四
    priority = models.SmallIntegerField('优先级', default=2) # 1,2,3分别表示低，中，高
    status = models.SmallIntegerField('状态', choices=STATUS_CHOICES, default=1, db_index=True)
    ocr_txt = models.TextField('OCR文本', blank=True, default='') 
    result_txt= models.TextField('结果文本', blank=True, default='') 
    
    # 用于记录当前工作的条目，下次用户进入任务时直接到此。
    # 文字校对，表示CorrectSeg的id；校勘判取表示page
    cur_focus = models.IntegerField('当前工作的条目', default=0)

    creator = models.CharField(verbose_name='创建人', max_length=255, blank=True)
    created_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)      

    executor = models.CharField(verbose_name='执行人', max_length=255, blank=True)
    picked_at = models.DateTimeField(verbose_name='执行时间', auto_now=True)      
    finished_at = models.DateTimeField(verbose_name='完成时间', auto_now=True)

    class Meta:
        verbose_name = u"文字校对任务"
        verbose_name_plural = u"文字校对任务"

#*proofread_difficultytask  
class proofread_difficultytask(models.Model):
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

    reel = models.ForeignKey(Reel, verbose_name='实体藏经卷', on_delete=models.CASCADE, editable=False)                
    status = models.SmallIntegerField('状态', choices=STATUS_CHOICES, default=1, db_index=True)
    result_txt= models.TextField('结果文本', blank=True, default='') 
    
    creator = models.CharField(verbose_name='创建人', max_length=255, blank=True)
    created_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)      

    executor = models.CharField(verbose_name='执行人', max_length=255, blank=True)
    picked_at = models.DateTimeField(verbose_name='执行时间', auto_now=True)      
    finished_at = models.DateTimeField(verbose_name='完成时间', auto_now=True)

    class Meta:
        verbose_name = u"难字任务"
        verbose_name_plural = u"难字任务"

#*proofread_seg
class proofread_seg(models.Model):    
    proofread_task = models.ForeignKey(proofread_task, verbose_name='文字校对任务', on_delete=models.CASCADE, editable=False)        
    page_code = models.CharField(max_length=23, blank=False) #参考 page表
    page_no = models.SmallIntegerField('页序号')
    line_no = models.SmallIntegerField('行序号')
    char_no = models.SmallIntegerField('子序号')
    offset = models.IntegerField('所在卷文本在整部经文中位置', default=0)
    txt1 = models.TextField('初校文本', blank=True, default='') 
    txt2 = models.TextField('二校文本', blank=True, default='') 
    txt3 = models.TextField('三校文本', blank=True, default='') 
    txt4 = models.TextField('四校文本', blank=True, default='') 
    compare_type = models.SmallIntegerField('页序号')    
    selected_txt= models.TextField('选定文本', blank=True, default='')

    class Meta:
        verbose_name = u"文字校对？"
        verbose_name_plural = u"文字校对？"

#*proofread_task
class proofread_doubt(models.Model):
    proofread_task = models.ForeignKey(proofread_task, verbose_name='文字校对任务', on_delete=models.CASCADE, editable=False)            
    page_code = models.CharField(max_length=23, blank=False) #参考 page表
    page_no = models.SmallIntegerField('页序号')
    line_no = models.SmallIntegerField('行序号')
    start_char_no = models.SmallIntegerField('开始字序号')
    start_char_no = models.SmallIntegerField('结束字序号')    
    doubt_text = models.TextField('存疑文本', blank=True, default='') 
    doubt_comment = models.TextField('存疑说明', blank=True, default='') 
    status = models.SmallIntegerField('状态',  default=1 )#status  0表示未处理，1表示已处理  
    creator = models.CharField(verbose_name='创建人', max_length=255, blank=True)
    created_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)    
    
    executor = models.CharField(verbose_name='执行人', max_length=255, blank=True)
    executed_at = models.DateTimeField(verbose_name='执行时间', auto_now=True)
    class Meta:
        verbose_name = u"文字校对存疑"
        verbose_name_plural = u"文字校对存疑"

class proofread_difficulty(models.Model):
    proofread_difficultytask = models.ForeignKey(proofread_difficultytask, verbose_name='文字校对任务', on_delete=models.CASCADE, editable=False)            
    page_code = models.CharField(max_length=23, blank=False) #参考 page表
    page_no = models.SmallIntegerField('页序号')
    line_no = models.SmallIntegerField('行序号')
    start_char_no = models.SmallIntegerField('开始字序号')
    start_char_no = models.SmallIntegerField('结束字序号')    
    doubt_text = models.TextField('存疑文本', blank=True, default='') 
    doubt_comment = models.TextField('存疑说明', blank=True, default='') 
    status = models.SmallIntegerField('状态',  default=1 )#status  0表示未处理，1表示已处理  
    creator = models.CharField(verbose_name='创建人', max_length=255, blank=True)
    created_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)    
    
    executor = models.CharField(verbose_name='执行人', max_length=255, blank=True)
    executed_at = models.DateTimeField(verbose_name='执行时间', auto_now=True)
    class Meta:
        verbose_name = u"文字校对难字"
        verbose_name_plural = u"文字校对难字"

# mark_reelstatus         
class mark_reelstatus(models.Model):
    reel = models.ForeignKey(Reel, verbose_name='实体藏经卷', on_delete=models.CASCADE, editable=False)        
    initial_1st_status = models.SmallIntegerField(verbose_name='初较状态')
    initial_2nd_status = models.SmallIntegerField(verbose_name='二较状态')    
    confirm_status  = models.SmallIntegerField(verbose_name='审定状态')    
    remark = models.TextField('备注', blank=True, default='') 
    class Meta:
        verbose_name = u"标注状态"
        verbose_name_plural = u"标注状态"

#*mark_task
class mark_task(models.Model):
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

    reel = models.ForeignKey(Reel, verbose_name='实体藏经卷', on_delete=models.CASCADE, editable=False)        
    stage = models.SmallIntegerField(verbose_name='阶段') #stage  0表示初校，1表示审定  
    initial_task_no = models.SmallIntegerField(verbose_name='阶段') #initial_task_no  1表示初校校一，2表示初校校二，3表示初校校三，4表示初校校四
    priority = models.SmallIntegerField('优先级', default=2) # 1,2,3分别表示低，中，高
    status = models.SmallIntegerField('状态', choices=STATUS_CHOICES, default=1, db_index=True)
    initial_txt = models.TextField('初始化文本', blank=True, default='') 
    result_txt= models.TextField('结果文本', blank=True, default='')         
    
    creator = models.CharField(verbose_name='创建人', max_length=255, blank=True)
    created_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)      

    executor = models.CharField(verbose_name='执行人', max_length=255, blank=True)
    picked_at = models.DateTimeField(verbose_name='执行时间', auto_now=True)      
    finished_at = models.DateTimeField(verbose_name='完成时间', auto_now=True)

    class Meta:
        verbose_name = u"标注任务"
        verbose_name_plural = u"标注任务"

#collate_reelstatus 
class collate_reelstatus(models.Model):
    lqreel = models.ForeignKey(LQReel, verbose_name='龙泉经卷', on_delete=models.CASCADE, editable=False)        
    collate_tripitaka_sutras = models.SmallIntegerField(verbose_name='校勘状态')
    initial_1st_status = models.SmallIntegerField(verbose_name='初较状态')
    initial_2nd_status = models.SmallIntegerField(verbose_name='二较状态')
    initial_3rd_status = models.SmallIntegerField(verbose_name='三较状态')
    initial_4th_status = models.SmallIntegerField(verbose_name='四较状态')
    confirm_status  = models.SmallIntegerField(verbose_name='审定状态')    
    remark = models.TextField('备注', blank=True, default='')    

    class Meta:
        verbose_name = u"校勘状态"
        verbose_name_plural = u"校勘状态"

# collate_task
class collate_task(models.Model):
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

    lqreel = models.ForeignKey(LQReel, verbose_name='龙泉经卷', on_delete=models.CASCADE, editable=False)
    stage = models.SmallIntegerField(verbose_name='阶段') #stage  0表示初校，1表示审定  
    initial_task_no = models.SmallIntegerField(verbose_name='阶段') #initial_task_no  1表示初校校一，2表示初校校二，3表示初校校三，4表示初校校四
    priority = models.SmallIntegerField('优先级', default=2) # 1,2,3分别表示低，中，高
    status = models.SmallIntegerField('状态', choices=STATUS_CHOICES, default=1, db_index=True)
    initial_txt = models.TextField('初始化文本', blank=True, default='') 
    result_txt= models.TextField('结果文本', blank=True, default='')         
    
    creator = models.CharField(verbose_name='创建人', max_length=255, blank=True)
    created_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)      

    executor = models.CharField(verbose_name='执行人', max_length=255, blank=True)
    picked_at = models.DateTimeField(verbose_name='执行时间', auto_now=True)      
    finished_at = models.DateTimeField(verbose_name='完成时间', auto_now=True)

    class Meta:
        verbose_name = u"标注任务"
        verbose_name_plural = u"标注任务"
        
#*collate_seg                            
class collate_seg(models.Model):
    collate_task = models.ForeignKey(collate_task, verbose_name='校勘任务', on_delete=models.CASCADE, editable=False)                
    base_pos = models.IntegerField('在基准文本中位置', default=0) # base_pos=0表示在第1个字前，base_pos>0表示在第base_pos个字后
    base_length = models.IntegerField('基准文本中对应文本段长度', default=0)
    selected_txt= models.TextField('选定文本', blank=True, default='')
    split_info = models.TextField('拆分信息', blank=True, null=True, default='{}')#json
    status = models.SmallIntegerField('状态',  default=1 )#status  0表示未处理，1表示已处理  
    if_doubt =  models.BooleanField(verbose_name='是否存疑', default=True)
    doubt_comment = models.TextField('存疑说明', blank=True, default='') 
    all_equal =   models.BooleanField(verbose_name='全部相同', default=True)
    
    class Meta:
        verbose_name = u"校勘片段"
        verbose_name_plural = u"校勘片段"        


#*collate_merge
class collate_merge(models.Model):
    collate_task = models.ForeignKey(collate_task, verbose_name='校勘任务', on_delete=models.CASCADE, editable=False)            
    start_collate_seg = models.ForeignKey(collate_seg, verbose_name='开始校勘片段', on_delete=models.CASCADE, editable=False)                
    merge_info  = models.TextField('合并信息', blank=True, null=True, default='{}')#json

    class Meta:
        verbose_name = u"校勘合并"
        verbose_name_plural = u"校勘合并"

#*collate_segtxt
class collate_segtxt(models.Model):
    tripitaka = models.ForeignKey(Tripitaka, on_delete=models.CASCADE, verbose_name='藏名')
    collate_seg = models.ForeignKey(collate_seg, verbose_name='开始校勘片段', on_delete=models.CASCADE, editable=False)                        
    text  = models.TextField('经文', blank=True, null=True, default='{}')#json
    position = models.IntegerField('在卷文本中的位置（前有几个字）', default=0)
    offset = models.IntegerField('所在卷文本在整部经文中位置', default=0)
    start_char_pos = models.CharField('起始经字位置', max_length=32, default='', null=True)
    end_char_pos = models.CharField('结束经字位置', max_length=32, default='', null=True)

    class Meta:
        verbose_name = u"校勘片段文本"
        verbose_name_plural = u"校勘片段文本"

#punct_reelstatus 
class punct_reelstatus(models.Model):
    lqreel = models.ForeignKey(LQReel, verbose_name='龙泉经卷', on_delete=models.CASCADE, editable=False)
    initial_1st_status = models.SmallIntegerField(verbose_name='初较状态')
    initial_2nd_status = models.SmallIntegerField(verbose_name='二较状态')
    initial_3rd_status = models.SmallIntegerField(verbose_name='三较状态')
    initial_4th_status = models.SmallIntegerField(verbose_name='四较状态')
    confirm_status  = models.SmallIntegerField(verbose_name='审定状态')       
    remark = models.TextField('备注', blank=True, default='')
    class Meta:
        verbose_name = u"标点状态"
        verbose_name_plural = u"标点状态" 

# *punct_task  
class punct_task(models.Model):
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

    lqreel = models.ForeignKey(LQReel, verbose_name='龙泉经卷', on_delete=models.CASCADE, editable=False)
    punct_base = models.TextField('基础标点', blank=True, default='') 
    stage = models.SmallIntegerField(verbose_name='阶段') #stage  0表示初校，1表示审定  
    initial_task_no = models.SmallIntegerField(verbose_name='阶段') #initial_task_no  1表示初校校一，2表示初校校二，3表示初校校三，4表示初校校四
    priority = models.SmallIntegerField('优先级', default=2) # 1,2,3分别表示低，中，高
    status = models.SmallIntegerField('状态', choices=STATUS_CHOICES, default=1, db_index=True)
    punct_txt = models.TextField('初始化文本', blank=True, default='') 
    
    
    cur_focus = models.IntegerField('当前工作的条目', default=0)

    creator = models.CharField(verbose_name='创建人', max_length=255, blank=True)
    created_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)      

    executor = models.CharField(verbose_name='执行人', max_length=255, blank=True)
    picked_at = models.DateTimeField(verbose_name='执行时间', auto_now=True)      
    finished_at = models.DateTimeField(verbose_name='完成时间', auto_now=True)

    class Meta:
        verbose_name = u"标点任务"
        verbose_name_plural = u"标点任务"
#=============================================================================
