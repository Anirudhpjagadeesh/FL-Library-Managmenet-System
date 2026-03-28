from rest_framework.pagination import PageNumberPagination

class IssueBookPagination(PageNumberPagination):
    page_size = 10                 # records per page
    page_size_query_param = 'page_size'
    max_page_size = 100
