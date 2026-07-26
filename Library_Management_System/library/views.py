from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Author, Book, IssuedBook, Member
from .serializers import (
    AuthorSerializer,
    BookSerializer,
    IssuedBookSerializer,
    MemberSerializer,
)


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all().prefetch_related("authors")
    serializer_class = BookSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["genre", "authors"]
    search_fields = ["title", "isbn", "authors__name", "genre"]
    ordering_fields = ["title", "published_date", "available_copies", "created_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        available = self.request.query_params.get("available")
        if available == "true":
            qs = qs.filter(available_copies__gt=0)
        elif available == "false":
            qs = qs.filter(available_copies=0)
        return qs


class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_active"]
    search_fields = ["name", "email", "phone"]
    ordering_fields = ["name", "joined_date"]


class IssuedBookViewSet(viewsets.ModelViewSet):
    queryset = IssuedBook.objects.select_related("book", "member").all()
    serializer_class = IssuedBookSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["book", "member"]
    ordering_fields = ["issue_date", "due_date"]
    http_method_names = ["get", "post", "head", "options"]  # issues are created/returned, not edited/deleted

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get("status")
        if status_param == "active":
            qs = qs.filter(return_date__isnull=True)
        elif status_param == "returned":
            qs = qs.filter(return_date__isnull=False)
        elif status_param == "overdue":
            qs = qs.filter(return_date__isnull=True, due_date__lt=timezone.localdate())
        return qs

    @action(detail=True, methods=["post"])
    def return_book(self, request, pk=None):
        issued = self.get_object()
        if issued.is_returned:
            return Response(
                {"detail": "This book has already been returned."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        issued.return_date = timezone.localdate()
        issued.save(update_fields=["return_date"])

        book = issued.book
        book.available_copies = min(book.available_copies + 1, book.total_copies)
        book.save(update_fields=["available_copies"])

        serializer = self.get_serializer(issued)
        return Response(
            {
                "detail": "Book returned successfully.",
                "overdue_days": issued.overdue_days,
                "late_fee": issued.late_fee,
                "issue": serializer.data,
            }
        )


class ReportsView(viewsets.ViewSet):
    """Read-only endpoints for library-wide reports (bonus requirement)."""

    def list(self, request):
        total_books = Book.objects.count()
        total_copies = sum(b.total_copies for b in Book.objects.all())
        available_copies = sum(b.available_copies for b in Book.objects.all())
        active_loans = IssuedBook.objects.filter(return_date__isnull=True)
        overdue_loans = active_loans.filter(due_date__lt=timezone.localdate())

        return Response(
            {
                "total_books": total_books,
                "total_copies": total_copies,
                "available_copies": available_copies,
                "total_members": Member.objects.count(),
                "active_loans": active_loans.count(),
                "overdue_loans": overdue_loans.count(),
                "total_outstanding_late_fees": sum(
                    loan.late_fee for loan in overdue_loans
                ),
            }
        )

    @action(detail=False, methods=["get"])
    def overdue(self, request):
        overdue_loans = IssuedBook.objects.select_related("book", "member").filter(
            return_date__isnull=True, due_date__lt=timezone.localdate()
        )
        serializer = IssuedBookSerializer(overdue_loans, many=True)
        return Response(serializer.data)
