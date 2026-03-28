from django.db import models
from django.contrib.auth.models import User

class Author(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Book(models.Model):
    title = models.CharField(max_length=200)
    flb_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    total_copies = models.PositiveIntegerField()
    available_copies = models.PositiveIntegerField()

    def __str__(self):
        return self.title

class IssueBook(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)

    issue_timestamp = models.DateTimeField(auto_now_add=True)  # FULL TIMESTAMP
    return_timestamp = models.DateTimeField(null=True, blank=True)

    returned = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.book.title} -> {self.user.username}"

    def __str__(self):
        return f"{self.book.title} -> {self.user.username}"
    

class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=255)  # e.g., "Created Book", "Issued Book"
    target = models.CharField(max_length=255, blank=True)  # e.g., "Book: Python 101"
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.action}"
