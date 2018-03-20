from django.core.management.base import BaseCommand, CommandError
from django.contrib import auth
from jwt_auth.models import Staff
from tdata.models import *
from tasks.models import *
from tasks.common import *
from tasks.task_controller import create_tasks_for_batchtask

import TripitakaPlatform.settings

import os, sys
from os.path import isfile, join
import traceback

import re, json

tcode_lst1 = ['PL', 'SX', 'YB', 'QL', 'ZH', 'QS', 'ZC']
tcode_lst2 = ['GL', 'LC']

class Command(BaseCommand):
    def handle(self, *args, **options):
        # 龙泉藏经
        self.ImportLQSutra()
        # 实体藏经
        self.ImportSutra()
        self.ImportReel()


    #FUNC_1 ImportLQSutra 创建龙泉藏经 龙泉经目 lqsutra_list.txt
    #sid		name			total_reels	author	remark	
    #LQ000010	佛說長阿含經	22	姚秦佛陀耶舍共竺佛念譯	
    def ImportLQSutra(self):       
        BASE_DIR = settings.BASE_DIR
        #LQSutra.objects.all().delete()
        mylist = []
        filename = os.path.join(BASE_DIR, 'data/sutra_list/%s' % 'lqsutra_list.txt')
        sid_set = set()
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                if  line.startswith('#') :
                    continue

                line = line.replace('\n','')

                sid, sname, total_reels, sauthor, remark= line.split('\t',4)                                                                             
                variant_code = sid[len(sid)-1:] 
                #print (sid+'\t'+variant_code+'\t'+sname+'\t'+total_reels+'\t'+sauthor+'\t'+remark)
                try:
                    ntotal_reels = int(total_reels) 
                except:                    
                    ntotal_reels = 0
                
                try:
                    lqsutra = LQSutra.objects.get(sid=sid)
                except:
                    if sid not in sid_set:
                        sid_set.add(sid)                        
                        lqsutra = LQSutra(sid=sid, variant_code=variant_code,name=sname,author=sauthor, 
                        total_reels=ntotal_reels,remark='' )
                        mylist.append(lqsutra)
            LQSutra.objects.bulk_create(mylist)


    #FUNC_2 ImportSutra 导入其他大藏经的经目 sutra_list.txt
    #sid		tripitaka	name			lqsutra	total_r	remark	
    #LQ000010	佛說長阿含經	22	姚秦佛陀耶舍共竺佛念譯	
    def ImportSutra(self):       
        BASE_DIR = settings.BASE_DIR
        #Sutra.objects.all().delete()

        mylist = []
        filename = os.path.join(BASE_DIR, 'data/sutra_list/%s' % 'sutra_list.txt')
        sid_set = set()
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                if  line.startswith('#') :
                    continue

                line = line.replace('\n','')
                sid, stripitak, sname, slqsutra, stotal_reels, sremark= line.split('\t',5)                                                                             
                scode=sid[2:7]#code 
                try :
                    lqsutra=LQSutra.objects.get(sid=slqsutra) 
                except:
                    print('lqsutra %s not exist: ' % slqsutra, line)
                    continue

                try :
                    tripitaka=Tripitaka.objects.get(code=stripitak) 
                except:
                    pass
                variant_code = sid[len(sid)-1:]  
                #print (sid+'\t'+variant_code+'\t'+sname+'\t'+total_reels+'\t'+sauthor+'\t'+remark)
                try:
                    ntotal_reels = int(stotal_reels) 
                except:                    
                    ntotal_reels = 0
                
                try:
                    sutra = Sutra.objects.get(sid=sid)
                except:  
                    if sid not in sid_set:
                        sid_set.add(sid)                                          
                        sutra = Sutra(sid=sid,lqsutra=lqsutra, name=sname,tripitaka=tripitaka,
                            variant_code= variant_code, total_reels=ntotal_reels,
                            remark=sremark, code =scode)
                        mylist.append(sutra)
            Sutra.objects.bulk_create(mylist)

    #FUNC_3 ImportSutraReel 导入其他大藏经的详目 reel_list.txt
    #sid	name    reel_no	start_vol	start_vol_page	end_vol	end_vol_page	remark	
    #GL000010	大般若波羅蜜多經	0	1	1	1	2	序
    def ImportReel(self):       
        BASE_DIR = settings.BASE_DIR
        #Reel.objects.all().delete()

        mylist = []
        filename = os.path.join(BASE_DIR, 'data/sutra_list/%s' % 'reel_list.txt')
        sid_set = set()
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                if  line.startswith('#') :
                    continue

                line = line.replace('\n','')
                sid, sname , reel_no , start_vol,  start_vol_page, end_vol, end_vol_page, remark = line.split('\t',7) 
                #-----------------------------------------------------------------------------------------------
                #sid, name, reel_no, start_vol, start_vol_page, end_vol_page = line.split('\t')
                sid=sid.strip()
                reel_no=reel_no.strip()
                key=sid +reel_no 
                tcode = sid[:2]
                reel_no = int(reel_no)
                try:
                    start_vol = int(start_vol)
                    start_vol_page = int(start_vol_page)
                    end_vol = end_vol
                    end_vol_page = int(end_vol_page)
                except:
                    start_vol = 0
                    end_vol = 0
                    start_vol_page = 0
                    end_vol_page = 0
                try:
                    sutra = Sutra.objects.get(sid=sid)
                except:
                    tripitaka = Tripitaka.objects.get(code=sid[:2])
                    sutra = Sutra(sid=sid, tripitaka=tripitaka, code=sid[2:7], \
                    variant_code=sid[7], name=sname, lqsutra=None, total_reels=0)
                    sutra.save()

                #print(sutra.sid)
                try:
                    reel = Reel.objects.get(sutra=sutra, reel_no=reel_no)
                    #print("find")
                except:
                    if key not in sid_set:
                        sid_set.add(key)                    
                        reel = Reel(sutra=sutra, reel_no=reel_no, start_vol=start_vol, start_vol_page=start_vol_page,
                        end_vol=end_vol, end_vol_page=end_vol_page,remark=remark )

                        if sutra.tripitaka.code in tcode_lst1 and reel.start_vol > 0:
                            reel.path1 = str(reel.start_vol)
                        elif sutra.tripitaka.code in tcode_lst2:
                            reel.path1 = str(int(sid[2:7]))
                            reel.path2 = str(reel.reel_no)
                        mylist.append(reel)
            Reel.objects.bulk_create(mylist)                                                                            
                ##------时间测试记录------------------------------
                # 【excel】：        1m44.248s ,    
                # ImportLQSutra :   0m3.596s
                # ImportSutra:      0m30.101s
                # ImportReel :      0m48.365s

                # 【txt】:real       3m12.421s ,    
                # ImportLQSutra :   0m9.464s
                # ImportSutra:      1m2.232s
                # ImportReel :      2m22.282s

                # 【exceltotxt】:real    real    0m31.926s
