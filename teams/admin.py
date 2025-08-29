from django.contrib import admin
from .models import Team, TeamMembership


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "invite_code", "created_at")
    list_filter = ("name", "created_at")
    search_fields = ("name", "invite_code")


@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):
    list_display = ("team", "user", "role", "joined_at")
    list_filter = ("team", "role")
    search_fields = ("team__name", "user__username", "user__email")
