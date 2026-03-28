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
    out_of_stock = Book.objects.filter(available_copies=0).count()

    context = {
        'total_books': total_books,
        'available_books': available_books,
        'issued_books': issued_books,
        'total_members': total_members,
        'out_of_stock': out_of_stock
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
    out_of_stock = Book.objects.filter(available_copies=0).count()

    context = {
        'total_books': total_books,
        'available_books': available_books,
        'issued_books': issued_books,
        'total_members': total_members,
        'out_of_stock': out_of_stock
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


    def create(self, request, *args, **kwargs):
        title = request.data.get('title')
        if Book.objects.filter(title__iexact=title).exists():
            return Response(
                {"error": "A book with this title already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        book = serializer.save()
        log_activity(
            user=self.request.user,
            action="Created Book",
            target=f"Book: {book.title}"
        )

    def perform_update(self, serializer):
        book = serializer.save()
        log_activity(
            user=self.request.user,
            action="Updated Book",
            target=f"Book: {book.title}"
        )

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
