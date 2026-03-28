from django.urls import path
from .views import (
    login_view,
    register_view,
    dashboard,
    books,
    issue_book,
    book_create,
    book_edit,
    issued_book,
    activity_log,
    home,
    profile,
    change_password,
)

urlpatterns = [
    # Auth pages
    path('', login_view, name='login'),
    path('register/', register_view, name='register'),

    # Dashboard
    path('api/dashboard/', dashboard, name='dashboard'),

    # Books (Frontend – NO conflict with DRF)
    path('books-list/', books, name='books-list'),
    path('books-list/create/', book_create, name='book-create'),
    path('books/<int:id>/edit/', book_edit, name='book-edit'),

    # Issue Book
    path('issue-book/', issue_book, name='issue-book'),
    path('issued-books/', issued_book, name='issue-book'),

    path('activity-logs/', activity_log, name='activity-logs'),
    path('home/', home, name='home'),
    # urls.py
    path("profile/", profile, name="profile"),
    path("change-password/", change_password, name="change-password"),

]
