from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuthorViewSet, CategoryViewSet, BookViewSet, IssueBookViewSet, ActivityLogViewSet, ChangePasswordAPIView

router = DefaultRouter()
router.register('authors', AuthorViewSet)
router.register('categories', CategoryViewSet)
router.register('books', BookViewSet)
router.register('issue-books', IssueBookViewSet)
router.register('activity-logs', ActivityLogViewSet, basename='activity-logs')

urlpatterns = [
    path('', include(router.urls)),
    path("change-password/", ChangePasswordAPIView.as_view(), name="change-password-api"),
]
