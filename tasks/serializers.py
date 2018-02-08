from rest_framework import serializers
from .models import Task




class TaskSerializer(serializers.ModelSerializer):

    class Meta:
        model = Task
        fields = '__all__'

class CorrectTaskSerializer(serializers.ModelSerializer):
    batch_task = serializers.SerializerMethodField()
    lqsutra_name = serializers.SerializerMethodField()
    tripitaka_name = serializers.SerializerMethodField()
    sutra = serializers.SerializerMethodField()
    reel_no = serializers.SerializerMethodField()
    priority = serializers.SerializerMethodField()

    def get_status(self, obj):
        return obj.get_status_display()

    def get_priority(self, obj):
        return obj.get_priority_display()

    def get_lqsutra_name(self, obj):
        try:
            return obj.lqreel.lqsutra.name
        except:
            return ''

    def get_tripitaka_name(self, obj):
        return obj.reel.sutra.tripitaka.name

    def get_sutra(self, obj):
        return obj.reel.sutra.name

    def get_reel_no(self, obj):
        return obj.reel.reel_no

    def get_batch_task(self, obj):
        return obj.batch_task.batch_no

    class Meta:
        model = Task
        fields = ('batch_task', 'lqsutra_name', 'tripitaka_name', 'sutra', 'reel_no', 'priority', 'id')
        read_only_fields = ('id', )

class VerifyCorrectTaskSerializer(CorrectTaskSerializer):
    pass


class JudgeTaskSerializer(serializers.ModelSerializer):
    batch_task = serializers.SerializerMethodField()
    lqsutra_name = serializers.SerializerMethodField()
    lqreel_no = serializers.SerializerMethodField()
    base_tripitaka_name = serializers.SerializerMethodField()
    priority = serializers.SerializerMethodField()


    def get_priority(self, obj):
        return obj.get_priority_display()

    def get_lqsutra_name(self, obj):
        try:
            return obj.lqreel.lqsutra.name
        except:
            return ''

    def get_base_tripitaka_name(self, obj):
        return obj.base_reel.sutra.tripitaka.name

    def get_lqreel_no(self, obj):
        try:
            return obj.lqreel.reel_no
        except:
            return ''

    def get_batch_task(self, obj):
        return obj.batch_task.batch_no

    class Meta:
        model = Task
        fields = ('batch_task', 'lqsutra_name', 'base_tripitaka_name', 'lqreel_no', 'priority', 'id')
        read_only_fields = ('id', )



class VerifyJudgeTaskSerializer(JudgeTaskSerializer):
    pass


class PunctTaskSerializer(JudgeTaskSerializer):
    progress = serializers.SerializerMethodField()

    def get_progress(self, obj):
        return "%s标" % obj.progress

    class Meta:
        model = Task
        fields = ('batch_task', 'lqsutra_name', 'base_tripitaka_name', 'lqreel_no', 'priority', 'progress', 'id')
        read_only_fields = ('id', )

class VerifyPunctTaskSerializer(PunctTaskSerializer):
    pass

class LqpunctTaskSerializer(PunctTaskSerializer):
    pass

class VerifyLqpunctTaskSerializer(PunctTaskSerializer):
    pass