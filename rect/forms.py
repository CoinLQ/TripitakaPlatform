# -*- coding: UTF-8 -*-

from django import forms
from datetime import date
import os
import base64
from rect.models import Schedule, SliceType
import hashlib


class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ['status', 'due_at', 'remark']


class ScheduleModelForm(forms.ModelForm):
    def create(self, commit=True):
        pass

    def save(self, commit=True):
        return super(ScheduleModelForm, self).save(commit=commit)

    class Meta:
        fields = ('status', 'due_at', 'remark')
        model = Schedule
