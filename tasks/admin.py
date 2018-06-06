from django.contrib import admin

from .models import BatchTask, Task, CorrectSeg,\
ReelDiff, DiffSeg, DiffSegText, DiffSegResult, ReelCorrectText, LQReelText,\
Punct, LQPunct, JudgeFeedback, LQPunctFeedback, Mark, MarkUnit

admin.site.register(BatchTask)
admin.site.register(Task)
admin.site.register(CorrectSeg)
admin.site.register(ReelDiff)
admin.site.register(DiffSeg)
admin.site.register(DiffSegText)
admin.site.register(DiffSegResult)

class ReelCorrectTextAdmin(admin.ModelAdmin):
    search_fields = ['reel__sutra__tripitaka__name', 'reel__sutra__name', 'reel__reel_no']
admin.site.register(ReelCorrectText, ReelCorrectTextAdmin)
admin.site.register(LQReelText)
admin.site.register(Punct)
admin.site.register(LQPunct)
admin.site.register(Mark)
admin.site.register(MarkUnit)

class JudgeFeedbackAdmin(admin.ModelAdmin):
    list_display = ['lqsutra_name', 'reel_no']
admin.site.register(JudgeFeedback, JudgeFeedbackAdmin)
admin.site.register(LQPunctFeedback)