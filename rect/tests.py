from django.test import TestCase
from rect.models import Schedule, Rect, CCTask, SliceType
from rect.models import Tripitaka, Sutra, Reel, Page, Rect, PageRect
from ccapi.serializer import *
from datetime import date
from django.db import IntegrityError, transaction
from django_bulk_update import helper
from tasks.management.commands import init

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


    def test_bulk_create_rect(self):
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


    def test_bulk_update_rect(self):
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

    def test_make_pagerect_demo(self):
        page = Page.objects.filter(pid='YB000860_001_02_0')
        import pdb;pdb.set_trace()
        page.first().pagerects.first().make_annotate()