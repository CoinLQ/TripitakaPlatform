# -*- coding: UTF-8 -*-

import re
import os
from rect.models import SliceType, PageRect, Rect, Page, TaskStatus, CCTask, \
                 ClassifyTask, PageTask, CharClassifyPlan, DeletionCheckItem, DelTask
import zipfile
import json
from django.db import transaction
from django.db.utils import DataError
from TripitakaPlatform.settings import MEDIA_ROOT
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

import base64
from django.utils.six import BytesIO
from rest_framework.parsers import JSONParser



'''
# 大藏经全名规则-正则描述:
a)	以经为单位组织的藏经按如下规则命名
藏经命名代码_S#####_R###_T####.*
例：高丽藏第1部经第22卷第28页：GLZ_S00001_R022_T0028.jpg
b)	以册为单位组织的藏经按如下规则命名
藏经命名代码_V###_T####.*
例：永乐北藏第1册正文第33页：YLBZ_V001_T0033.png
C）图片名（不含后缀）中不得带有字母、_、数字以外字符
'''
IMG_TYPE_CONFIG = [
    'png',
    'jpg',
    'jpeg'
]
PAGE_URL_SUTRA_RE = r'((?P<series>[A-Z]+)_)?S?(?P<sutra>\d+)_R?(?P<roll>\d+)(_(?P<rollCount>\d+))?_(?P<page>(?P<pageType>[TIPC]?)(?P<pageNum>\d+))\.?(?P<imgType>(?:'+'|'.join(IMG_TYPE_CONFIG).lower()+')?)'
PAGE_URL_VOLUME_RE = r'((?P<series>[A-Z]+)_)?V?(?P<volume>\d+)_(?P<page>(?P<pageType>[TIPC]?)(?P<pageNum>\d+))\.?(?P<imgType>(?:'+'|'.join(IMG_TYPE_CONFIG).lower()+')?)'
pagePatternForSutra = re.compile(PAGE_URL_SUTRA_RE)
pagePatternForVolume = re.compile(PAGE_URL_VOLUME_RE)


def name_to_imgPath(name):
    if name :
        m = pagePatternForSutra.match(name)
        if m : return m.groupdict()
        m = pagePatternForVolume.match(name)
        if m : return m.groupdict()
    return None

def imgPath_to_name(ipo):
    if ipo:
        get = lambda key, prefix='': prefix+ipo[key] if key in ipo and ipo[key] else ''
        name = get('series')
        name += get('volume', '_V') + get('sutra', '_S') + get('roll', '_V')
        name += '_'+ipo['page']
        name += '.'+ipo['imgType'] if 'imgType' in ipo else ''
        return name

def exist_img_on_s3(img, series=''):
    imgPathObj = name_to_imgPath(img)
    if series: imgPathObj['series'] = series
    return imgPathObj and is_img_exist(imgPath_to_name(imgPathObj))

def parseBatch(batch):
    parser = HuaNanBatchParser(batch=batch)



class BatchParser(object):

    def __init__(self, batch):
        self.batch = batch
        self.notFundImgList = []

    def parse(self, ):
        pass

    def parsePage(self, data):
        pass

    def savePageRect(self, pageRect):
        #return PageRect.objects.create(pageRect)
        return pageRect.save()

    @transaction.atomic
    def saveRectSet(self, rectModelList, pageRect=None, bulk=True):
        pageRect.save()
        for rect in rectModelList:
            rect.page_rect = pageRect
            rect.batch = self.batch
            if not bulk: Rect.objects.create(rect)
        if bulk:
            try:
                return Rect.objects.bulk_create(rectModelList)
            except DataError as err:
                print(err)

    def parsePageCode(self, pageName):
        pass


    def repair0(self, val, maxLength):
        if val and len(val) < maxLength:
            val = '0' * (maxLength - len(val)) + val
        return val


