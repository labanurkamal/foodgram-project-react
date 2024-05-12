from rest_framework import pagination

from module.constants import PAGINATION_PAGE_SIZE


class PageLimitPagination(pagination.PageNumberPagination):
    page_size_query_param = 'limit'
    page_size = PAGINATION_PAGE_SIZE
