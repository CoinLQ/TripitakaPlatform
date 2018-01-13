from django import forms
from .models import TaskBase
from sutradata.models import LQSutra

class BatchTaskForm(forms.Form):
    sid = forms.CharField(label='龙泉经目经号编码')
    reel_no = forms.CharField(label='卷号', help_text='以英文逗号分隔')
    priority = forms.ChoiceField(label='优先级', choices=TaskBase.PRIORITY_CHOICES)

    def clean(self):
        cleaned_data = super().clean()
        sid = cleaned_data.get('sid')
        reel_no = cleaned_data.get('reel_no')
        try:
            reel_no_lst = reel_no.split(',')
            lqsutra = LQSutra.objects.get(pk=sid)
            for no in reel_no_lst:
                if no > lqsutra.total_reels:
                    raise forms.ValidationError('卷号格式错误')
        except:
            raise forms.ValidationError('经号错误')
