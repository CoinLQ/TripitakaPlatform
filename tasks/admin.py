from django.contrib import admin

from .models import CompareReel, CompareSeg, BatchTask, Task, CorrectSeg, ReelDiff, DiffSeg, DiffSegText

admin.site.register(CompareReel)
admin.site.register(CompareSeg)
admin.site.register(BatchTask)
admin.site.register(Task)
admin.site.register(CorrectSeg)
admin.site.register(ReelDiff)
admin.site.register(DiffSeg)
admin.site.register(DiffSegText)
