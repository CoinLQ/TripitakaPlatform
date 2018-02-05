from django.shortcuts import render
from rest_framework import mixins, viewsets
from rest_framework.decorators import detail_route, list_route
from tdata.models import *
from tdata.serializer import PageSerializer

class PageViewSet(viewsets.ReadOnlyModelViewSet, mixins.ListModelMixin):
    queryset = Page.objects.all()
    serializer_class = PageSerializer
    permission_classes = []