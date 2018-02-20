from django.test import TestCase
from rect.models import Schedule, Rect, CCTask, SliceType
from rect.models import Tripitaka, Sutra, Reel, Page, Rect, PageRect
from ccapi.serializer import *
from datetime import date
from django.conf import settings
from django.db import IntegrityError, transaction
from django_bulk_update import helper
from tasks.management.commands import init
from rect.lib.arrange_rect import ArrangeRect
from dotmap import DotMap
from PIL import Image, ImageFont, ImageDraw
import os, sys
import json
from io import BytesIO
import urllib.request

class BaseModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        with open('data/tripitaka_list.txt', 'r') as f:
            for line in f.readlines():
                code, name, shortname = line.rstrip().split()
                tripitaka = Tripitaka(code=code, name=name, shortname=shortname)
                tripitaka.save()
        init.Command().handle()
        cls.prepare_gl()
        cls.prepare_yb()

    @classmethod
    def prepare_yb(cls):
        pass

    @classmethod
    def prepare_gl(cls):
        pass


    def _test_bulk_create_rect(self):
        count = Rect.objects.count()
        rects =  [{
            "w": 34,
            "line_no": 5,
            "ch": "德",
            "wcc": 0.999976,
            "op": 3,
            "cc": 0.999976,
            "x": 944,
            "ts": "",
            "char_no": 9,
            "h": 28,
            "y": 372,
            "column_set": {
                "x1": 987,
                "y1": 780,
                "y": 0,
                "col_id": "YB_27_c1014",
                "x": 936
            },
            "cid": "YB000860_001_01_0_12_22",
            "page_pid": "YB000860_001_01_0",
            "reel_id": "1"
        },
        {
            "w": 34,
            "line_no": 8,
            "ch": "衆",
            "wcc": 0.999971,
            "op": 3,
            "cc": 0.999971,
            "x": 796,
            "ts": "",
            "char_no": 3,
            "h": 30,
            "y": 176,
            "column_set": {
                "x1": 842,
                "y1": 780,
                "y": 0,
                "col_id": "YB_27_c1014",
                "x": 792
            },
            "cid": "YB000860_001_01_0_12_23",
            "page_pid": "YB000860_001_01_0",
            "reel_id": "1"
        }]
        Rect.bulk_insert_or_replace(rects)
        self.assertEquals(Rect.objects.count(), count+2)


    def _test_bulk_update_rect(self):
        total = Rect.objects.count()
        rects = [rect.serialize_set for rect in Rect.objects.all().order_by('-id')[:100]]
        for r in rects[:10]:
            r['id'] = None
        for r in rects:
            r['x']=10000
        rectset = RectWriterSerializer(data=rects, many=True)
        rectset.is_valid()
        Rect.bulk_insert_or_replace(rectset.data)
        all_changed = Rect.objects.filter(x=10000).count()
        self.assertEquals(100, all_changed)
        print(all_changed)
        self.assertEquals(Rect.objects.count(), total+10)

    def test_reformat_page(self):
        page_pid = 'YB000860_001_02_0'
        count = Rect.objects.count()
        # print(Rect.objects.filter(page_pid=page_pid).values_list('cid', flat=True))
        PageRect.reformat_rects('YB000860_001_02_0')
        # print(Rect.objects.filter(page_pid=page_pid).values_list('cid', flat=True))
        self.assertEquals(Rect.objects.count(), count)

    def test_rebuild_page(self):
        count = len(PageRect.objects.first().rect_set)
        page_rect = PageRect.objects.first()
        page_rect.rebuild_rect()
        # print(Rect.objects.values_list('cid', flat=True))
        # print(Rect.objects.first().__dict__)
        self.assertEquals(len(PageRect.objects.first().rect_set), count)

    def _test_make_pagerect_demo(self):
        page = Page.objects.filter(pid='YB000860_001_02_0')
        page.first().pagerects.first().make_annotate()

    def _test_pagerect_align(self):
        data_path = "%s/rect/test_data/" % settings.BASE_DIR
        # for n in range(1, 100):
        #     page_cut = "YB_27_%d.cut" % n
        # for n in range(1, 50):
        #     page_cut = "QL_24_%d.cut" % n
        # for n in range(59, 100):
        #     page_cut = "ZH_12_%d.cut" % n
        for n in range(59, 100):
            page_cut = "ZH_12_%d.cut" % n
            print(page_cut)
            cut_file = data_path + page_cut
            try:
                cut_info = json.loads(open(cut_file, 'r').read())
            except:
                continue
            print(ArrangeRect.resort_rects_from_josndata(cut_info))


    def _test_build_reformated_rects_image(self):
        for n in range(1, 100):
            s3_id = "QS_22_%d" % n
            self.make_annotate_by_s3id(s3_id)

    def _remote_image_stream(self, s3_id):
        img_filename = "%s/rect/test_data/%s.jpg" % (settings.BASE_DIR, s3_id)
        if os.path.exists(img_filename):
           return Image.open(img_filename)
        try:
            s3_uri = 'https://s3.cn-north-1.amazonaws.com.cn/lqdzj-image/%s/%s.jpg' % (os.path.dirname(s3_id.replace('_', '/')), s3_id)
            print(s3_uri)
            opener = urllib.request.build_opener()
            reader = opener.open(s3_uri)
        except:
            return ''
        data = reader.read()
        open(img_filename, 'wb').write(data)
        return Image.open(img_filename)

    def _remote_data_stream(self, s3_id):
        cut_filename = "%s/rect/test_data/%s.cut" % (settings.BASE_DIR, s3_id)
        if os.path.exists(cut_filename):
            with open(cut_filename, 'r') as f:
                return f.read()
        try:
            s3_uri = 'https://s3.cn-north-1.amazonaws.com.cn/lqdzj-image/%s/%s.cut' % (os.path.dirname(s3_id.replace('_', '/')), s3_id)
            opener = urllib.request.build_opener()
            reader = opener.open(s3_uri)
        except:
            return ''
        data = reader.read()
        open(cut_filename, 'wb').write(data)
        return data

    def make_annotate_by_s3id(self, s3_id):
        image_file = self._remote_image_stream(s3_id)
        source_img = image_file.convert("RGBA")
        cutfile = self._remote_data_stream(s3_id)
        cut_info = json.loads(cutfile)

        work_dir = "/tmp/annotations"
        try:
            os.stat(work_dir)
        except:
            os.makedirs(work_dir)
        out_file = "%s/%s_marked.jpg" % (work_dir, s3_id)
        # make a blank image for the rectangle, initialized to a completely transparent color
        tmp = Image.new('RGBA', source_img.size, (0, 0, 0, 0))
        # get a drawing context for it
        draw = ImageDraw.Draw(tmp)
        myfont = ImageFont.truetype("/Library/Fonts/Songti.ttc", 22)
        columns = ArrangeRect.resort_rects_from_josndata(cut_info)
        for lin_n, line in enumerate(columns, start=1):
            for col_n, _r in enumerate(line, start=1):
                rect = DotMap(_r)
                # draw a semi-transparent rect on the temporary image
                draw.rectangle(((rect.x, rect.y), (rect.x + int(rect.w), rect.y + int(rect.h))),
                                 fill=(255, 255, 255, 120))
                anno_str = u"%s-%s" % (lin_n, col_n)
                draw.text((rect.x, rect.y), anno_str, font=myfont, fill=(255, 0, 120))
        source_img = Image.alpha_composite(source_img, tmp)
        source_img.save(out_file, "JPEG")