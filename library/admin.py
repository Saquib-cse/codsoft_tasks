from django.contrib import admin

from .models import Author, Book, IssuedBook, Member


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ["title", "isbn", "genre", "total_copies", "available_copies"]
    search_fields = ["title", "isbn"]
    list_filter = ["genre"]


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "is_active", "joined_date"]
    search_fields = ["name", "email"]
    list_filter = ["is_active"]


@admin.register(IssuedBook)
class IssuedBookAdmin(admin.ModelAdmin):
    list_display = ["book", "member", "issue_date", "due_date", "return_date"]
    list_filter = ["issue_date", "return_date"]
