from api.views import mixin
from .models import Test
from .serializer import TestSerializer
from rest_framework import viewsets

class TestViewSet(mixin.CreateUpdateMixin, viewsets.ModelViewSet):
    queryset = Test.objects.all()
    serializer_class = TestSerializer
