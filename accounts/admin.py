from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Roles & Teams", {"fields": ("role", "default_team")}),
    )
    list_display = ("username", "email", "role", "is_staff", "is_superuser")
    list_filter = ("username", "is_staff", "is_superuser")
