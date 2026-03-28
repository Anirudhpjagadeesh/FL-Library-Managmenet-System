from rest_framework import viewsets, permissions, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import date
from django.utils import timezone
from .models import Book, Author, Category, IssueBook, ActivityLog
from .serializers import *
from .pagination import IssueBookPagination

# ------------------- VIEWS -------------------

def home(request):
    """Dashboard stats for home page"""
    total_books = Book.objects.count()
    available_books = Book.objects.filter(available_copies__gt=0).count()
    issued_books = IssueBook.objects.filter(returned=False).count()
    total_members = User.objects.count()

    context = {
        'total_books': total_books,
        'available_books': available_books,
        'issued_books': issued_books,
        'total_members': total_members,
    }

    return render(request, 'home.html', context)

# views.py
def profile(request):
    return render(request, "profile.html")


def login_view(request): 
    return render(request, "login.html")


def register_view(request): 
    return render(request, "register.html")


def change_password(request): 
    return render(request, "change_password.html")


def dashboard(request): 
    """Dashboard stats for home page"""
    total_books = Book.objects.count()
    available_books = Book.objects.filter(available_copies__gt=0).count()
    issued_books = IssueBook.objects.filter(returned=False).count()
    total_members = User.objects.count()

    context = {
        'total_books': total_books,
        'available_books': available_books,
        'issued_books': issued_books,
        'total_members': total_members,
    }
    return render(request, "dashboard.html", context)


def books(request): 
    return render(request, "books.html")


def book_create(request):
    return render(request, "book_form.html")


def book_edit(request, id):
    return render(request, "book_form.html")


def issue_book(request): 
    return render(request, "issue_book.html")


def issued_book(request): 
    return render(request, "issued_books.html")


def activity_log(request): 
    return render(request, "activity_logs.html")


# ------------------- UTILITY -------------------

def log_activity(user, action, target=""):
    """Create an activity log entry"""
    ActivityLog.objects.create(user=user, action=action, target=target)


# ------------------- API VIEWSETS -------------------

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """Users API: read-only for dropdowns"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None



class IsAdminOrReadOnly(permissions.BasePermission):
    """Admin users can create/update/delete, others read-only"""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsAdminOrReadOnly]


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = None

    def get_or_create_author_category(self, request_data):
        author_name = request_data.get('author_name')
        category_name = request_data.get('category_name')
        
        author, _ = Author.objects.get_or_create(name=author_name)
        category, _ = Category.objects.get_or_create(name=category_name)
        
        return author, category

    def create(self, request, *args, **kwargs):
        """
        Custom create to handle error responses correctly for the frontend
        """
        try:
            title = request.data.get('title')
            if not title:
                return Response({"error": "Title is required"}, status=status.HTTP_400_BAD_REQUEST)

            if Book.objects.filter(title__iexact=title).exists():
                return Response(
                    {"error": "A book with this title already exists."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            author, category = self.get_or_create_author_category(request.data)
            
            try:
                total_copies = int(request.data.get('total_copies', 1))
            except (ValueError, TypeError):
                total_copies = 1

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            book = serializer.save(
                author=author,
                category=category,
                available_copies=total_copies
            )
            
            log_activity(
                user=self.request.user,
                action="Created Book",
                target=f"Book: {book.title}"
            )
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            error_msg = "Validation error"
            if isinstance(e.detail, dict):
                error_msg = e.detail.get('error', e.detail.get('non_field_errors', [str(e.detail)]))
                if isinstance(error_msg, list): error_msg = error_msg[0]
            return Response({"error": str(error_msg)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Server Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        try:
            author, category = self.get_or_create_author_category(request.data)
            
            # Adjust available_copies based on change in total_copies
            try:
                new_total = int(request.data.get('total_copies', instance.total_copies))
            except (ValueError, TypeError):
                new_total = instance.total_copies
                
            diff = new_total - instance.total_copies
            new_available = instance.available_copies + diff
            
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            book = serializer.save(
                author=author,
                category=category,
                available_copies=new_available
            )
            
            log_activity(
                user=self.request.user,
                action="Updated Book",
                target=f"Book: {book.title}"
            )
            
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def perform_destroy(self, instance):
        log_activity(
            user=self.request.user,
            action="Deleted Book",
            target=f"Book: {instance.title}"
        )
        instance.delete()



from rest_framework.exceptions import ValidationError

class IssueBookViewSet(viewsets.ModelViewSet):
    queryset = IssueBook.objects.select_related('book', 'user').order_by('-issue_timestamp')
    # queryset = IssueBook.objects.all()
    serializer_class = IssueBookSerializer
    pagination_class = IssueBookPagination

    def create(self, request, *args, **kwargs):
        """
        Custom create to handle error responses correctly for the frontend
        """
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except ValidationError as e:
            # Extract the error message from the exception
            error_msg = "Validation error"
            if isinstance(e.detail, dict):
                error_msg = e.detail.get('error', [str(e.detail)])
                if isinstance(error_msg, list): error_msg = error_msg[0]
            elif isinstance(e.detail, list):
                error_msg = e.detail[0]
            
            return Response({"error": error_msg}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        """Issue a book and decrease available copies"""
        book = serializer.validated_data['book']

        if book.available_copies <= 0:
            raise ValidationError({"error": "No available copies left"})

        book.available_copies -= 1
        book.save()

        issue = serializer.save(
            returned=False
        )

        log_activity(
            user=self.request.user,
            action="Issued Book",
            target=f"Book: {issue.book.title} to User: {issue.user.username}"
        )

    def partial_update(self, request, *args, **kwargs):
        """
        Return or Re-issue a book (Undo Return)
        """
        instance = self.get_object()
        returned = request.data.get("returned", None)

        if returned is not None:
            # Case 1: Marking as returned
            if returned is True and not instance.returned:
                instance.returned = True
                instance.return_timestamp = timezone.now()
                instance.book.available_copies += 1
                
                log_activity(
                    user=self.request.user,
                    action="Returned Book",
                    target=f"Book: {instance.book.title} by User: {instance.user.username}"
                )

            # Case 2: Undo return (Mistake correction)
            elif returned is False and instance.returned:
                if instance.book.available_copies <= 0:
                    return Response(
                        {"error": "Cannot undo return. No copies available to re-issue."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                instance.returned = False
                instance.return_timestamp = None
                instance.book.available_copies -= 1
                
                log_activity(
                    user=self.request.user,
                    action="Undo Return (Re-issued)",
                    target=f"Book: {instance.book.title} to User: {instance.user.username}"
                )

            instance.book.save()
            instance.save()

            serializer = self.get_serializer(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)

        return super().partial_update(request, *args, **kwargs)


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ActivityLog.objects.all().order_by('-timestamp')
    serializer_class = ActivityLogSerializer
    permission_classes = [permissions.IsAuthenticated]

class ChangePasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        if not old_password or not new_password or not confirm_password:
            return Response(
                {"error": "All fields are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not user.check_password(old_password):
            return Response(
                {"error": "Old password is incorrect"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_password != confirm_password:
            return Response(
                {"error": "New passwords do not match"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(new_password) < 6:
            return Response(
                {"error": "Password must be at least 6 characters"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()

        return Response(
            {"message": "Password changed successfully"},
            status=status.HTTP_200_OK
        )
