from dotmap import DotMap
from .line_util import Line
from .split_bar import SplitBar

class ArrangeRect(object):

    @classmethod
    def resort_rects_from_josndata(cls, cut_info):
        rects = cut_info['char_data']
        tp = cut_info['img_code'][0:2]
        columns = cls.resort_rects_from_rectset(rects)
        # cut_result = list(map(lambda m: ArrangeRect.normalize(m), rects))
        # columns = []
        # while cut_result:
        #     columns.append(Line._pick_one_column(cut_result))

        #return SplitBar.bar_line_array(columns, tp)
        return SplitBar.bared_columns(columns, tp)
        #return columns

    @classmethod
    def resort_rects_from_rectset(cls, rect_set):
        cut_result = list(map(lambda m: ArrangeRect.normalize(dict(m)), rect_set))
        columns = []
        while cut_result:
            columns.append(Line._pick_one_column(cut_result))
        return columns

    @classmethod
    def resort_rects_from_qs(cls, rects, tp):
        columns = cls.resort_rects_from_rectset(rects)
        return SplitBar.bared_columns(columns, tp)

    @staticmethod
    def _normalize(r):
        if (r.w < 0):
            r.x = r.x + r.w
            r.w = abs(r.w)
        if (r.h < 0):
            r.y = r.y + r.h
            r.h = abs(r.h)

        if (r.w == 0):
            r.w = 1
        if (r.h == 0):
            r.h = 1
        return r

    @staticmethod
    def normalize(r):
        if isinstance(r, dict):
            r = DotMap(r)
        r = ArrangeRect._normalize(r)
        if isinstance(r, DotMap):
            r = r.toDict()
        return r

