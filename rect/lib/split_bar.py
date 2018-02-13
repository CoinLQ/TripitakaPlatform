import numpy as np

class SplitBar(object):
    @classmethod
    def bared_columns(cls, columns, tp):
        bar_lines = cls.bar_line_array(columns, tp)
        origin_length = len([item for sublist in columns for item in sublist])
        ## 没有分栏,直接用线性排列
        print(len(columns))
        print("*****************")
        if not bar_lines:
            return columns
        else:
            new_columns = []
            for bl in sorted(bar_lines):
                for idx, column in enumerate(columns):
                    chs = list(filter(lambda X: X['y'] < bl, column))
                    columns[idx] = list(filter(lambda X: X['y'] >= bl, column))
                    new_columns.append(chs)
            ## 栏线上的处理完, 把余下的入列位
            for column in columns:
                new_columns.append(column)
        if origin_length != len([item for sublist in new_columns for item in sublist]):
            raise 'sddddds'
        return new_columns

    @classmethod
    def bar_line_array(cls, columns, tp):
        if (tp in ['SX', 'PL', 'GL', 'LC', 'JX']):
            return []
        if (tp == "YB"):
            return cls.yb_mode_split_bar(columns)
        elif (tp =="QL"):
            return cls.ql_mode_split_bar(columns)
        elif (tp =="ZH"):
            return cls.zh_mode_split_bar(columns)
        else:
            return []

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
    def yb_mode_split_bar(cls, columns, tp = "YB"):
        flat_list = [item for sublist in columns for item in sublist]
        mean_height = int(np.mean(list(map(lambda X: int(X['h']), flat_list))))
        min_y = int(np.min(list(map(lambda X: int(X['y']), flat_list))))
        max_y = int(np.max(list(map(lambda X: int(X['h']+X['y']), flat_list))))
        ## 大面积空白页, 不存在分栏,直接返回最下线框区的最下线
        if (len(flat_list) < 50):
            return []

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
                    if not result:
                        #print("failure: %d , Y: %d,%d"  % (len(failure_lines), y1, y2 ))
                        failure_lines.append(item["idx_col"])
                    else:
                        y1, y2 = result
                        success_lines.append(item["idx_col"])
                #print(len(success_lines), len(columns), y1 , y2)
                if len(success_lines)/ len(columns) >= 0.7:
                    if (y1+y2)/2 >730 and   (y1+y2)/2 <900 and (y2-y1) >6:
                        lines.append([y1, y2])
                    elif (y1+y2)/2 >700 and y2> 1100 and y1 < 830:
                        ## 应对下页留白的情况
                        lines.append([y1,y1])

            if lines:
                break
        if not lines and len(flat_list)> 20:
            return [820]
        return [(line[0] +line[1])/2 for line in lines]



    @classmethod
    def ql_mode_split_bar(cls, columns):
        flat_list = [item for sublist in columns for item in sublist]
        mean_height = int(np.mean(list(map(lambda X: int(X['h']), flat_list))))
        max_line_char = max(map(lambda X: len(X), columns))
        min_y = int(np.min(list(map(lambda X: int(X['y']), flat_list))))
        max_y = int(np.max(list(map(lambda X: int(X['h']+X['y']), flat_list))))
        ## 大面积空白页, 不存在分栏,直接返回最下线框区的最下线
        if (len(flat_list) < 50):
            return []

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
                    if not result:
                        failure_lines.append(item["idx_col"])
                    else:
                        y1, y2 = result
                        success_lines.append(item["idx_col"])
                #print(len(success_lines), len(columns), y1 , y2)
                if len(success_lines)/ len(columns) >= 0.7:
                    if (y1+y2)/2 >730 and   (y1+y2)/2 <900 and (y2-y1) >6:
                        lines.append([y1, y2])
                    elif (y1+y2)/2 >700 and y2> 1100 and y1 < 830:
                        ## 应对下页留白的情况
                        lines.append([y1,y1])
            if lines:
                break
        if not lines and len(flat_list)> 20:
            return [780]
        return [(line[0] +line[1])/2 for line in lines]



    # TODO: 中华大藏经 三栏分布未完成
    @classmethod
    def zh_mode_split_bar(cls, columns):
        flat_list = [item for sublist in columns for item in sublist]
        mean_height = int(np.mean(list(map(lambda X: int(X['h']), flat_list))))
        max_line_char = max(map(lambda X: len(X), columns))
        min_y = int(np.min(list(map(lambda X: int(X['y']), flat_list))))
        max_y = int(np.max(list(map(lambda X: int(X['h']+X['y']), flat_list))))
        ## 大面积空白页, 不存在分栏,直接返回最下线框区的最下线
        if (len(flat_list) < 50):
            return [max_y]

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
                    if not result:
                        failure_lines.append(item["idx_col"])
                    else:
                        y1, y2 = result
                        success_lines.append(item["idx_col"])
                print(len(success_lines), len(columns), y1 , y2)
                if len(success_lines)/ len(columns) >= 0.7:
                    if (y1+y2)/2 >730 and   (y1+y2)/2 <900 and (y2-y1) >6:
                        lines.append([y1, y2])
                    elif (y1+y2)/2 >700 and y2> 1100 and y1 < 830:
                        ## 应对下页留白的情况
                        lines.append([y1,y1])
            if lines:
                break
        if not lines and len(flat_list)> 20:
            return [780]
        return [(line[0] +line[1])/2 for line in lines]