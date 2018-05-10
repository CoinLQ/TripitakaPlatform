from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse, Http404
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.conf import settings

from rest_framework import mixins, viewsets, generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from tdata.models import *
from tasks.models import *
from jkapi.serializers import *
from jkapi.permissions import *

import json, re




class MarkTaskDetail(APIView):
    permission_classes = (IsTaskPickedByCurrentUser, )
    
    def get(self, request, task_id, format=None):
        base_text = re.compile('[pb\n]').sub("\n", self.task.mark.reeltext.text)
        
        response = {
            'task_id': task_id,
            'status': self.task.status,
            'base_text': base_text,
            
            }
        return Response(response)
