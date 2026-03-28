from rest_framework import serializers
from .models import Book, Author, Category, IssueBook
from django.contrib.auth.models import User
from .models import ActivityLog

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = '__all__'

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'

# class IssueBookSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = IssueBook
#         fields = '__all__'


class IssueBookSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source='book.title', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = IssueBook
        fields = ['id', 'book', 'user', 'issue_timestamp', 'return_timestamp', 'returned', 'book_title', 'user_name', 'email']


class ActivityLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = ActivityLog
        fields = ['id', 'user_name', 'action', 'target', 'timestamp']

