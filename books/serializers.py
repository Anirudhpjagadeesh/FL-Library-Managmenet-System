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
    author_name = serializers.CharField(source='author.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Book
        fields = ['id', 'flb_id', 'title', 'author', 'category', 'total_copies', 'available_copies', 'author_name', 'category_name']
        extra_kwargs = {
            'author': {'required': False},
            'category': {'required': False},
            'available_copies': {'required': False}
        }

# class IssueBookSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = IssueBook
#         fields = '__all__'


class IssueBookSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source='book.title', read_only=True)
    book_flb_id = serializers.CharField(source='book.flb_id', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = IssueBook
        fields = '__all__'


class ActivityLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = ActivityLog
        fields = ['id', 'user_name', 'action', 'target', 'timestamp']

