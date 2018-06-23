from random import Random  # 用于生成随机码
from django.core.mail import send_mail  # 发送邮件模块
from django.core.mail import EmailMultiAlternatives  # 导入邮件模块
from tdata.models import EmailVerifycode  # 邮箱验证model
from rest_framework.authtoken.models import Token
from django.conf.urls import url
from jwt_auth.models import Staff
from django.conf import settings
import base64
# 生成随机字符串


def random_str(randomlength=8):
    str = ''
    chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
    length = len(chars) - 1
    random = Random()
    for i in range(randomlength):
        str += chars[random.randint(0, length)]
    return str


def send_verifycode_email(email, send_type, username):
    try:
        if send_type == "forget":
            EmailVerifycode.objects.filter(email=email,send_type = 'forget').delete()
        elif send_type == "register":
            EmailVerifycode.objects.filter(email=email,send_type = 'register').delete()
    except Exception as e:
        pass
    
    email_record = EmailVerifycode()
    # 将给用户发的信息保存在数据库中
    code = random_str(6)
    email_record.code = code
    email_record.email = email
    email_record.send_type = send_type
    email_record.username = username
    email_record.save()
    # 初始化为空
    email_title = ""
    email_body = ""
    # 如果为注册类型
    if send_type == "register":
        email_title = "注册激活链接"
        s = email+code
        key = 'XIANHU'
        data = s
        jiami_key, jiemi_key = suanfa(key)
        miwen = bianma(jiami_key, data)
        miwen = miwenToNew(miwen)
        mingwen = miwenToOld(miwen)
        mingwen = bianma(jiemi_key, mingwen)
        if settings.DEBUG:
            host_url = settings.FRONT_HOST + "/activate"
        else:
            host_url = settings.PUBLIC_HOST + "/activate"
        active_url = "http://" + '/'.join([host_url, miwen])
        # 发送邮件
        from_email = settings.EMAIL_FROM
        tolist = [email]
        cclist = []
        try:
            if SendMultiEmail(from_email, tolist, cclist, active_url, username):
                return True
            else:
                return False
        except Exception as e:
            return False
    elif send_type == "forget":
        email_title = "找回您的密码"
        email_body = "龙泉大藏经校勘平台用户您好，\n您已发起用户重置密码请求，您的本次操作验证码为：{0}。如果不是您本人操作，请忽略此邮件！\n阿弥陀佛！".format(
            code)
        # 发送邮件
        try:
            send_status = send_mail(email_title, email_body, settings.EMAIL_FROM, [email])
        except Exception as e:
            return False
        if send_status:
            return True
        else:
            return False


# 加密
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

    # print jiami_key
    # print jiemi_key
    return jiami_key, jiemi_key
# 解密


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

    # print data2
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


# tolist:收件人；cclist：抄送人；fromemail：发件人
# 邮件中显示的发件人的邮箱，可以试试以其他人的邮件发哈，不保证成功^^
def SendMultiEmail(from_email, tolist, cclist, active_url, username):
    try:
        # 发送邮件的主体，可以放在函数内，也可以通过参数传过来，看自己需要。
        html_body = '''   
            <div style="width:600px;padding:20px;margin:0 auto;text-align:left;font:14px/2 &quot;Helvetica Neue&quot;,Helvetica,STheiti,Arial,Tahoma,微软雅黑,sans-serif,serif;color:#333">
                <a href="http://work.lqdzj.cn/" target="_blank" style="text-decoration:none;color:black;font-size:24px">龙泉大藏经校勘平台-激活</a>
                <div style="border-top:1px solid #808080;border-bottom:1px solid #808080;margin:20px 0 10px;padding:20px 0">
                <p style="font-size:14px;font-weight:bold;font-family:'Helvetica Neue',Helvetica,STheiti,Arial,Tahoma,微软雅黑,sans-serif,serif;color:#222;padding:0;margin:0">尊敬的藏经平台用户
                    <b style="color:#0086d0;margin:0 5px">'''+username+'''</b>您好：</p>
                <div style="font-size:14px;font-family:'Helvetica Neue',Helvetica,STheiti,Arial,Tahoma,微软雅黑,sans-serif,serif;color:#464646;padding:0;margin:20px 0 30px;line-height:1.6">您可以在收到此邮件后激活龙泉大藏经校勘平台账号。龙泉大藏经校勘平台致力于更现代、更高效、更专业化地进行大藏经校勘整理工作，方便诸位法师及广大信众轻松高效地参与并完成大藏经整理工作，泽被后世，利益众生。感恩随喜！</div>
                <p>
                    <a href="'''+active_url+'''"
                    target="_blank" style="display:block;width:269px;height:44px;background:#5da9f9;text-decoration:none;font-size:18px;color:#fff;text-align:center;line-height:44px;border-radius:5px">点击激活藏经平台账号</a>
                </p>
                <p style="font-size:12px;font-family:'Helvetica Neue',Helvetica,STheiti,Arial,Tahoma,微软雅黑,sans-serif,serif;color:#666;padding:0;margin:30px 0 15px;line-height:1.6">如果点击无效，请复制下方网页地址到浏览器地址栏中打开：
                    <a href="'''+active_url+'''"
                    target="_blank" style="display:block;font-size:12px;color:#004778;word-break:break-all;word-wrap:break-word">''' + active_url + ''' </a>
                </p>
                </p>
                </div>
                <div style="font-size:12px;font-family:'Helvetica Neue',Helvetica,STheiti,Arial,Tahoma,微软雅黑,sans-serif,serif;color:#888;padding:0;margin:0;text-align:center">Copyright ©
                <span style="border-bottom:1px dashed #ccc;z-index:1" t="7" onclick="return false;" data="2008-2018">2008-2018</span> lqdzj.cn</div>
            </div>
         '''

        text_content = '您好，这是龙泉大藏经校勘平台注册激活邮件。'  # 对方不支持多媒体邮件的话显示这里的内容
        subject = '龙泉大藏经校勘平台注册激活邮件(请不要回复此邮件)'  # 邮件标题
        # headers = {"Cc":",".join(cclist)}这一部分起到显示的作用。
        # 不加的话，邮件是可以发送成功的，但是发送的邮件里不显示抄送的名单，回复的时候不能回复所有，不方便
        msg = EmailMultiAlternatives(
            subject, text_content, from_email, tolist, cclist, headers={"Cc": ",".join(cclist)})
        # 邮件显示html_body的内容，html编码
        msg.attach_alternative(html_body, "text/html")
        msg.send()
        return True
    except Exception as e:
        return False
