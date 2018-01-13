from django.contrib import admin

from .models import LQSutra, Tripitaka, Sutra, LQReel, Reel, Page

admin.site.register(Tripitaka)
admin.site.register(LQSutra)
admin.site.register(Sutra)
admin.site.register(LQReel)
admin.site.register(Reel)
admin.site.register(Page)