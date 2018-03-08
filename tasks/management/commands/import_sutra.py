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

class Command(BaseCommand):
    def handle(self, *args, **options):
        #call 龙泉经 ImportLQSutra
        
        self.ImportLQSutra()

        #call 其他大藏经 ImportSutra
        self.ImportSutra()


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

                sid,stripitak, sname , slqsutra , stotal_reels,  sremark= line.split('\t',5)                                                                             
                scode=sid[2:7]#code 
                try :
                    lqsutra=LQSutra.objects.get(sid=slqsutra) 
                except:
                    pass

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