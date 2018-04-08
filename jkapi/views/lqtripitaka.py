
from rest_framework import viewsets
from rest_framework import pagination
from tdata.models import LQSutra
from tdata.serializer import LQSutraSerializer

class LQSutraResultsSetPagination(pagination.PageNumberPagination):
    page_size = 30

class LQSutraViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LQSutra.objects.all()
    serializer_class = LQSutraSerializer
    pagination_class = LQSutraResultsSetPagination