# admin.py
from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


class UserAdminForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Пароль", widget=forms.PasswordInput, required=False
    )
    password2 = forms.CharField(
        label="Подтверждение пароля", widget=forms.PasswordInput, required=False
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "default_team",
            "is_staff",
            "is_active",
        ]

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")
        if p1 or p2:
            if p1 != p2:
                raise forms.ValidationError("Пароли не совпадают")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        p1 = self.cleaned_data.get("password1")
        if p1:
            user.set_password(p1)
        if commit:
            user.save()
        return user


class UserAdmin(BaseUserAdmin):
    form = UserAdminForm
    add_form = UserAdminForm

    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "role",
        "default_team",
        "is_staff",
        "is_active",
    )
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("username",)

    fieldsets = (
        (None, {"fields": ("username", "email", "password1", "password2")}),
        (
            "Личная информация",
            {"fields": ("first_name", "last_name", "role", "default_team")},
        ),
        ("Права", {"fields": ("is_staff", "is_active", "groups", "user_permissions")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "password1",
                    "password2",
                    "role",
                    "default_team",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )


admin.site.register(User, UserAdmin)
