from rest_framework import serializers
from tdata.models import Page, LQSutra, LQReel, Sutra,Reel,Tripitaka,Volume

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
        fields = ('id', 'sid', 'name', 'total_reels', 'lqreel_set')

class ReelSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reel
        fields = ('id', 'reel_no','ocr_ready','start_vol','start_vol_page','end_vol','end_vol_page')

class SutraSerializer(serializers.ModelSerializer):
    reel_set = ReelSimpleSerializer(many=True)

    class Meta:
        model = Sutra
        fields = ('id','sid', 'name', 'total_reels','reel_set')
        read_only_fields = ('id','sid', 'name', 'total_reels', 'reel_set')        

class TripitakaSerializer(serializers.ModelSerializer):    
    class Meta:
        model = Tripitaka
        fields = ('code', 'name')
        read_only_fields =('code', 'name')

class VolumeSerializer(serializers.ModelSerializer):    
     class Meta:
        model = Volume
        fields = '__all__'
    # class Meta:
    #     model = Volume
    #     fields = ('tripitaka_code', 'vol_no', 'page_count')
    #     read_only_fields =('tripitaka_code', 'vol_no', 'page_count')


 