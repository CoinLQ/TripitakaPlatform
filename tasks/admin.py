from django.contrib import admin

from .models import CompareReel, CompareSeg, BatchTask, Task, CorrectSeg

admin.site.register(CompareReel)
admin.site.register(CompareSeg)
admin.site.register(BatchTask)
admin.site.register(Task)
admin.site.register(CorrectSeg)
# admin.site.register(SkipCharacter)
# admin.site.register(SutraText)
# admin.site.register(PunctResult)
# admin.site.register(CharFeedback)
# admin.site.register(JudgementFeedback)
