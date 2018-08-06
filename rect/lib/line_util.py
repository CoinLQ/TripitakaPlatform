import numpy as np
from dotmap import DotMap

class Line(object):
    @classmethod
    def _pick_rtop_rectangle(cls, rects, height, width):
        x1 = max(map(lambda Y: Y['x'], rects))
        return {'x': x1, 'y': 0, 'w': width, 'h': height}

    @staticmethod
    def _intersects_with(_rect1, _rect2):
        rect1, rect2 = DotMap(_rect1), DotMap(_rect2)
        if (rect2.x < rect1.x + int(rect1.w) and rect1.x < rect2.x + int(rect2.w) and
            rect2.y <= rect1.y + int(rect1.h)):
            return rect1.y <= rect2.y + int(rect2.h)
        else:
            return False

    @staticmethod
    def _inside_with(_large_rect, _rect2):
        _large_rect, rect2 = DotMap(_large_rect), DotMap(_rect2)
        if (_large_rect.x <= rect2.x) and (_large_rect.x + _large_rect.w >= rect2.x + rect2.w) and \
                (_large_rect.y <= rect2.y) and (_large_rect.y + _large_rect.h >= rect2.y + rect2.h):
                return True
        else:
                return False


    @staticmethod
    def _equal_with(_large_rect, _rect2):
        _large_rect, rect2 = DotMap(_large_rect), DotMap(_rect2)
        if (_large_rect.x == rect2.x):
                return True
        else:
                return False

    @staticmethod
    def dequefilter(_rects, condition):
        _col_rect = list()
        for _ in range(len(_rects)):
            item = _rects.pop()
            if not condition(item):
                _rects.insert(0, item)
            else:
                _col_rect.append(item)
        return _col_rect

    @classmethod
    def intersect_with(cls, rect):
        def inner_func(rect2):
            return cls._intersects_with(rect, rect2)
        return inner_func

    @classmethod
    def inside_with(cls, rect):
        def inner_func(rect2):
            return cls._inside_with(rect, rect2)
        return inner_func

    @classmethod
    def equal_with(cls, rect):
        def inner_func(rect2):
            return cls._equal_with(rect, rect2)
        return inner_func

    @classmethod
    def _pick_one_column(cls, cut_result):
        max_height = max(map(lambda Y: Y['y'] + Y['h'], cut_result))
        mean_width = int(np.mean(list(map(lambda X: int(X['w']), cut_result))))
        _rect = cls._pick_rtop_rectangle(cut_result, max_height, mean_width)
        col_rect = cls.dequefilter(cut_result, cls.intersect_with(_rect))
        if not col_rect:
            col_rect = cls.dequefilter(cut_result, cls.inside_with(_rect))
            if not col_rect:
                col_rect = cls.dequefilter(cut_result, cls.equal_with(_rect))
            print("Hint: inner case!")
        return sorted(col_rect, key=lambda Y: int(Y['y']))