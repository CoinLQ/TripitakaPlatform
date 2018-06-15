import os, hashlib
from django.conf import settings

IMAGE_SECRET_KEY = os.environ.get('IMAGE_SECRET_KEY')

def sign(name_prefix):
    m = hashlib.shake_256()
    s = name_prefix + IMAGE_SECRET_KEY
    data = s.encode('utf-8')
    m.update(data)
    return m.hexdigest(4)

def get_signed_name_prefix(name_prefix):
    digest = sign(name_prefix)
    new_name_prefix = '%s-%s' % (name_prefix, digest)
    return new_name_prefix

def get_signed_path(path):
    pos = path.rfind('/')
    dot_pos = path.rfind('.')
    name_prefix = path[pos+1 : dot_pos]
    new_name_prefix = get_signed_name_prefix(name_prefix)
    new_path = '%s%s%s' % (path[:pos+1], new_name_prefix, path[dot_pos:])
    return new_path

def get_image_url(reel, vol_page):
    path = '%s%d.jpg' % (reel.url_prefix(), vol_page)
    signed_path = get_signed_path(path)
    url = settings.PAGE_IMAGE_URL_PREFIX + signed_path
    return url

def get_cut_url(reel, vol_page, suffix='cut'):
    path = '%s%d.%s' % (reel.url_prefix(), vol_page, suffix)
    signed_path = get_signed_path(path)
    url = settings.PAGE_IMAGE_URL_PREFIX + signed_path
    return url