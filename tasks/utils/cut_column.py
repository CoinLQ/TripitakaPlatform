from django.conf import settings

import json
from pathlib import Path
from itertools import groupby
from operator import itemgetter
from PIL import Image
from io import BytesIO
import urllib.request
import boto3

def gene_col_data(char_lst):
    '''
    根据每列字块坐标生成列的左上右下顶点坐标
    :param char_lst:
    :return:
    '''
    # 找出w的中位值
    w_lst = [c.get('w', 0) for c in char_lst]
    mid_index = int(len(w_lst) / 2)
    w_mid = w_lst[mid_index]
    xs = []
    ys = []
    for c in char_lst:
        if c.get('w', 0) >= 2 * w_mid: # 如果字框宽度大于2倍w中位值，忽略
            continue
        if 'x' in c:
            xs.append(c['x'])
            if 'w' in c:
                xs.append(c['x'] + c['w'])
        if 'y' in c:
            ys.append(c['y'])
            if 'h' in c:
                ys.append(c['y'] + c['h'])
    min_y = min(ys)
    if min_y > 30:
        min_y -= 30
    if min_y < 0:
        min_y = 0
    max_y = max(ys) + 30
    min_x = min(xs)
    if min_x > 5:
        min_x -= 5
    if min_x < 0:
        min_x = 0
    max_x = max(xs) + 5
    return min_x, min_y, max_x, max_y

def gene_new_col(image_name_prefix, char_lst):
    '''
    根据切分数据生成切列数据
    : image_name_prefix QL_24_111
    '''
    col_ele = tuple(image_name_prefix.split('_'))
    if col_ele[-1].isdigit():
        col_id = ("{}_" * (len(col_ele) - 1) + "c{}0").format(*col_ele)
    else:
        col_id = ("{}_" * (len(col_ele) - 1) + "c{}").foramt(*col_ele)
    col_groups = groupby(char_lst, itemgetter('line_no'))
    col_group_dict = dict([(col, list(col_group)) for col, col_group in col_groups])
    col_data = []
    for col in col_group_dict.keys():
        if col_group_dict[col]:
            x, y, x1, y1 = gene_col_data(col_group_dict[col])
            col_data.append(
                {"col_id": "{}{:02d}".format(col_id, col), "x": x, "y": y, "x1": x1, "y1": y1})
    #print('col_data: ', col_data)
    return col_data

def crop_col_online(img_path, col_data):
    '''
    根据切列数据切图并直接上传到s3
    :param img_path /QL/24/QL_24_111.jpg
    :param col_data:
    :return:
    '''
    if not settings.UPLOAD_COLUMN_IMAGE:
        return
    img_path = img_path.lstrip('/')
    pos = img_path.rfind('/')
    img_prefix = img_path[:pos+1]
    s3c = boto3.client('s3')
    my_bucket = 'lqdzj-image'
    img_url = "https://s3.cn-north-1.amazonaws.com.cn/lqdzj-image/" + img_path
    img = Image.open(BytesIO(urllib.request.urlopen(img_url).read()))
    for col in col_data:
        image = img.crop((col['x'], col['y'], col['x1'], col['y1']))
        buffer = BytesIO()
        image.save(buffer, format="jpeg")
        b = BytesIO(buffer.getvalue())
        key = "{}{}.jpg".format(img_prefix, col['col_id'])
        s3c.upload_fileobj(b, my_bucket, key)

