from django import forms
from django.core.exceptions import ValidationError

from teams.models import Team
from .models import Meeting


class MeetingForm(forms.ModelForm):
    class Meta:
        model = Meeting
        fields = ("title", "description", "team", "participants", "start_at", "end_at")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        team_val = None
        data = args[0] if args else None
        if data and hasattr(data, "get"):
            team_val = data.get("team")
        if not team_val and self.instance and self.instance.pk:
            team_val = self.instance.team_id
        if team_val:
            try:
                team = Team.objects.get(pk=team_val)
                self.fields["participants"].queryset = team.members.all()
            except Team.DoesNotExist:
                pass

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_at")
        end = cleaned.get("end_at")
        team = cleaned.get("team")
        participants = cleaned.get("participants")

        if start is None or end is None:
            raise ValidationError("start_at and end_at are required")

        if start >= end:
            raise ValidationError("end_at should be later start_at")

        qs = Meeting.objects.filter(team=team)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.filter(start_at__lt=end, end_at__gt=start).exists():
            raise ValidationError("At this time the team already has a meeting")

        if participants:
            for u in participants:
                u_qs = Meeting.objects.filter(participants=u)
                if self.instance and self.instance.pk:
                    u_qs = u_qs.exclude(pk=self.instance.pk)
                if u_qs.filter(start_at__lt=end, end_at__gt=start).exists():
                    raise ValidationError(f"Member {u.email} has an overlapping meeting")

        return cleaned
