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
    xs = []
    ys = []
    for c in char_lst:
        if 'x' in c:
            xs.append(c['x'])
            if 'w' in c:
                xs.append(c['x'] + c['w'])
        if 'y' in c:
            ys.append(c['y'])
            if 'h' in c:
                ys.append(c['y'] + c['h'])
    min_y = min(ys)
    if min_y > 10:
        min_y -= 10
    max_y = max(ys) + 10
    return min(xs), min_y, max(xs), max_y

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
    img_path = img_path.lstrip('/')
    pos = img_path.rfind('/')
    img_prefix = img_path[:pos+1]
    s3c = boto3.client('s3')
    my_bucket = 'lqdzj-image'
    img_url = "https://s3.cn-north-1.amazonaws.com.cn/lqdzj-image/" + img_path
    img = Image.open(BytesIO(urllib.request.urlopen(img_url).read()))
    col_img_dict = {
        "whole": img_url,
        "crops": []
    }
    for col in col_data:
        image = img.crop((col['x'], col['y'], col['x1'], col['y1']))
        buffer = BytesIO()
        image.save(buffer, format="jpeg")
        b = BytesIO(buffer.getvalue())
        key = "{}{}.jpg".format(img_prefix, col['col_id'])
        #s3c.upload_fileobj(b, my_bucket, key)
        #savefile = '/home/xian/Downloads/after_correct/%s' % key
        #image.save(savefile, format="jpeg")
        #print('upload: ', key)
        col_img_dict["crops"].append("https://s3.cn-north-1.amazonaws.com.cn/lqdzj-image/%s" % key)
    return col_img_dict

