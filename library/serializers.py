from django.utils import timezone
from rest_framework import serializers

from .models import Author, Book, IssuedBook, Member


class AuthorSerializer(serializers.ModelSerializer):
    book_count = serializers.IntegerField(source="books.count", read_only=True)

    class Meta:
        model = Author
        fields = ["id", "name", "bio", "book_count"]


class BookSerializer(serializers.ModelSerializer):
    authors = serializers.PrimaryKeyRelatedField(
        queryset=Author.objects.all(), many=True
    )
    author_names = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "isbn",
            "authors",
            "author_names",
            "genre",
            "published_date",
            "total_copies",
            "available_copies",
            "is_available",
            "created_at",
        ]
        read_only_fields = ["available_copies", "created_at"]

    def get_author_names(self, obj):
        return [a.name for a in obj.authors.all()]

    def validate(self, attrs):
        total = attrs.get(
            "total_copies", getattr(self.instance, "total_copies", None)
        )
        if total is not None and total < 0:
            raise serializers.ValidationError(
                {"total_copies": "Total copies cannot be negative."}
            )
        return attrs

    def create(self, validated_data):
        authors = validated_data.pop("authors")
        validated_data["available_copies"] = validated_data.get("total_copies", 1)
        book = Book.objects.create(**validated_data)
        book.authors.set(authors)
        return book

    def update(self, instance, validated_data):
        # If total_copies is increased/decreased, adjust available_copies
        # by the same delta so currently-issued copies stay consistent.
        new_total = validated_data.get("total_copies")
        if new_total is not None and new_total != instance.total_copies:
            delta = new_total - instance.total_copies
            instance.available_copies = max(instance.available_copies + delta, 0)
        authors = validated_data.pop("authors", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if authors is not None:
            instance.authors.set(authors)
        return instance


class MemberSerializer(serializers.ModelSerializer):
    active_loans = serializers.SerializerMethodField()

    class Meta:
        model = Member
        fields = [
            "id",
            "name",
            "email",
            "phone",
            "joined_date",
            "is_active",
            "active_loans",
        ]
        read_only_fields = ["joined_date"]

    def get_active_loans(self, obj):
        return obj.issues.filter(return_date__isnull=True).count()


class IssuedBookSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source="book.title", read_only=True)
    member_name = serializers.CharField(source="member.name", read_only=True)
    is_returned = serializers.BooleanField(read_only=True)
    overdue_days = serializers.IntegerField(read_only=True)
    late_fee = serializers.IntegerField(read_only=True)

    class Meta:
        model = IssuedBook
        fields = [
            "id",
            "book",
            "book_title",
            "member",
            "member_name",
            "issue_date",
            "due_date",
            "return_date",
            "is_returned",
            "overdue_days",
            "late_fee",
        ]
        read_only_fields = ["due_date", "return_date"]

    def validate(self, attrs):
        book = attrs.get("book")
        member = attrs.get("member")

        if not member.is_active:
            raise serializers.ValidationError(
                {"member": "This member is not active and cannot borrow books."}
            )

        if not book.is_available:
            raise serializers.ValidationError(
                {"book": "No copies of this book are currently available."}
            )

        duplicate = IssuedBook.objects.filter(
            book=book, member=member, return_date__isnull=True
        ).exists()
        if duplicate:
            raise serializers.ValidationError(
                "This member already has an active loan for this book."
            )

        return attrs

    def create(self, validated_data):
        book = validated_data["book"]
        book.available_copies = max(book.available_copies - 1, 0)
        book.save(update_fields=["available_copies"])
        return super().create(validated_data)
