from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.parsers import BaseParser,FileUploadParser,MultiPartParser
from rest_framework.response import Response
from tsdata.models import * 
#from tsbdata.models import   

import logging
import xlrd
import xlwt
from datetime import datetime
from django.conf import settings
 

logger = logging.getLogger(__name__)

def myTestprint(info):
    # try:
    #     print(info)
    # except:
    #     print('myprintError.')
    return None


class ImportSutraFromExcel(APIView):
    def post(self, request, format=None):        
        file_obj = request.FILES['excel_file'].file                
        data =xlrd.open_workbook(file_contents=file_obj.getvalue())
        table = data.sheets()[0]
        print("file:",request.FILES['excel_file'].file)
        print('rows:',table.nrows)
        
        filecount = int( request.data['filecount'])

        jingmufils=[]
        jingmufils.append(data)

        for i in range(filecount-1):
            i=i+1
            print('iii',i)
            filename = "excel_file["+str(i)+"]"
            if ( filename in request.FILES ) :
                file_obj = request.FILES[filename].file
                print("file:",file_obj)
                data =xlrd.open_workbook(file_contents=file_obj.getvalue())
                jingmufils.append(data)
                #table = data.sheets()[0]
                print('rows:',table.nrows)

        self.ImportSutra(jingmufils)
        return Response(status=200, data={
                'status': 0, 'result_file_name': ''
            })


        
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
    def ImportSutra(self,jingmufils):                   
        #BASE_DIR = settings.BASE_DIR
        #sutra_libs_file = '/data/jingmu'        
        #jingmufils=self.__get_excel_file(BASE_DIR+sutra_libs_file)
        #Sutra.objects.all().delete()
         
        errorlist=[]
        # load data
        sutra_lst = []
        sid_set = set()
        #oneSutraFile
        for data in jingmufils :            
            #print (oneSutraFile)            
            #data = xlrd.open_workbook(oneSutraFile)
            table = data.sheets()[0]            
            nrows = table.nrows
            errorlist.append(str(nrows))
            ncols = table.ncols
            tripitaka_id=''#藏只有一次
            print('导入 rows:',table.nrows)

            #解析属性
            for i in range(nrows):
                if i  >0   :
                    #try:      
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
                        if len( Sutra.objects.filter(sid=sid)) >0 :
                            errMsg+='存疑D,经编号重复：'+sid    

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

                    if sid not in sid_set:
                        sid_set.add(sid)
                        sutra = Sutra(sid=sid,lqsutra=lqsutra, name=name,tripitaka=tripitaka,
                        variant_code= variant_code, total_reels=total_reels,
                        remark=remark, code =code)
                        #sutra.save()
                        sutra_lst.append(sutra)
                #except:
                    a=("error: "+str(i+1)+":"+str(values[0])+":"+str(values[1])+":"+str(values[2])+":"+str(values[3])+".errmsg:"+errMsg)                    
                    print(a)
                    errorlist.append(a)
                    # break                       
                    #break
            fl=open(str(nrows)+'.log', 'w')
            for s in errorlist:
                fl.write(s)
                fl.write("\n")
            fl.write('共%d条记录' % (len(errorlist)-1)  )      
            fl.close()   
            print(fl.name)
            errorlist.clear()
        Sutra.objects.bulk_create(sutra_lst)
        return None

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
            #print(a)                                           
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