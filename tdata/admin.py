from django.contrib import admin
from .models import Tripitaka, Volume, LQSutra, Sutra, LQReel, Reel, \
ReelOCRText, Page, Column

admin.site.register(Tripitaka)
admin.site.register(Volume)
admin.site.register(LQSutra)
admin.site.register(Sutra)
admin.site.register(LQReel)
admin.site.register(Reel)
admin.site.register(ReelOCRText)
admin.site.register(Page)
admin.site.register(Column)