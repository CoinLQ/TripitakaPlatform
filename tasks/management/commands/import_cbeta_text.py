from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from jwt_auth.models import Staff
from tdata.models import *
from tasks.models import *
from tasks.common import *
from tasks.task_controller import *

import os, sys
from os.path import isfile, join
import traceback

import re, json

CLEAN_PATTERN = re.compile('[「」『』◎　　 \r]')
CLEAN_PATTERN_PUNCT = re.compile('[、？「」◎　　 ，；。：！　]')
def read_reel_info(huayan_cb, reel_no, lines):
    start_vol = 0
    start_vol_page = 0
    end_vol = 0
    end_vol_page = 0
    for line in lines:
        line = line.strip()
        if not line.startswith('T'):
            continue
        pos = line.find('║')
        cbeta_code = line[:pos]
        line_text = line[pos+1:].strip()
        vol = int(cbeta_code[1:3])
        vol_page = int(cbeta_code[10:14])
        if not line_text or line_text.startswith('No'):
            continue
        if not start_vol:
            start_vol = vol
            start_vol_page = vol_page
        if vol > end_vol:
            end_vol = vol
        if vol == end_vol and vol_page > end_vol_page:
            end_vol_page = vol_page

    reel = Reel(sutra=huayan_cb, reel_no=reel_no, start_vol=start_vol,
    start_vol_page=start_vol_page, end_vol=end_vol, end_vol_page=end_vol_page,
    edition_type=Reel.EDITION_TYPE_BASE)
    reel.save()

def process_cbeta_text(huayan_cb, reel_no, lines1, lines2):
    reel = Reel.objects.get(sutra=huayan_cb, reel_no=reel_no)
    results = []
    for line in lines2[1:]:
        if line.find('----------') != -1:
            break
        if line.startswith('No.'):
            continue
        pos = line.find(']')
        if pos != -1:
            line = line[pos+1:]
        line = line.strip()
        line_text = CLEAN_PATTERN.sub('', line)
        if line_text:
            results.append(line_text + '\n')
    sutra_text = ''.join(results)
    punctuation, text = extract_punct(sutra_text)
    text = read_text_info(lines1)
    reelcorrecttext = ReelCorrectText(reel=reel)
    reelcorrecttext.set_text(text)
    reelcorrecttext.save()
    punct = Punct(reel=reel, reeltext=reelcorrecttext, punctuation=json.dumps(punctuation))
    punct.save()

#得到cbeta的卷编号
def read_code_info( path ): 
    filename=path
    with open(filename, 'r', encoding='utf-8') as f:
        lines2 = f.readlines() 
    strRet=''
    for line in lines2:
        line = line.strip()
        if line.startswith('No. '):                        
            strRet= line[4:].strip()            
            nf=strRet.find(' ')
            strRet=strRet[0:nf]
            return strRet

#得到卷信息的同时也要得到文本信息
def read_text_info(lines):
    reeltext = []
    for line in lines:
        line = line.strip()
        if not line.startswith('T'):
            continue
        pos = line.find('║')
        line_text = line[pos+1:].strip()
        if not line_text or line_text.startswith('No') :
            continue
        line_text = line_text.strip()
        line_text = CLEAN_PATTERN_PUNCT.sub('', line_text)
        if line_text:
            reeltext.append( line_text )
    return '\n'.join(reeltext)

#命令行参数参考
#参考：https://docs.djangoproject.com/en/2.0/howto/custom-management-commands/
class Command(BaseCommand):    
    def add_arguments(self, parser):
        parser.add_argument('LQSutra_sid', nargs='+', type=str)#设置一个龙泉id的参数，支持多个

    def handle(self, *args, **options):
        BASE_DIR = settings.BASE_DIR
        sid='LQ003100' #默认值
        CB = Tripitaka.objects.get(code='CB')# 写死，固定是取cbeta的经文        
        for sid in options['LQSutra_sid']:            
            #准备变量                
            #文件名：reel_1/text_1：
            #{tripitaka_id}_{[T/R]}_{Sutra_code}_{index}#T表示经文文件，R表示经目文件
            reelfilename = BASE_DIR+'/data/cbeta/'+sid+'/reel_info' #reel_%s.txt' % reel_no)
            textfilename = BASE_DIR+'/data/cbeta/'+sid+'/text' #text_%s.txt' % reel_no)
            #获得对象
            try:
                lqsutra = LQSutra.objects.get(sid=sid) #需要命令行输入                
            except:
                print('龙泉经目中未查到此编号：'+sid)
                continue

            name=lqsutra.name #'大方廣佛華嚴經'#根据 sid从龙泉经目对象中获得            
            total_reels=lqsutra.total_reels#根据 sid从龙泉经目对象中获得  
            code= '00'+read_code_info(textfilename+'/1.txt') # 文件名固定 code='00278'#从cbeta中读取
            sutra_sid='CB'+code+'0'#TODO 还得考虑格式化固定位数的问题。                                                        
            print('import cbeta text', name, sutra_sid )
            #下面创建经对象        
            try:
                huayan_cb = Sutra.objects.get(sid=sutra_sid)#读取文件
            except:
                huayan_cb = Sutra(sid=sutra_sid, tripitaka=CB, code=code, variant_code='0',
                name=name, lqsutra=lqsutra, total_reels=total_reels)# total_reels 读取龙泉经目信息
                huayan_cb.save()
            Reel.objects.filter(sutra=huayan_cb).delete()

            # #创建经卷和经文对象
            for reel_no in range(1, total_reels+1):
                filename = reelfilename+'/%s.txt' % reel_no
                with open(filename, 'r', encoding='utf-8') as f:
                    lines1 = f.readlines()

                filename = textfilename+'/%s.txt' % reel_no
                text = ''
                with open(filename, 'r', encoding='utf-8') as f:
                    lines2 = f.readlines()

                read_reel_info(huayan_cb, reel_no, lines1)
                process_cbeta_text(huayan_cb, reel_no, lines1, lines2)