from django.conf import settings
from django.db import models


class Meeting(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    team = models.ForeignKey("teams.Team", on_delete=models.CASCADE, related_name="meetings")
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="meetings")
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL,
                                   related_name="created_meetings")

    class Meta:
        ordering = ("-start_at",)
        indexes = [
            models.Index(fields=["team", "start_at", "end_at"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.start_at.isoformat()} — {self.end_at.isoformat()})"
