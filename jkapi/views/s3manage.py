import boto3
from rest_framework.views import APIView
from rest_framework.response import Response
import tdata.lib.image_name_encipher as encipher
from django.conf import settings

s3c = boto3.client('s3')

class BucketViewset(APIView):
    def get(self, request, format=None):
        bucket_list = s3c.list_buckets()['Buckets']
        return Response({'bucketnames': [{'Prefix': b['Name']} for b in bucket_list if b['Name'].split('-')[0] == 'lqdzj']})

def get_all_contents(content_type, prefix, bucket):
    res = s3c.list_objects_v2(Bucket=bucket, MaxKeys=1, Delimiter='/', Prefix=prefix)
    # 获取列表，方法含义参见文档 http://boto3.readthedocs.io/en/latest/reference/services/s3.html#S3.Client.list_objects_v2
    if content_type in res.keys():
        res = s3c.list_objects_v2(Bucket=bucket, MaxKeys=1000, Delimiter='/', Prefix=prefix)
        contents = res[content_type]
        # 根据获取列表数据 Contents：为对象文件 CommonPrefixes：为文件夹
        IsTruncated = res['IsTruncated']
        # 判断是否还有后续数据
        while IsTruncated:
            # 循环取出后续数据
            ct = res['NextContinuationToken']
            # 后续数据令牌
            res = s3c.list_objects_v2(Bucket=bucket, MaxKeys=1000, Delimiter='/', Prefix=prefix, ContinuationToken=ct)
            contents.extend(res[content_type])
            IsTruncated = res['IsTruncated']
        return contents
    else:
        return []

def get_part_contents(content_type, prefix, bucket, ContinuationToken):
    if not ContinuationToken:
        res = s3c.list_objects_v2(Bucket=bucket, MaxKeys=1, Delimiter='/', Prefix=prefix)
        # 获取列表，方法含义参见文档 http://boto3.readthedocs.io/en/latest/reference/services/s3.html#S3.Client.list_objects_v2
        if content_type in res.keys():
            res = s3c.list_objects_v2(Bucket=bucket, MaxKeys=30, Delimiter='/', Prefix=prefix)
            contents = res[content_type]
            # 根据获取列表数据 Contents：为对象文件 CommonPrefixes：为文件夹
            IsTruncated = res['IsTruncated']
            if IsTruncated:
                return {'contents': contents, 'ct': res['NextContinuationToken']}
            else:
                return {'contents': contents, 'ct': ''}
        # 判断是否还有后续数据
        else:
            return []
    else:
        res = s3c.list_objects_v2(Bucket=bucket, MaxKeys=30, Delimiter='/', Prefix=prefix, ContinuationToken=ContinuationToken)
        contents = res[content_type]
        # 根据获取列表数据 Contents：为对象文件 CommonPrefixes：为文件夹
        IsTruncated = res['IsTruncated']
        if IsTruncated:
            return {'contents': contents, 'ct': res['NextContinuationToken']}
        else:
            return {'contents': contents, 'ct': ''}

def gen_key(code):
    ks = code.split('_')
    key = ("{}/" * (len(ks) - 1)).format(*ks[:-1]) + code
    return key

def gen_signed_key(code):
    signed_key = gen_key(code).replace(code, encipher.get_signed_name_prefix(code))
    return signed_key

class SourceSearch(APIView):
    def get(self, request, code, format=None):
        bucket_list = s3c.list_buckets()['Buckets']
        b_names = [b['Name'] for b in bucket_list if b['Name'].split('-')[0] == 'lqdzj']
        suffix_lst = ['.jpg', '.cut', '.col', '.txt']
        result_lst = []
        for bucket in b_names:
            for suffix in suffix_lst:
                try:
                    key = gen_key(code) + suffix
                    signed_key = gen_signed_key(code) + suffix
                    s3c.get_object_acl(Bucket=bucket, Key=key)
                    result_lst.append('{}/{}/{}'.format(settings.FILE_URL_PREFIX, bucket, key))
                except:
                    pass
                try:
                    s3c.get_object_acl(Bucket=bucket, Key=signed_key)
                    result_lst.append('{}/{}/{}'.format(settings.FILE_URL_PREFIX, bucket, signed_key))
                except:
                    pass
        if result_lst:
            result_lst = [{'label': r.split('/')[-1], 'path': r} for r in result_lst]
        return Response(result_lst)

class DelSource(APIView):
    def get(self, request, format=None):
        path = request.query_params['p']
        split_pos = path.find('/')
        bucket = path[:split_pos]
        key = path[split_pos+1:]
        try:
            res_del = s3c.delete_object(
                Bucket=bucket,
                Key=key,
            )
            res = '删除成功！'
        except Exception as e:
            res = '删除失败！'
        return Response(res)

class RepSource(APIView):
    def post(self, request, format=None):
        path = request.query_params['p']
        split_pos = path.find('/')
        bucket = path[:split_pos]
        key = path[split_pos+1:]
        try:
            s3c.upload_fileobj(request.data['file'], bucket, key)
            res = '更新成功！'
        except Exception as e:
            res = '更新失败！'
        return Response(res)

class BucketDetail(APIView):
    def get(self, request, name, format=None):
        key = request.query_params['key']
        ct = request.query_params['ct']
        if not key:
            key = ''
        try:
            result = get_part_contents('CommonPrefixes', key, name, ct)
            if result:
                lst = result['contents']
                ct = result['ct']
                lst = [{
                           'key': ele['Prefix'],
                           'Prefix': int(ele['Prefix'].split('/')[-2]) if ele['Prefix'].split('/')[-2].isdigit() else ele['Prefix'].split('/')[-2]
                       } for ele in lst]
                lst = sorted(lst, key=lambda X: X['Prefix'])
                return (Response({'contents': lst, 'ct': ct}))
            else:
                result = get_part_contents('Contents', key, name, ct)
        except Exception as e:
            result = get_part_contents('Contents', key, name, ct)
        if result:
            lst = result['contents']
            ct = result['ct']
            lst = [{
                       'key': ele['Key'],
                       'Prefix': int(ele['Key'].split('/')[-1]) if ele['Key'].split('/')[-1].isdigit() else ele['Key'].split('/')[-1],
                       'leaf': True,
                       'path': '{}/{}/{}'.format(settings.FILE_URL_PREFIX, name, ele['Key']),
                       'suffix': ele['Key'].split('.')[-1]
                   } for ele in lst]
            lst = sorted(lst, key=lambda X: X['Prefix'])
        else:
            lst = []
            ct = ''
        return (Response({'contents': lst, 'ct': ct}))
