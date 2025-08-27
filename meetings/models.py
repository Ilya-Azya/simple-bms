from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


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

    def clean(self):
        if self.end_at <= self.start_at:
            raise ValidationError("End of meeting should be later than start")

        overlap = Meeting.objects.filter(
            Q(team=self.team),
            Q(start_at__lt=self.end_at),
            Q(end_at__gt=self.start_at),
        )
        if self.pk:
            overlap = overlap.exclude(pk=self.pk)

        if overlap.exists():
            raise ValidationError("Intersects with another meeting")

        if self.pk:
            participants = self.participants.all()
        else:
            participants = getattr(self, "_participants_for_validation", [])

        for user in participants:
            u_qs = Meeting.objects.filter(
                participants=user,
                start_at__lt=self.end_at,
                end_at__gt=self.start_at,
            )
            if self.pk:
                u_qs = u_qs.exclude(pk=self.pk)
            if u_qs.exists():
                raise ValidationError(f"User {user.email} has another meeting at that time")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
