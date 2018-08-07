from jwt_auth.models import Staff
from django.db import models

class Test(models.Model):
    test = models.CharField(max_length=128, null=True, blank=True)
    location = models.CharField(max_length=122, null=True, blank=True)
    creator=models.ForeignKey(Staff, null=True, blank=True, on_delete=models.SET_NULL)
    creat_time = models.DateField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    updater = models.ForeignKey(Staff, null=True, blank=True, on_delete=models.SET_NULL, related_name='updater')
