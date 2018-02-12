import base64
import simplejson as json
import numpy as np
from dotmap import DotMap
from collections import defaultdict


class ArrangeRect(object):

    @classmethod
    def resort_rects_from_list(cls, rects):
        cut_result = list(map(lambda m: ArrangeRect.normalize(m), rects))
        if not cut_result:
            mean_width = 0
        else:
            mean_width = int(np.mean(list(map(lambda X: int(X['w']), cut_result))))
        columns = []
        while cut_result:
            columns.append(cls._pick_one_column(cut_result, mean_width))

        return cls.try_split_yb_bar(columns)

        #return columns

    @classmethod
    def resort_rects_from_qs(cls, queryset, tp):
        cut_result = list(dict(qs) for qs in queryset)
        if not cut_result:
            mean_width = 0
        else:
            mean_width = int(np.mean(list(map(lambda X: int(X['w']), cut_result))))
        columns, m = dict(), 0
        while cut_result:
            m = m + 1
            columns[m] = cls._pick_one_column(cut_result, mean_width)
        return columns

    # 交叠线段,自动截段
    @staticmethod
    def stroke_line(y1, y2, item):
        l1 = item['y1']
        l2 = item['y2']
        #print("l1: %d, l2: %d" % (l1,l2))
        lines = []
        # 包含
        if (y1<= l1 and l2 <= y2):
            lines.append([l1, l2])
        elif (l1<= y1 and y2 <= l2):
            lines.append([y1, y2])
        #交叠1 断线下交叠
        elif ((l1 < y1 and y1<= l2) and l2 <= y2):
            lines.append([y1,l2])
        elif (l1 < y2 and y2 <= l2) and y1 <= l1:
            lines.append([l1, y2])
        #交叠2 断线上交叠
        elif ((y1 < l1 and l1<= y2) and y2 <= l2):
            lines.append([l1,y2])
        elif  ((y1 < l2 and l2<= y2) and l1 <= y1):
            lines.append([l2, y1])
        else:
            return False

        return lines[0]


    @classmethod
    def try_split_yb_bar(cls, columns, tp = "YB"):
        flat_list = [item for sublist in columns for item in sublist]
        mean_height = int(np.mean(list(map(lambda X: int(X['h']), flat_list))))
        min_y = int(np.min(list(map(lambda X: int(X['y']), flat_list))))
        max_y = int(np.max(list(map(lambda X: int(X['h']+X['y']), flat_list))))
        if (len(flat_list) < 50):
            return [max_y, max_y]

        space_y = []
        for idx_col, col in enumerate(columns):
            cols = []
            for idx, chr in enumerate(col):
                try:
                    next_y = col[idx+1]['y']
                except IndexError as e:
                    next_y = max_y
                y_bottom = chr['y'] + chr['h']
                if (next_y - y_bottom) > mean_height*0.3:
                    dist = next_y - y_bottom
                    item = {"idx_col": idx_col, "idx": idx, "y2": next_y, "y1": y_bottom , "dist": dist}
                    cols.append(item)
            space_y.append(cols)

        if tp == "YB":
            if max(map(lambda X:X['dist'] , space_y[len(columns)-1])) > 300:
                columns = columns[0:len(columns)-1]
                space_y = space_y[0:len(columns)-1]
            elif max(map(lambda X:X['dist'] , space_y[0])) > 253:
                columns = columns[1:len(columns)]
                space_y = space_y[1:len(columns)]
            else:
                print("not found")
        check_list =  [item for sublist in space_y for item in sublist]
        lines =[]
        for nn in space_y:
            for n in nn:
                y1 = n['y1']
                y2 = n['y2']
                success_lines = []
                failure_lines = []
                for item in check_list:
                    result = cls.stroke_line(y1, y2, item)
                    if not result :
                        #print("failure: %d , Y: %d,%d"  % (len(failure_lines), y1, y2 ))
                        failure_lines.append(item["idx_col"])
                    else:
                        y1, y2 = result
                        success_lines.append(item["idx_col"])
                print(len(success_lines), len(columns), y1 , y2)
                if len(success_lines)/ len(columns) >= 0.7:
                    if (y1+y2)/2 >700 and   (y1+y2)/2 <900 and (y2-y1) >6:
                        lines.append([y1, y2])
                    elif (y1+y2)/2 >700 and y2> 1100 and y1 < 830:
                        ## 应对下页留白的情况
                        lines.append([y1,y1])

            if lines:
                break
        return lines

    @classmethod
    def _pick_rtop_rectangle(cls, rects, height, width):
        x1 = max(map(lambda Y: int(Y['x']), rects))
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
    def normalize(rect):
        if (rect['w'] < 0):
            rect['x'] = rect['x'] + rect['w']
            rect['w'] = abs(rect['w'])
        if (rect['h'] < 0):
            rect['y'] = rect['y'] + rect['h']
            rect['h'] = abs(rect['h'])

        if (rect['w'] == 0):
            rect['w'] = 1
        if (rect['h'] == 0):
            rect['h'] = 1
        return rect

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

    @staticmethod
    def intersect_with(rect):
        def inner_func(rect2):
            return ArrangeRect._intersects_with(rect, rect2)
        return inner_func

    @staticmethod
    def inside_with(rect):
        def inner_func(rect2):
            return ArrangeRect._inside_with(rect, rect2)
        return inner_func

    @classmethod
    def _pick_one_column(cls, cut_result, mean_width):
        max_height = max(map(lambda Y: int(Y['y']) + int(Y['h']), cut_result))
        mean_width = int(np.mean(list(map(lambda X: int(X['w']), cut_result))))
        _rect = ArrangeRect._pick_rtop_rectangle(cut_result, max_height, mean_width)
        col_rect = ArrangeRect.dequefilter(cut_result, ArrangeRect.intersect_with(_rect))
        if not col_rect:
            col_rect = ArrangeRect.dequefilter(cut_result, ArrangeRect.inside_with(_rect))
            print("Hint: inner case!")
        return sorted(col_rect, key=lambda Y: int(Y['y']))