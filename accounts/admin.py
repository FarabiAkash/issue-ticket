from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Role", {"fields": ("role", "company")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Role", {"fields": ("role", "company")}),
    )
    list_display = ("username", "email", "role", "company", "is_active", "is_staff")
    list_filter = ("role", "is_active", "is_staff")
