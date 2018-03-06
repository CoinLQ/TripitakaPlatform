from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from tdata.models import *
from tasks.models import *
from django.db.utils import IntegrityError


import TripitakaPlatform.settings

import os, sys
from os.path import isfile, join
import traceback

from difflib import SequenceMatcher
import re, json
import xlrd

#测试输出的函数
def myTestprint(info):
    # try:
    #     print(info)
    # except:
    #     print('myprintError.')
    return None

tcode_lst1 = ['PL', 'SX', 'YB', 'QL', 'ZH', 'QS', 'ZC']
tcode_lst2 = ['GL', 'LC']
#
#入口类
#
class Command(BaseCommand):
    #FUNC_0  handle
    def handle(self, *args, **options):
        BASE_DIR = settings.BASE_DIR

        try:
            lqsutra = LQSutra.objects.get(sid='LQ003100') #大方廣佛華嚴經60卷
        except:
            # create LQSutra
            lqsutra = LQSutra(sid='LQ003100', name='大方廣佛華嚴經', total_reels=60)
            lqsutra.save()
        
        #导入龙泉经目 OK            
        # self.ImportLQSutra()
                                  

        # #1) call 获得或创建管理员  OK
        # admin= self.CreateAdmin()

        #导入经目  OK
        # self.ImportSutra()

        #导入详目    ok
        self.ImportSutraJuan()     
   
        return None
                             

    #FUNC_1 CreateAdmin 获得或创建管理员
    def CreateAdmin(self):
        admin=None
        try :            
            admin = User.objects.get_by_natural_key('admin') 
        except User.DoesNotExist:  
            print("查询用户错误")

        if (admin):
            print("已经存在admin用户了")            
        else:                             
            admin = User.objects.create_superuser('admin', 'admin@example.com', 'longquan')
            print("创建admn用户")
        return admin

    #FUNC_2 ImportSutraJuan 导入详目  
    # 1           2           3           4           5       6           7           8      9       
    # 龍泉編碼	高麗編碼	實體經名	    卷序號	    起始冊碼	起始頁碼	終止頁碼	終止冊碼	備註
    # LQ0246	GL0001	 大般若波羅蜜多經	0	      1	        1	      2	           1	    序
    #sutra = '实体藏经',           第二列
    #reel_no =                    第四列
    #start_vol = ('起始册')        第五列
    #start_vol_page = ('起始页')   第六列
    #end_vol = '终止册')           第八列
    #end_vol_page = ('终止页')     第七列
    def ImportSutraJuan(self):                 
        BASE_DIR = settings.BASE_DIR
        sutra_libs_file = '/data/xiangmu'        
        jingmufils=self.__get_excel_file(BASE_DIR+sutra_libs_file)
        #Reel.objects.all().delete()
        #藏经版本
        
        reel_lst = []
        reel_lst.append('reel_list.txt')
        key=('sid','name','reel_no','start_v','start_p','end_v','end_p','remark')
        reel_lst.append(key)

        reel_no_str_set = set()
        # load data
        for oneSutraFile in jingmufils :
            print (oneSutraFile)
            data = xlrd.open_workbook(oneSutraFile)
            table = data.sheets()[0]
            nrows = table.nrows
            ncols = table.ncols
            errorlist=[]
            #解析属性     
            
            #先获得tripitaka
            tripitaka=self.__get_tripitaka( nrows , table ,errorlist )            
            pre_sutra_sid=''
            pre_sutra_name=''
            sutra=None
            for i in range(nrows):
                if (tripitaka == None) : break 
                
                if i  >0   :
                    try:
                        #初始化
                        sutra_sid='' ; reel_no=-1
                        start_vol=-1 ; start_vol_page=-1
                        end_vol=-1   ; end_vol_page=-1                    
                        errMsg='' ; remark=''
                        myTestprint(i)
                        values = table.row_values(i)  
                        myTestprint(values) 
                        remark=str(values[8]) 
                        if (remark == None )                             :
                            remark=''

                        #对应经对象的获得 sutra_sid = '实体藏经的id',第二列   
                        changed , newSutra , errMsg=self.__get_sutra( i, values , tripitaka , 
                                         errorlist , errMsg ,pre_sutra_sid   ,pre_sutra_name,remark )
                        if (not changed):
                            pass 
                        elif (changed and newSutra):
                            sutra_sid=newSutra.sid
                            pre_sutra_sid=newSutra.sid
                            pre_sutra_name=newSutra.name
                            sutra=newSutra
                        else:
                            continue                                                
                        
                        #其他数据列获得
                        #['', 'QS0001', '大般若波羅蜜多經', 502.0, 10.0, 634.0, 10.0, '缺頁', '缺頁', '']                         
                        reel_no,start_vol,start_vol_page,end_vol,end_vol_page,errMsg = self.__get_intColumnValue(
                             values,reel_no,start_vol,start_vol_page,end_vol,end_vol_page,errMsg)
                        #更新 errMsg、remark
                        if (len(errMsg.strip())>0):
                            errMsg= "行"+str(i+1)+":"+errMsg
                        if (len(remark)>0 and len(errMsg.strip()) >0 ):
                            remark=errMsg+'('+remark+')'
                        
                        #创建卷对象
                        if reel_no < 0:
                            errMsg= "行"+str(i+1)+": reel_no<0"
                        reel_no_str = '%s%03d' % (sutra.sid, reel_no)
                        #if reel_no > 0 and reel_no_str not in reel_no_str_set:
                        print('reel: ', reel_no_str)
                        reel_no_str_set.add(reel_no_str)
                        # reel = Reel(sutra=sutra,reel_no=reel_no, start_vol=start_vol,start_vol_page=start_vol_page
                        #                 , end_vol= end_vol, end_vol_page=end_vol_page,remark=remark )
                        #key=('sid','name','reel_no','start_vol_page','end_vol','end_vol_page','remark')
                        d={}
                        d['sid']=sutra.sid
                        d['name']=sutra.name
                        d['reel_no']=reel_no
                        d['start_v']=start_vol                        
                        d['start_p']=start_vol_page
                        d['end_v']=end_vol                            
                        d['end_p']=end_vol_page
                        d['remark']=remark                                                            
                        reel_lst.append(d) 
                        print(d)
                            # if sutra.tripitaka.code in tcode_lst1 and reel.start_vol > 0:
                            #     reel.path1 = str(reel.start_vol)
                            # elif sutra.tripitaka.code in tcode_lst1:
                            #     reel.path1 = str(int(sutra.code))
                            #     reel.path2 = str(reel.reel_no)
                            #reel_lst.append(reel)
                        if (len(errMsg)>0):                                          
                            myTestprint(errMsg)                                          
                            errorlist.append(errMsg)                                                                                                           
                        myTestprint('end')
                    except IntegrityError as e:
                        strunique='duplicate key value violates unique constraint "tdata_reel_sutra_id_reel_no_c9f0f174_uniq'
                        err='%s' % e
                        if (err.find(strunique)>-1):
                            errMsg='经号+卷号重复，无法导入此记录。'+err
                            a="(error_a) "
                        else:
                            errMsg=err
                            a="(error_b) "    
                        a='行'+str(i+1)+":"+a+errMsg
                        print(a)                                          
                        errorlist.append(a)
                    except :  
                        a='行'+str(i+1)+':(error_c) '+errMsg 
                        print(a)                                          
                        errorlist.append(a)  
                    # break                     
            #break                                       
            fl=open(oneSutraFile+'.log', 'w')
            for s in errorlist:
                fl.write(s)
                fl.write("\n")
            fl.write('共%d条记录' % len(errorlist))    
            fl.close()
            #break
        #Reel.objects.bulk_create(reel_lst)
        self.__save_data(reel_lst)
        return None          

   #FUNC_3 ImportSutra 导入经目
    #class Sutra(models.Model, TripiMixin):
    # lqsutra       对应模板第一列
    # sid =         对应模板第二列    
    # tripitaka     对应模板第二列，要解析前两位
    # variant_code  对应模板第二列，要解析横杠后面
    # name          对应模板第三列
    # total_reels   对应模板第四列
    # remark       对应模板第十列    
    #   A       B           C             D     E             F         G        H           I       J
    #龙泉编码	高丽初刻编码	實體經名	    卷序號	实际卷数	起始冊碼	起始頁碼	終止頁碼	終止冊碼	備註
    #LQ0246	   GLCK0001	  大般若波羅蜜多經	481	    4	       1	     65	       86	        1	    备注。。。  

    def ImportSutra(self):                   
        BASE_DIR = settings.BASE_DIR
        sutra_libs_file = '/data/jingmu'        
        jingmufils=self.__get_excel_file(BASE_DIR+sutra_libs_file)
        #Sutra.objects.all().delete()
        errorlist=[]
        # load data
        sutra_lst = []
        sutra_lst.append('sutra_list.txt')
        key=('sid','tripitaka','name','lqsutra','total_r','remark')
        sutra_lst.append(key)
        sid_set = set()
        for oneSutraFile in jingmufils :
            print (oneSutraFile)
            errorlist.append(oneSutraFile)
            data = xlrd.open_workbook(oneSutraFile)
            table = data.sheets()[0]
            nrows = table.nrows
            ncols = table.ncols
            tripitaka_id=''#藏只有一次
            #解析属性
            for i in range(nrows):
                if i  >0   :
                    try:      
                        errMsg='';    lqsutra_id='';   sid=''                        
                        variant_code=''; code=''
                        name='' ;     total_reels=-1;  remark='';
                        
                        values = table.row_values(i)#第i行数据
                        sid=str(values[1])#  经ID             
                        name=str(values[2]).strip() #name          对应模板第三列
                        if (   len( name ) ==0 ):
                            errMsg+='存疑A,经名为空。name:'+name+'。'                          
                        
                        # lqsutra       对应模板第一列
                        lqsutra_id=str(values[0]).strip() #经编号 
                        lqsutra=None 
                        myTestprint(lqsutra_id)
                        if (len(lqsutra_id) == 0 ): # 空编号
                            errMsg+='存疑C,龙泉编号为空 '                            
                        elif (len(lqsutra_id)<6 ): # 编号无效 
                            errMsg+='存疑C,龙泉编号无效：'+lqsutra_id                            
                        else:           
                            bRet,lqsutra_id=self.__get_reel_sutraID(str(values[0])) #经编号
                            lqsutra_id = lqsutra_id.strip()
                            myTestprint(lqsutra_id)
                            if (not bRet ):                                
                                errMsg+='存疑C,龙泉编号不存在：'+str( values[0] ) 
                            else:                                
                                try :
                                    s=LQSutra.objects.filter(sid=lqsutra_id)
                                    if (len(s)>0):
                                        lqsutra=s[0]                                        
                                except:
                                    pass
                                if  (lqsutra == None):                                                              
                                    errMsg+='存疑C,龙泉编号不存在：'+lqsutra_id

                        #增加逻辑，判断经名是否存在，增加备注信息。2-2                        
                        if ( ( lqsutra == None )  and  ( not len( name ) ==0 ) ):                            
                            s=LQSutra.objects.filter(name__contains=name)                            
                            if( len(s) >0 ):#如果有值，给出提示。
                                a='，存在%d条经名相似的记录：'%(len(s))                                
                                for s1 in s :
                                    a+='[%s,%s] '%(s1.name ,s1.sid )                                       
                                errMsg+=a        
                                myTestprint(errMsg)                         
                        
                        # sid =         对应模板第二列                          
                        bRet,sid=self.__get_reel_sutraID(str(values[1])) #经编号                        
                        if ( not bRet ):                            
                            errMsg+='存疑B,经编号在异常。id：'+str(values[1])+' 。'  
                            if (errMsg.find('存疑A') >-1 ) :#不导入的情况。
                                errMsg+='经编号和经名都不存在，不导入。'
                                raise '经编号和经名都不存在，不导入。'  
                        else:    
                            # tripitaka     对应模板第二列，要解析前两位
                            if len(tripitaka_id)== 0 :
                                tripitaka_id=sid[0:2]
                                s=Tripitaka.objects.filter(code=tripitaka_id)
                                if (len(s)>0):
                                    tripitaka=s[0]                                
                            variant_code=sid[-1]# variant_code  对应模板第二列，要解析横杠后面
                            code=sid[2:7]#code 


                            #查看经号是否重复
                            # if len( Sutra.objects.filter(sid=sid)) >0 :
                            #     errMsg+='存疑D,经编号重复：'+sid    

                        mytotal_reels=values[3]
                        try :                            
                            total_reels=int(mytotal_reels)
                        except:
                            pass
                      
                        # remark       对应模板第9列
                        try :
                            remark=str(values[9])
                            if remark== None:
                                remark=""                                                             
                        except:
                            pass   
                        if (len(errMsg)>0):                                                        
                            a=("\n行"+str(i+1)+":"+errMsg)                    
                            myTestprint(a)
                            if (len(remark)>0):
                                remark=a+"("+remark+")"
                            else:
                                remark=a    
                            errorlist.append(a)

                        myTestprint(lqsutra_id) ; myTestprint(lqsutra);myTestprint(sid) ; myTestprint(name); 
                        myTestprint(variant_code);myTestprint("total_reels"+str(total_reels))
                        myTestprint('remark:'+remark)      ; myTestprint('tripitaka:'+tripitaka.code)
                        #key=('sid','tripitaka','name','lqsutra','total_reels','remark')
                        if sid not in sid_set:
                            sid_set.add(sid)
                            d={}
                            d['sid']=sid
                            d['name']=name
                            d['tripitaka']=tripitaka.code
                            if lqsutra ==None :
                                d['lqsutra']=''
                            else:
                                d['lqsutra']=lqsutra.sid                            
                            d['total_r']=total_reels
                            d['remark']=remark                                                            
                            sutra_lst.append(d)                                                        
                    except:
                        a=("error: "+str(i+1)+":"+str(values[0])+":"+str(values[1])+":"+str(values[2])+":"+str(values[3])+".errmsg:"+errMsg)                    
                        print(a)
                        errorlist.append(a)
                        # break                       
                    #break
            fl=open(oneSutraFile+'.log', 'w')
            for s in errorlist:
                fl.write(s)
                fl.write("\n")
            fl.write('共%d条记录' % (len(errorlist)-1)  )      
            fl.close()    
            errorlist.clear()
            #break
        self.__save_data(sutra_lst)
        return None 

    #FUNC_4 ImportLQSutra 创建龙泉藏经 龙泉经目 第一个需求
    # 4169 4692 开始不连续了
    def ImportLQSutra(self):       
        lqsutra=None
        #清空
        #LQSutra.objects.all().delete() 
        #从excel中读取
        BASE_DIR = settings.BASE_DIR
        sutra_libs_file = 'data/LQBM.xls' #龙泉编码文件
        
        # load data
        data = xlrd.open_workbook(sutra_libs_file)
        table = data.sheets()[0]
        nrows = table.nrows
        ncols = table.ncols       

        #解析属性
        lqsutra_lst = []
        lqsutra_lst.append('lqsutra_list.txt')
        key=('sid','name','total_reels','author','remark')
        lqsutra_lst.append(key)
        for i in range(nrows):
            if i > 0 :                
                values = table.row_values(i)                               
                sname=values[1]#经名
                nvolumns =1
                sauthor=str(values[2])#著者
                id=''
                try:
                    id= self.__get_LQSutraID( str(values[0]) )#转化编号
                    variant_code=id[-1]# variant_code  对应模板第二列，要解析横杠后面
                    if len(str(values[3]).strip())==0:
                        nvolumns=0
                    else:                                           
                        nvolumns= int (values[3])#卷数   
                    d={}
                    d['sid']=id
                    d['name']=sname
                    d['total_reels']=nvolumns
                    d['author']=sauthor                                                            
                    lqsutra_lst.append(d)
                except:
                    print('error j='+str(i)+'value:'+str(values[3])+'::'+id+sname+str(nvolumns))
                    pass
        self.__save_data(lqsutra_lst)
        return         
    
    
    #        
    #龙泉经编号的转化 excel文件导入的为四位或者5～6位，要规范为系统的8位
    #用户数据是 四位编码 & '-' & 别本号，转化为6位编号，前面加一个0，后面加一位别本号  (0~9a~z)  
    #用户数据 like '0123', or '0123-12' -的后面是别本号                   
    def __get_LQSutraID(self,orignid):                  
        hgindex=orignid.find('-') 
        hgindex2=orignid.find('–') #兼容 –
        hgindex3=orignid.find('—') #兼容 —
        
        nbiebenhao=0
        if hgindex ==4 or hgindex2 ==4 or hgindex3 ==4 :#带有横杠的
            nbiebenhao=int(orignid[5:]) 
            print
            if (nbiebenhao<0):
                nbiebenhao*=-1#转正 兼容 ’--‘分隔符
        if (nbiebenhao<=9):
            id='LQ0'+orignid[0:4]+chr(nbiebenhao+48)
        else:
            id='LQ0'+orignid[0:4]+chr(nbiebenhao+97-10)                
        return id
    
    #
    #转化整形值
    #
    def __is_can_getnum(self,value):         
        try :
            n=int(value)
            return True
        except:
            return False
    

    #
    #实体藏经编号的转化 excel文件导入的为6位，要规范为系统的8位
    #用户数据是 四位编码 & '-' & 别本号，转化为6位编号，前面加一个0，后面加一位别本号  (0~9a~z)  
    #用户数据 like '0123', or '0123-12' -的后面是别本号                   
    def __get_reel_sutraID(self,orignid):     
        #判断是否是一个有效的编号：逻辑为第三个字符应该数字
        if ( orignid ==None or len(orignid) < 3 ):
            return False,orignid
        else:
            nasc=ord(orignid[2:3])
            if not ( nasc >= 48 and nasc <= 57 ):
                return False,orignid                    

        hgindex=orignid.find('-') 
        hgindex2=orignid.find('–') #兼容 –
        hgindex3=orignid.find('—') #兼容 —                        

        nbiebenhao=0
        #if hgindex ==6 :#带有横杠的
        if hgindex ==6 or hgindex2 ==6 or hgindex3 ==6 :#带有横杠的
            nbiebenhao=int(orignid[7:]) 
        if (nbiebenhao <= 9 ) :
            id=orignid[0:2]+'0'+orignid[2:6]+chr(nbiebenhao+48)
        else:
            id=orignid[0:2]+'0'+orignid[2:6]+chr(nbiebenhao+97-10)                
        return True,id


    #    
    #遍历文件夹，获取所有xls文件名
    #
    def __get_excel_file(self,path):
        """
        用于文字校对前的文本比对
        text1是基础本，不包含换行符和换页标记；text2是要比对的版本，包含换行符和换页标记。
        """
        _pathList=[]
        filepath = path
        
        fileTypes = ['.xlsx','.xls']
        
        if os.path.isdir(filepath):
            pathDir =  os.listdir(filepath)
            
            for allDir in pathDir:
                child = os.path.join('%s/%s' % (filepath, allDir))
                if os.path.isdir(child):
                    _pathList.append(__get_excel_file(child))
                    pass
                else:
                    typeList = os.path.splitext(child)
                    if typeList[1] in fileTypes:#check file type:.txt
                        _pathList.append(child)
                        #print('child:','%s' % child.encode('utf-8','ignore'))
                        pass
                    else:#not .txt
                        pass
                
            pass
        else:
            typeList = os.path.splitext(filepath)
            if typeList[1] in fileTypes:#check file type:.txt
                _pathList.append(filepath)
                pass                            
            #print ('---',child.decode('cp936') )# .decode('gbk')是解决中文显示乱码问题
        #print(_pathList)    
        return _pathList  


    #导入卷的时候用到的获得tripitaka 的子函数    
    def __get_tripitaka(self, nrows , table ,errorlist ,):
       #先根据编号获得藏编号，当没有经编号，时要用到藏号，如果一条编号都没有就无法导入。请管理员补充数据。
        tripitaka=None
        for i in range( nrows )  :
            if (i >100 ) : break
            values = table.row_values(i)
            sutra_sid=str( values[1] ).strip()
            if len( sutra_sid ) >= 2 :#经号 #先处理经号不存在的情况
                tripitaka_id = sutra_sid[0:2]                          
                s=Tripitaka.objects.filter(code=tripitaka_id)
                if (len(s)>0):
                    tripitaka=s[0]
                    break                        
        if ( tripitaka == None ):
            a='error_d:前100条数据，经号列没有数据，无法判断藏编号。请完善数据再导入。'
            errorlist.append(a)     
        return tripitaka    


    #导入卷的时候用到的判断经id的子函数
    #主要是获得 sutra_sid \ sutra \ pre_sutra_sid \ pre_sutra_name \ errMsg
                        
    def __get_sutra(self, i, values ,tripitaka,  errorlist , errMsg , pre_sutra_sid  , pre_sutra_name , remark ):        
        #初始化 
        sutra_sid=''
        sutra=None   
        changed= True # 默认发生了变化     
        myTestprint ("__get_sutra 1 begin")
        bRet,sutra_sid=self.__get_reel_sutraID( str(values[1]) ) #经编号  
        if  bRet :#经号有效            
            myTestprint ("__get_sutra 1 :"+ sutra_sid)
            #是否换了经对象
            if  (pre_sutra_sid == sutra_sid)  :
                changed=False  # pre_sutra_sid值 没变   #  sutra 不变, pre_sutra_sid 不变, pre_sutra_name 不变, errMsg  不用写入值
                myTestprint ("__get_sutra 2 : 没有变化")
            else:# 经号变了                    
                pre_sutra_sid=sutra_sid
                s=Sutra.objects.filter(sid=sutra_sid)            
                #获得 新的经对象
                if (len(s)>0):
                    sutra=s[0]
                    myTestprint ("__get_sutra 3 通过编号获得经对象 ")
                else:#如果查不到经对象,就创建一个
                    sutra = Sutra(sid=sutra_sid, name=str(values[2]),tripitaka=tripitaka #tripitaka 的值在前面获取。
                            , remark='行号%s：存疑E。经目数据缺失，从详目补充。（%s）'%( str(i+1) ,remark ) , )                       
                    sutra.save()        
                    myTestprint ("__get_sutra 4 : 对应编号的经对象不存在, 新创建经对象")
                myTestprint(sutra)
        elif  len( str( values[2] ).strip() ) >= 2 :# 看经名是否存在
            myTestprint (" __get_sutra 5 ,经号无效,判断经名")
            newname=str( values[2] ).strip() 
            if  (pre_sutra_name == newname)  :  
                changed=False  # pre_sutra_name 值 没变   #  sutra 不变, pre_sutra_sid 不变, pre_sutra_name 不变, errMsg  不用写入值
                myTestprint (" __get_sutra 6  pre_sutra_name 没有变化")
            else: #经号不存在,通过经名判断发生了变化了.                            
                myTestprint (" __get_sutra 7  pre_sutra_name 变了")                    
                s=Sutra.objects.filter( name = newname) #过滤经名                                
                s=s.filter(tripitaka=tripitaka)#过滤藏
                #myTestprint(s)
                if (len(s)>0):
                    sutra=s[0]
                    errMsg+='存疑G,经号无效，通过经名搜索的第一个经。'
                    myTestprint (" __get_sutra 8  通过经名获得了经对象")                                
                    myTestprint(sutra)
                #else 经名无法查到,就无法导入了.下面处理.

        #判断前面的结果   #最后根据新获得的经编号及经对象,更新相关数据              
        if ( not changed ):#都不用修改,
            myTestprint (" __get_sutra 9 没有变化,直接返回")
            return changed,None,''
        if ( sutra ):#修改了,还取到了新经  sutra \ sutra_sid \ pre_sutra_sid \ pre_sutra_name 
            myTestprint (" __get_sutra 10 变化了,返回新对象")
            return changed,sutra,errMsg            
        else:# 都不存在，就跳过，记录日志。
            myTestprint (" __get_sutra 11 变化了, 但是没有这个经.记录日志,并返回")
            a=("行 "+str(i+1)+":经号无效，通过经名也无法获得经数据，无法录入系统。")
            print(a)                                           
            errorlist.append(a)   
            return changed,None,errMsg

    #获得卷 的页册等数据
    def __get_intColumnValue(self,values,reel_no,start_vol,start_vol_page,end_vol,end_vol_page,errMsg) :
        #['', 'QS0001', '大般若波羅蜜多經', 502.0, 10.0, 634.0, 10.0, '缺頁', '缺頁', '']
        #reel_no =                    第四列
        myTestprint( values[3])
        if self.__is_can_getnum( values[3]): #卷序号                             
            reel_no=int(values[3])
        else:
            errMsg+='存疑F,第4列：['+str(values[3])+']不是一个数字。'
        myTestprint('reel_no:'+ str(values[3] ) )
        
        #start_vol = ('起始册')        第五列                        
        if self.__is_can_getnum(values[4]) :
            start_vol=int(values[4])
        else:
            errMsg+='存疑F,第5列：['+str(values[4])+']不是一个数字。'
        
        #start_vol_page = ('起始页')   第六列
        if self.__is_can_getnum(values[5]) :
            start_vol_page=int(values[5])
        else:
            errMsg+='存疑F,第6列：['+str(values[5])+']不是一个数字。'                            
        myTestprint('start_vol_page:'+str(values[5]))
        
        #end_vol = '终止册')           第八列                                                
        if self.__is_can_getnum(values[7]) :
            end_vol=int(values[7])                        
        else:
            errMsg+='存疑F,第8列：['+str(values[7])+']不是一个数字。'                                                        
        myTestprint('end_vol:'+str(values[7]))
        
        #end_vol_page = ('终止页')     第七列  
        if self.__is_can_getnum(values[6]) :
            end_vol_page=int(values[6])                                                                        
        else:
            errMsg+='存疑F,第7列：['+str(values[6])+']不是一个数字。'                                                        
        myTestprint('end_vol_page:'+str(values[6]))
        
        myTestprint(reel_no)
        myTestprint(start_vol)
        myTestprint(start_vol_page)
        myTestprint(end_vol)
        myTestprint(end_vol_page)

        return  reel_no,start_vol,start_vol_page,end_vol,end_vol_page,errMsg 

     #导入卷的时候用到的获得tripitaka 的子函数    
    def __save_data(self, datalist ,):
        BASE_DIR = settings.BASE_DIR
        save_file = BASE_DIR+'/data/textdata/'+ datalist[0]        
        print(save_file)
        key=datalist[1]
        strData='#'
        for strkey in key:
            strData+=strkey+'\t'
            if ( strkey =='sid'):
                strData+='\t'
            if ( strkey =='name'):
                strData+='\t\t'

        strData+='\n'
        n=len(datalist)
        i=2                        
        while(i<n):
            d=datalist[i]
            i=i+1
            for strkey in key:
                try: 
                    strData+=str(d[strkey])+'\t'                                        
                except : pass 
            strData+='\n'    

        print(strData)    

        with open(save_file, 'w') as fout:
            fout.write(strData)
        fout.close    

        
    # #FUNC_4 LQSutra 创建某个版本的佛经
    # def CreateSutra(self,bandCode,strsid,code,var_code,sname,lqsutra,t_reels):  
    #     BASE_DIR = settings.BASE_DIR
    #     #取版本号
    #     Band = Tripitaka.objects.get(code=bandCode)#YB = Tripitaka.objects.get(code='YB')
    #     if (Band == None): 
    #         return
    #     #查看是否已经创建
    #     #下面的变量名要改的
    #     huayan_yb = None
    #     try :            
    #         huayan_yb = Sutra.objects.get(sid=strsid) 
    #     except Sutra.DoesNotExist:  
    #         print("版本["+bandCode+"]藏经不存在 ID："+strsid)

    #     if (huayan_yb):
    #          print("版本["+bandCode+"]藏经存在 ID："+strsid)
    #     else:
    #         huayan_yb = Sutra(sid=strsid, tripitaka=Band, code=code, variant_code=var_code,
    #                     name=sname, lqsutra=lqsutra, total_reels=t_reels)
    #         huayan_yb.save()
    #     return huayan_yb   
    #     pass   

    

    #remark 2018-1-25
    # def CreateLQSutra(self):        
    #     lqsutra=None
    #     strsid='LQ003100'
    #     try :            
    #         lqsutra = LQSutra.objects.get(sid=strsid) 
    #     except LQSutra.DoesNotExist:  
    #         print("藏经不存在 ID："+strsid)

    #     if (lqsutra):
    #         print("已经存在藏经 ID:"+strsid)            
    #     else:                             
    #         lqsutra = LQSutra(sid=strsid, name='大方廣佛華嚴經', total_reels=60)    
    #         print("创建华严经 ID："+strsid)
    #     lqsutra.save() 
    #     return lqsutra 


    #Func_6  ImportSutra 导入经卷
    #先导入 高丽藏第一卷 为例
    #暂时不支持重复导入，还不知道Reel表是否可以支持关键字查询
    # def ImportSutraText(self, huayan_gl,):                                
    #     BASE_DIR = settings.BASE_DIR
    #     ll=self.GetJingMuData() #获得经目数据
    #     #huayan_gl_1 = Reel(sutra=huayan_gl, reel_no=1, start_vol=14,start_vol_page=31, end_vol=14, end_vol_page=37)

    #     #读取经文
    #     fullSutraText=''#全部经文
    #     OneVolumnText=''#某卷经文
    #     filename = os.path.join(BASE_DIR, 'data/sutra_text/%s_1.txt' % huayan_gl.sid)
    #     with open(filename, 'r') as f:
    #         sutraText = f.read()
        
    #     lines = sutraText.split('\n')#全部经文行列表
    #     prePageIndex=1
    #     preVolumnIndex=1
    #     for line in lines:     
    #         line=line.replace(' ','')                          
    #         if not (line.strip() ):#过滤空行
    #             continue

    #         print(line)
    #         arr=line.split(';')               
    #         #分卷
    #         i=arr[0].find('V')+1
    #         p= int ( arr[0][i:i+3])
    #         if (p>preVolumnIndex):     
    #             #
    #         print(arr)
    #         OneVolumnText=OneVolumnText+arr[1]+'\n'  
    #         #分页
    #         i=arr[0].find('P')+1
    #         p= int ( arr[0][i:i+2])
    #         if (p>prePageIndex):
    #             prePageIndex=p
    #             OneVolumnText=OneVolumnText+'p\n'              
    #     #huayan_gl_1.save()

        # 大藏经第 卷的文本
        #huayan_sutra_1 = Reel(sutra=huayan_gl, reel_no=reel_no, start_vol=vol_no,start_vol_page=start_page_no, end_vol=vol_no, end_vol_page=end_page_no)                    
        #huayan_sutra_1.text = get_reel_text(sid, reel_no, vol_no,start_page_no, end_page_no)
        #huayan_sutra_1.save()
        #print(line_list,line_list[3],huayan_sutra_1)
        #huayan_gl_1 = Reel(sutra=huayan_gl, reel_no=1, start_vol=14,start_vol_page=31, end_vol=14, end_vol_page=37)


 
            


