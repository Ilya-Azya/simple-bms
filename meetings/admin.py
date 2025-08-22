from django.contrib import admin

from .models import Meeting


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ("title", "team", "start_at", "end_at", "created_by")
    list_filter = ("team",)
    search_fields = ("title", "description", "created_by__email")
