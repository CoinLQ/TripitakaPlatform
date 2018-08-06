from django.shortcuts import render
from rest_framework import mixins, viewsets
from rest_framework import viewsets, permissions, mixins, generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import detail_route, list_route
from tdata.models import *
from tdata.serializer import EmailVerifycodeSerializer
from tdata.serializer import PageSerializer
from django.http import HttpResponse
from jwt_auth.models import Staff
from jwt_auth.serializers import StaffSerializer
from django.conf import settings
import base64


class PageViewSet(viewsets.ReadOnlyModelViewSet, mixins.ListModelMixin):
    queryset = Page.objects.all()
    serializer_class = PageSerializer
    permission_classes = []

class ResetStaffView(mixins.CreateModelMixin,mixins.UpdateModelMixin, generics.GenericAPIView):
    queryset = Staff.objects.all()
    permission_classes = (permissions.AllowAny, )
    serializer_class = StaffSerializer 

    def put(self, request, *args, **kwargs):
        params = request.data
        email, verify_code, password = params['email'], params['vericode'], params['password']
        codes = EmailVerifycode.objects.filter(email=email, code=verify_code)
        if len(codes) > 0:
            codes.delete()
            staff = Staff.objects.get(email=email)
            staff.set_password(password)
            staff.save()
            return Response({'status':0, 'msg':'成功'})
        else:
            return Response({'status':'-1', 'msg':'验证码错误'}, status=status.HTTP_406_NOT_ACCEPTABLE)

class HomeResetStaffView(mixins.CreateModelMixin,mixins.UpdateModelMixin, generics.GenericAPIView):
    queryset = Staff.objects.all()
    permission_classes = (permissions.AllowAny, )
    serializer_class = StaffSerializer 

    def put(self, request, *args, **kwargs):
        params = request.data
        send_type, email = params['send_type'], params['email']
        try:
            if send_type == 'base_info':
                new_username, password = params['username'], params['password']
                staff = Staff.objects.get(email=email)
                if staff.check_password(password):
                    staff.username = new_username
                    staff.save()
                    return Response({'status':0, 'msg':'成功'})
                else:
                    return Response({'status':'-1', 'msg':'密码错误，修改失败。'}, status=status.HTTP_406_NOT_ACCEPTABLE)
            elif send_type == 'reset_pwd':
                oldpassword, newpassword = params['oldpassword'], params['newpassword']
                staff = Staff.objects.get(email=email)
                if staff.check_password(oldpassword):
                    staff.set_password(newpassword)
                    staff.save()
                    return Response({'status':0, 'msg':'成功'})
                else:
                    return Response({'status':'-1', 'msg':'修改失败，原密码不匹配。'}, status=status.HTTP_406_NOT_ACCEPTABLE)
            else:
                return Response({'status':'-1', 'msg':'错误的请求。'}, status=status.HTTP_406_NOT_ACCEPTABLE)
        except Exception as e:
            return Response({'status':'-1', 'msg':'操作失败。'}, status=status.HTTP_406_NOT_ACCEPTABLE)

class EmailVerifycodeView(mixins.CreateModelMixin, generics.GenericAPIView):
    queryset = EmailVerifycode.objects.all()
    permission_classes = (permissions.AllowAny, )
    serializer_class = EmailVerifycodeSerializer

    def post(self, request, *args, **kwargs):
        try:
            return self.create(request, *args, **kwargs)
        except Exception as e:
            return Response({"status": -1, "msg": str(e)}, status=status.HTTP_406_NOT_ACCEPTABLE)


def active_user(request, token):
    key = 'XIANHU'
    jiami_key, jiemi_key = suanfa(key)
    miwen = token
    miwen = miwenToOld(miwen)
    mingwen = bianma(jiemi_key, miwen)
    code = mingwen[-6:]
    email = mingwen[:-6]
    #验证激活码
    try:
        email_record = EmailVerifycode.objects.get(email=email, send_type = 'register')
        if email_record.code == code and email_record.email == email:
            staff = Staff.objects.get(email=email)
            staff.is_active = True
            staff.save()
            #删除激活码
            try:
                EmailVerifycode.objects.filter(email=email, send_type = 'register').delete()  
            except Exception as e:
                pass
            host_url = "http://" +  settings.FRONT_HOST
            active_url = '/'.join([host_url + "/activate", miwen])
            return render(request, 'active_success.html', {'message': '激活成功请登录', 'url': host_url})
        else:
            return render(request, 'active_fail.html', {'message': '激活未能成功，请联系管理员。', 'url': request.path})
    except Exception as e:
        return render(request, 'active_fail.html', {'message': '激活链接过期或错误。', 'url': request.path})

#加密


def suanfa(key):
    alp = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

    jiami_key = {}
    jiemi_key = {}

    list0 = list(alp)
    list1 = list(key)
    list2 = list(alp)
    for n in list1:
        for m in list2:
            if m == n:
                list2.remove(m)

    alp1 = ''.join(list2)
    key1 = key + alp1
    list3 = list(key1)

    a = 0
    if a < len(list0):
        for m in list0:
            jiami_key[m] = list3[a]
            a = a + 1

    b = 0
    if b < len(list3):
        for n in list3:
            jiemi_key[n] = list0[b]
            b = b + 1

    #print jiami_key
    #print jiemi_key
    return jiami_key, jiemi_key
#解密


def bianma(key_dic, data):
    list_data = list(data)
    data1 = []
    for a in list_data:
         if a == ' ':
             data1.append(a)

         elif a.islower():
             a = a.upper()
             if a in key_dic.keys():
                 x = key_dic[a]
                 data1.append(x.lower())

         elif a.isupper():
             if a in key_dic.keys():
                 x = key_dic[a]
                 data1.append(x)
         else:
             data1.append(a)

    data2 = ''.join(data1)

    #print data2
    return data2


def miwenToNew(key):
    alp = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    newKey = key
    # 重新排序
    newKey = newKey[::-1]
    # 替换文字
    words = ''

    for item in newKey:
        if item == '.':
            words = words + '*'
        elif item == '@':
            words = words + '$'
        elif item == '9':
            words = words + 'A'
        elif item in alp and item != '9':
            index = alp.index(item)
            words = words + alp[index+1]
        else:
            words = words + item
    return words


def miwenToOld(data2):
    # 解密。
    # 替换文字。
    alp = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    words = ''
    newKey = data2
    for item in newKey:
        if item == '*':
            words = words + '.'
        elif item == '$':
            words = words + '@'
        elif item == 'A':
            words = words + '9'
        elif item in alp and item != 'A':
            index = alp.index(item)
            words = words + alp[index-1]
        else:
            words = words + item

    # 重新排序。
    newKey = words
    newKey = newKey[::-1]
    # 明文。
    data2 = newKey
    return data2


email_vericode = EmailVerifycodeView.as_view()
reset_password = ResetStaffView.as_view()
home_reset_password = HomeResetStaffView.as_view()