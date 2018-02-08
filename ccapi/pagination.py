from django.core.paginator import EmptyPage
from rest_framework import pagination
from rest_framework.response import Response
try:
    from rest_framework.compat import OrderedDict
except ImportError:
    from collections import OrderedDict


class StandardPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 10000

    def get_paginated_response(self, data):
        try:
            previous_page_number = self.page.previous_page_number()
        except EmptyPage:
            previous_page_number = None

        try:
            next_page_number = self.page.next_page_number()
        except EmptyPage:
            next_page_number = None

        return Response({
            'pagination': {
                'previous_page': previous_page_number,
                'next_page': next_page_number,
                'start_index': self.page.start_index(),
                'end_index': self.page.end_index(),
                'total_entries': self.page.paginator.count,
                'total_pages': self.page.paginator.num_pages,
                'page_size': self.page.paginator.per_page,
                'page': self.page.number,
            },
            'models': data,
        })


class CommonPageNumberPagination(pagination.PageNumberPagination):
    def get_paginated_response(self, data):
        count = self.page.paginator.count
        total_page = self.page.paginator.num_pages
        return Response(OrderedDict([
            ('per_page', self.page_size),
            ('current_page', self.page.number),
            ('total_page', total_page),
            ('count', count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))
