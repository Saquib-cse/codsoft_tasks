from django.contrib import admin

from .models import Contact


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone_number', 'company', 'owner', 'created_at')
    list_filter = ('company',)
    search_fields = ('name', 'email', 'phone_number')
