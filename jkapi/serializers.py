from rest_framework import serializers
from tdata.models import *
from tasks.models import *

import json

class TripitakaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tripitaka
        fields = ('id', 'shortname')
        read_only_fields = ('id', 'shortname')

class DiffSegTextSerializer(serializers.ModelSerializer):
    tripitaka = TripitakaSerializer()

    class Meta:
        model = DiffSegText
        fields = ('tripitaka', 'text', 'start_char_pos', 'rect', 'column_url')
        read_only_fields = ('tripitaka', 'text', 'start_char_pos', 'rect', 'column_url')

class DiffSegSerializer(serializers.ModelSerializer):
    diffsegtexts = DiffSegTextSerializer(many=True)

    class Meta:
        model = DiffSeg
        fields = ('id', 'diffseg_no', 'recheck', 'recheck_desc', 'diffsegtexts')
        read_only_fields = ('id', 'diffseg_no', 'recheck', 'recheck_desc', 'diffsegtexts')

class DiffSegResultSerializer(serializers.ModelSerializer):
    diffseg = DiffSegSerializer(read_only=True)

    class Meta:
        model = DiffSegResult
        fields = ('id', 'diffseg', 'typ', 'selected_text', 'merged_diffsegresults', 'split_info', 'selected', 'doubt', 'doubt_comment')
        read_only_fields = ('id', 'diffseg', 'typ', 'selected_text', 'merged_diffsegresults', 'split_info', 'selected', 'doubt', 'doubt_comment')

class DiffSegResultSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiffSegResult
        fields = ('id', 'typ', 'selected_text', 'merged_diffsegresults', 'split_info', 'selected', 'doubt', 'doubt_comment')
        read_only_fields = ['id']
        extra_kwargs = {'typ': {'required': 'True'}}

    def validate(self, data):
        typ = data['typ']
        if typ == DiffSegResult.TYPE_SELECT:
            if 'selected_text' not in data:
                raise serializers.ValidationError('no selected_text')
            self.is_valid_selected_text(data['selected_text'])
        elif typ == DiffSegResult.TYPE_SPLIT:
            if 'split_info' not in data:
                raise serializers.ValidationError('no split_info')
            if 'selected_text' not in data:
                raise serializers.ValidationError('no selected_text')
            self.check_split_info(data)
        return data

    def is_valid_selected_text(self, value):
        for diffsegtext in self.instance.diffseg.diffsegtexts.all():
            if diffsegtext.text == value:
                return value
        raise serializers.ValidationError('invalid selected_text')

    def check_split_info(self, data):
        tripitaka_id_to_oldtext = {}
        for diffsegtext in self.instance.diffseg.diffsegtexts.all():
            tripitaka_id_to_oldtext[diffsegtext.tripitaka_id] = diffsegtext.text
        try:
            split_info = json.loads(data['split_info'])
        except:
            raise serializers.ValidationError('not json string')
        try:
            selected_text = data['selected_text']
            merged_diffsegresults = data['merged_diffsegresults']
        except:
            raise serializers.ValidationError('data error')
        if merged_diffsegresults != []:
            raise serializers.ValidationError('data error')
        if 'split_count' not in split_info:
            raise serializers.ValidationError('no split_count')
        if 'tripitaka_id_to_texts' not in split_info:
            raise serializers.ValidationError('no tripitaka_id_to_texts')
        split_count = split_info['split_count']
        tripitaka_id_to_texts = split_info['tripitaka_id_to_texts']
        selected_lst = split_info['selected_lst']
        try:
            for tripitaka_id, oldtext in tripitaka_id_to_oldtext.items():
                tripitaka_id = '%s' % tripitaka_id
                texts = tripitaka_id_to_texts[tripitaka_id]
                if len(texts) != split_count:
                    raise Exception()
                if oldtext != ''.join(texts):
                    raise Exception()
            if selected_text != ''.join(selected_lst):
                raise Exception()
        except:
            raise serializers.ValidationError('invalid split_info')

class CorrectSegSerializer(serializers.ModelSerializer):
    class Meta:
        model = CorrectSeg
        fields = ('id', 'tag', 'position', 'text1', 'text2', 'selected_text', 'page_no', 'line_no', 'char_no', 'doubt_comment')
        read_only_fields = ('id', 'tag', 'position', 'text1', 'text2', 'page_no', 'line_no', 'char_no')