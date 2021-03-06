from rest_framework import serializers
from tdata.models import Page, LQSutra, LQReel, Sutra,Reel,Tripitaka,Volume, ReelOCRText,EmailVerifycode
from TripitakaPlatform import email_send
from tasks.models import Task, ReelCorrectText
import tdata.lib.image_name_encipher as encipher
import json
import boto3
import urllib
s3c = boto3.client('s3')
my_bucket = 'lqdzj-images'

class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = '__all__'

class LQReelSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = LQReel
        fields = ('id', 'reel_no', 'text_ready')

class LQSutraSerializer(serializers.ModelSerializer):
    lqreel_set = LQReelSimpleSerializer(many=True)

    class Meta:
        model = LQSutra
        fields = ('id', 'sid', 'name', 'author', 'total_reels', 'lqreel_set')

class ReelSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reel
        fields = ('id', 'reel_no','ocr_ready','start_vol','start_vol_page','end_vol','end_vol_page', 'correct_ready')

class SutraSerializer(serializers.ModelSerializer):
    reel_set = ReelSimpleSerializer(many=True)

    class Meta:
        model = Sutra
        fields = ('id','sid', 'name', 'total_reels','reel_set')
        read_only_fields = ('id','sid', 'name', 'total_reels', 'reel_set')        

class TripitakaSerializer(serializers.ModelSerializer):    
    withvol = serializers.SerializerMethodField()
    class Meta:
        model = Tripitaka
        fields = ('code', 'name', 'withvol')
        read_only_fields =('code', 'name', 'withvol')

    def get_withvol(self, obj):
        if obj.code in ['GL', 'LC', 'JX']:
            return False
        else:
            return True

class VolumeSerializer(serializers.ModelSerializer):    
     class Meta:
        model = Volume
        fields = '__all__'

def get_page_text(page_dict):
    txt = {}
    for c in page_dict['char_data']:
        col_no = int(c['line_no'])
        char_no = int(c['char_no'])
        char = c['ch']
        if col_no in txt.keys():
            txt[col_no][char_no] = char
        else:
            txt[col_no] = {char_no: char}
    for col_no in txt.keys():
        col_txt = sorted(txt[col_no].items(), key=lambda a: a[0], reverse=False)
        txt[col_no] = ''.join(list(zip(*col_txt))[1])
    p_txts = sorted(txt.items(), key=lambda a: a[0], reverse=False)
    p_txt = list(zip(*p_txts))[1]
    return p_txt

def gen_key(code):
    ks = code.split('_')
    key = ("{}/" * (len(ks) - 1)).format(*ks[:-1]) + code
    return key

def gen_signed_key(code):
    signed_key = gen_key(code).replace(code, encipher.get_signed_name_prefix(code))
    return signed_key

class TripitakaPageListSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Page
        fields = ['image_url', 'page_code']

    def get_image_url(self, obj):
        return obj['image_url']

class TripitakaPageSerializer(serializers.ModelSerializer):
    page_data = serializers.SerializerMethodField()

    class Meta:
        model = Page
        fields = ['page_data']

    def get_page_data(self, obj):
        try:
            s3c.get_object_acl(Bucket=my_bucket, Key=gen_signed_key(obj.page_code) + '.cut')
            cut_dict = json.loads(urllib.request.urlopen(encipher.get_cut_url(obj.reel, obj.reel_page_no)).readlines()[0])
            ocr_txt = get_page_text(cut_dict)
            ocr_cuts = cut_dict['char_data']
        except Exception as e:
            ocr_txt = []
            ocr_cuts = []
        try:
            task = Task.objects.filter(typ=1, task_no=1, reel=obj.reel)
            first_correct_txt = task.result.split('\n')
        except:
            first_correct_txt = []
        try:
            task = Task.objects.filter(typ=1, task_no=2, reel=obj.reel)
            second_correct_txt = task.result.split('\n')
        except:
            second_correct_txt = []
        try:
            reelcorrects = ReelCorrectText.objects.filter(reel=obj.reel).order_by("created_at")
            reelcorrect = list(reelcorrects)[-1]
            reelcorrectid = reelcorrect.id
            whole_text = reelcorrect.text
            # TODO 改成最新的校对文本即可
            text_list = []
            page_txt_list = whole_text.split('p')
            blank_no = 0
            pos = 0
            for p_no, i in enumerate(page_txt_list):
                i = i.split('\n')
                for line_no, k in enumerate(i):
                    for char_no, l in enumerate(k):
                        if l == 'b':
                            blank_no += 1
                            text_list.append([p_no, 0, line_no, char_no, l, -1])
                        else:
                            text_list.append([p_no, 0, line_no, char_no, l, pos-blank_no])
                        pos += 1
            verify_txt = []
            tmp = -1
            for t_no, t in enumerate(text_list):
                if t[0] == obj.reel_page_no:
                    if tmp != t[2]:
                        tmp = t[2]
                        verify_txt.append([])
                    verify_txt[-1].append({'char': t[-2], 'no': t[-1]})
            # page_txt = whole_text.split('p')[obj.reel_page_no]
            # verify_txt = whole_text.split('\n')
        except:
            verify_txt = []
            reelcorrectid = -1

        if obj.cut_info:
            final_cuts = json.loads(obj.cut_info)['char_data']
        else:
            final_cuts = []

        return {
            'ocr_txt': ocr_txt,
            'first_correct_txt': first_correct_txt,
            'second_correct_txt': second_correct_txt,
            'verify_txt': verify_txt,
            'final_cuts': final_cuts,
            'ocr_cuts': ocr_cuts,
            'reelcorrectid': reelcorrectid,
        }

class EmailVerifycodeSerializer(serializers.ModelSerializer):
    class Meta:
       model = EmailVerifycode
       fields = '__all__'

    def create(self, validated_data):
        try:
            email = validated_data['email']
        except Exception as e:
            email = ''
        try:
            send_type = validated_data['send_type']
        except Exception as e:
            send_type = ''
        try:
            username = validated_data['username']
        except Exception as e:
            username = ''
        
        if email_send.send_verifycode_email(email=email, send_type=send_type, username=username):
            emailVerifycode = EmailVerifycode.objects.get(email=email,send_type=send_type, username=username)
        return emailVerifycode
