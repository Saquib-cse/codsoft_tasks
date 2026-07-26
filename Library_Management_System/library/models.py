from datetime import timedelta

from django.db import models
from django.utils import timezone


class Author(models.Model):
    name = models.CharField(max_length=200)
    bio = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=255)
    isbn = models.CharField(max_length=20, unique=True)
    authors = models.ManyToManyField(Author, related_name="books")
    genre = models.CharField(max_length=100, blank=True)
    published_date = models.DateField(null=True, blank=True)
    total_copies = models.PositiveIntegerField(default=1)
    available_copies = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

    @property
    def is_available(self):
        return self.available_copies > 0


class Member(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    joined_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class IssuedBook(models.Model):
    LOAN_PERIOD_DAYS = 14
    LATE_FEE_PER_DAY = 5  # currency units per overdue day

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="issues")
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="issues")
    issue_date = models.DateField(default=timezone.localdate)
    due_date = models.DateField(blank=True, null=True)
    return_date = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ["-issue_date"]

    def save(self, *args, **kwargs):
        if not self.due_date:
            self.due_date = self.issue_date + timedelta(days=self.LOAN_PERIOD_DAYS)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.book.title} -> {self.member.name}"

    @property
    def is_returned(self):
        return self.return_date is not None

    @property
    def overdue_days(self):
        end = self.return_date or timezone.localdate()
        delta = (end - self.due_date).days
        return max(delta, 0)

    @property
    def late_fee(self):
        return self.overdue_days * self.LATE_FEE_PER_DAY
