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
    # sid		name			total_reels	author	
    #LQ000010	佛說長阿含經	22	姚秦佛陀耶舍共竺佛念譯	
    def ImportLQSutra(self):       
        BASE_DIR = settings.BASE_DIR
        lqsutra_lst = []
        filename = os.path.join(BASE_DIR, 'data/sutra_list/%s' % 'lqsutra_list.txt')
        exist_sids = set([lqsutra.sid for lqsutra in LQSutra.objects.all()])
        sid_set = set()
        lqreels_lst = []
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                if  line.startswith('#') :
                    continue

                line = line.rstrip('\n')
                sid, name, total_reels_str, author = line.split('\t')                                                                             
                variant_code = sid[len(sid)-1:] 
                try:
                    total_reels = int(total_reels_str) 
                except:                    
                    total_reels = 0
                if sid in exist_sids or sid in sid_set:
                    continue
                sid_set.add(sid)                        
                lqsutra = LQSutra(sid=sid, variant_code=variant_code, name=name, author=author, 
                total_reels = total_reels, remark='')
                lqsutra_lst.append(lqsutra)
                lqreels = []
                for reel_no in range(1, total_reels+1):
                    lqreel = LQReel(reel_no=reel_no)
                    lqreels.append(lqreel)
                lqreels_lst.append(lqreels)
            LQSutra.objects.bulk_create(lqsutra_lst)
            all_lqreels = []
            for i in range(len(lqsutra_lst)):
                for lqreel in lqreels_lst[i]:
                    lqreel.lqsutra = lqsutra_lst[i]
                    all_lqreels.append(lqreel)
            LQReel.objects.bulk_create(all_lqreels)

    #FUNC_2 ImportSutra 导入其他大藏经的经目 sutra_list.txt
    #sid		tripitaka	name			lqsutra	total_r	remark	
    #LQ000010	佛說長阿含經	22	姚秦佛陀耶舍共竺佛念譯	
    def ImportSutra(self):       
        BASE_DIR = settings.BASE_DIR

        mylist = []
        filename = os.path.join(BASE_DIR, 'data/sutra_list/%s' % 'sutra_list.txt')
        exist_sids = set([sutra.sid for sutra in Sutra.objects.all()])
        sid_set = set()
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                if  line.startswith('#') :
                    continue

                line = line.rstrip('\n')
                sid, tripitaka_code, name, lqsutra_sid, total_reels_str, remark= line.split('\t')                                                                             
                scode=sid[2:7]#code 
                try :
                    lqsutra = LQSutra.objects.get(sid=lqsutra_sid) 
                except:
                    print('lqsutra %s not exist: ' % lqsutra_sid, line)
                    continue

                try :
                    tripitaka = Tripitaka.objects.get(code=tripitaka_code) 
                except:
                    pass
                variant_code = sid[len(sid)-1:]  
                try:
                    total_reels = int(total_reels_str) 
                except:                    
                    total_reels = 0
                
                if sid in exist_sids or sid in sid_set:
                    continue 
                sid_set.add(sid)                                          
                sutra = Sutra(sid=sid, lqsutra=lqsutra, name=name, tripitaka=tripitaka,
                    variant_code=variant_code, total_reels=total_reels,
                    remark=remark, code=scode)
                mylist.append(sutra)
            Sutra.objects.bulk_create(mylist)

    #FUNC_3 ImportSutraReel 导入其他大藏经的详目 reel_list.txt
    #sid	name    reel_no	start_vol	start_vol_page	end_vol	end_vol_page	remark	
    #GL000010	大般若波羅蜜多經	0	1	1	1	2	序
    def ImportReel(self):       
        BASE_DIR = settings.BASE_DIR

        mylist = []
        filename = os.path.join(BASE_DIR, 'data/sutra_list/%s' % 'reel_list.txt')
        reel_str_set = set()
        exist_reels = set(['%s%03d' % (reel.sutra.sid, reel.reel_no) for reel in Reel.objects.all()])
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
                    end_vol = end_vol
                except:
                    start_vol = 0
                    end_vol = 0
                try:
                    start_vol_page = int(start_vol_page)
                    end_vol_page = int(end_vol_page)
                except:
                    start_vol_page = 0
                    end_vol_page = 0
                try:
                    sutra = Sutra.objects.get(sid=sid)
                except:
                    print('no sutra: ', line)
                    continue

                reel_str = '%s%03d' % (sid, reel_no)
                if reel_str in exist_reels or reel_str in reel_str_set:
                    continue
                reel_str_set.add(reel_str)                    
                reel = Reel(sutra=sutra, reel_no=reel_no, start_vol=start_vol, start_vol_page=start_vol_page,
                end_vol=end_vol, end_vol_page=end_vol_page,remark=remark )

                if sutra.tripitaka.code in tcode_lst1 and reel.start_vol > 0:
                    reel.path1 = str(reel.start_vol)
                elif sutra.tripitaka.code in tcode_lst2:
                    reel.path1 = str(int(sid[2:7]))
                    reel.path2 = str(reel.reel_no)
                mylist.append(reel)
            Reel.objects.bulk_create(mylist)