class HuaNanBatchParser(BatchParser):
    linePattern = re.compile(r'(?P<pageImg>\w+\.jpg) (?P<rectData>.+)\!(?P<txtData>.+)')
    separate = re.compile(';')
    rectPattern = re.compile(r'(?P<x>\d+),(?P<y>\d+),(?P<w>\d+),(?P<h>\d+),(?P<cc>[0-9]+\.[0-9]+)')
    wordPattern = re.compile(r'(?P<word>[\x80-\xff]+)')
    # 0001_001_26_01.jpg => GLZ_S00001_R001_T0001
    pageCodePattern = re.compile(r'''
        (?P<series>[A-Z]+_)?    #藏经版本编号
        (?P<sutra>\d{1,5})      #经编号
        _
        (?P<roll>\d{1,3})       #卷编号
        _
        ((?P<pageCountInRoll>\d{1,4})_)?    #每一卷页的数量
        (?P<page>\d{1,4})       #页编号
        (\.(?P<pageImgType>\w{1,6}))?   #图片类型
        ''', re.VERBOSE)

    def parse(self):
        upload_file = self.batch.upload
        upload_file_path = os.path.join(MEDIA_ROOT, upload_file.name)
        zfile = zipfile.ZipFile(upload_file_path, 'r')
        # TODO 要和用户约定上传文件格式
        for file in zfile.namelist():
            if file.endswith('.txt'):
                with zfile.open(file, 'r') as f:
                    for line in f.readlines():
                        try:
                            self.parsePage(str(line, encoding='utf-8'))
                        except UnicodeDecodeError as error:
                            print(error) #todo log记录未解析的页数据.

    def parsePageCode(self, pageName):
        cm = self.pageCodePattern.match(pageName)
        if cm:
            series = cm.group('series') if cm.group('series') else self.batch.series
            sutra = 'S' + self.repair0(cm.group('sutra'), 5)
            roll = 'R' + self.repair0(cm.group('roll'), 3)
            page = 'T' + self.repair0(cm.group('page'), 4)
            return series + '_' + sutra + '_' + roll + '_' + page
        return ""

    def parsePage(self, data):
        lineMatcher = self.linePattern.match(data)
        if lineMatcher:
            img = lineMatcher.group('pageImg')
            pageCode = self.parsePageCode(img)
            # if not pageCode or not is_img_exist(pageCode):
            #     self.notFundImgList.append(img)
            #     return []

            rectData = lineMatcher.group('rectData')
            txtData = lineMatcher.group('txtData')

            rectColumnArr = self.separate.split(rectData)
            txtColumnArr = self.separate.split(txtData)
            #maxColumnCount = max(len(rectColumnArr), len(txtColumnArr))
            columnNum = 0
            maxLineCount = 0
            pageRectSetList = []
            pageRectModelList = []
            for i in range(len(rectColumnArr)): #以切块数据列数为准.
                rectIter = self.rectPattern.finditer(rectColumnArr[columnNum])
                txtColumn = txtColumnArr[columnNum]
                columnNum += 1 #按人类习惯列号以1为开始
                lineNum = 0
                if rectIter:
                    for rect in rectIter:
                        rectDict = rect.groupdict()
                        word = txtColumn[lineNum]
                        if word: rectDict['ch'] = word
                        lineNum += 1 #按人类习惯用法行号以1为开始.
                        maxLineCount = max(lineNum, maxLineCount)
                        rectDict['char_no'] = lineNum
                        rectDict['line_no'] = len(rectColumnArr) - columnNum + 1
                        rectDict['w'] = (int(rectDict['w']) - int(rectDict['x']))/2
                        rectDict['x'] = rectDict['x']/2
                        rectDict['h'] = int(rectDict['h']) - int(rectDict['y'])
                        rectDict['pcode'] = pageCode # pageCode用于字块找出字图和字列图
                        pageRectSetList.append(rectDict)
                        model = Rect.generate(rectDict)
                        if model: pageRectModelList.append(model)

            pageRect = PageRect()
            pageRect.batch = self.batch
            # try:
            #     pageRect.page = Page.objects.get(code=imgPath)
            # except ObjectDoesNotExist:
            #     pass
            pageRect.code = pageCode
            pageRect.column_count = columnNum
            pageRect.line_count = maxLineCount
            pageRect.rect_set = json.dumps(pageRectSetList, ensure_ascii=False)
            # self.savePageRect(pageRect)

            # 批量保存每一列的Rect数据
            self.saveRectSet(pageRectModelList, pageRect)
            return pageRectSetList
        return []
