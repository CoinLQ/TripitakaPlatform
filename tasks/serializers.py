from rest_framework import serializers
from .models import Task
from django.conf import settings
from django.utils.timezone import localtime

class DateTimeTzAwareField(serializers.DateTimeField):

    def to_representation(self, value):
        value = localtime(value);
        return super(DateTimeTzAwareField, self).to_representation(value)

class TaskSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    picked_at = DateTimeTzAwareField(format=settings.DATETIME_FORMAT)
    finished_at = DateTimeTzAwareField(format=settings.DATETIME_FORMAT)


    def get_status(self, obj):
        return obj.get_status_display()

    class Meta:
        model = Task
        fields = '__all__'


class CorrectTaskSerializer(TaskSerializer):
    batchtask = serializers.SerializerMethodField()
    tripitaka_name = serializers.SerializerMethodField()
    sutra = serializers.SerializerMethodField()
    reel_no = serializers.SerializerMethodField()
    priority = serializers.SerializerMethodField()
    task_no = serializers.SerializerMethodField()

    def get_task_no(self, obj):
        return "校%s" % obj.get_task_no_display()

    def get_priority(self, obj):
        return obj.get_priority_display()

    def get_tripitaka_name(self, obj):
        return obj.reel.sutra.tripitaka.name

    def get_sutra(self, obj):
        return obj.reel.sutra.name

    def get_reel_no(self, obj):
        return obj.reel.reel_no

    def get_batchtask(self, obj):
        return obj.batchtask.batch_no

    class Meta:
        model = Task
        fields = ('batchtask', 'tripitaka_name',
        'sutra', 'reel_no', 'priority', 'id', 'status', 'task_no', 'picked_at', 'finished_at')
        read_only_fields = ('id', )

class VerifyCorrectTaskSerializer(CorrectTaskSerializer):
    pass

class CorrectDifficultTaskSerializer(CorrectTaskSerializer):
    pass


class JudgeTaskSerializer(TaskSerializer):
    batchtask = serializers.SerializerMethodField()
    lqsutra_name = serializers.SerializerMethodField()
    lqreel_no = serializers.SerializerMethodField()
    base_tripitaka_name = serializers.SerializerMethodField()
    priority = serializers.SerializerMethodField()
    task_no = serializers.SerializerMethodField()

    def get_task_no(self, obj):
        return "校%s" % obj.get_task_no_display()

    def get_priority(self, obj):
        return obj.get_priority_display()

    def get_lqsutra_name(self, obj):
        try:
            return obj.lqreel.lqsutra.name
        except:
            return ''

    def get_base_tripitaka_name(self, obj):
        try:
            return obj.base_reel.sutra.tripitaka.name
        except:
            return ''
    def get_lqreel_no(self, obj):
        try:
            return obj.lqreel.reel_no
        except:
            return ''

    def get_batchtask(self, obj):
        return obj.batchtask.batch_no

    class Meta:
        model = Task
        fields = ('batchtask', 'lqsutra_name', 'base_tripitaka_name',
            'lqreel_no', 'priority', 'id',  'status', 'task_no', 'picked_at', 'finished_at')
        read_only_fields = ('id', )



class VerifyJudgeTaskSerializer(JudgeTaskSerializer):
    pass

class JudgeDifficultTaskSerializer(JudgeTaskSerializer):
    pass

class PunctTaskSerializer(CorrectTaskSerializer):
    task_no = serializers.SerializerMethodField()
    lqsutra_name = serializers.SerializerMethodField()

    def get_lqsutra_name(self, obj):
        try:
            return obj.lqreel.lqsutra.name
        except:
            return ''

    def get_task_no(self, obj):
        return "标%s" % obj.get_task_no_display()

    class Meta:
        model = Task
        fields = ('batchtask', 'lqsutra_name', 'tripitaka_name',
        'sutra',  'reel_no', 'priority', 'task_no', 'id',
        'status', 'picked_at', 'finished_at')
        read_only_fields = ('id', )

class VerifyPunctTaskSerializer(PunctTaskSerializer):
    pass

class LqpunctTaskSerializer(JudgeTaskSerializer):

    def get_task_no(self, obj):
        return "标%s" % obj.get_task_no_display()

    class Meta:
        model = Task
        fields = ('batchtask', 'lqsutra_name', 'base_tripitaka_name',
            'lqreel_no', 'priority', 'task_no', 'id',  'status', 'picked_at', 'finished_at')
        read_only_fields = ('id', )

class VerifyLqpunctTaskSerializer(LqpunctTaskSerializer):
    pass
