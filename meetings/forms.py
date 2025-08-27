from django import forms

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
