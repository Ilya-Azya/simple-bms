from django import forms

from core.permissions import is_admin
from teams.models import Team
from .models import Meeting


class MeetingForm(forms.ModelForm):
    class Meta:
        model = Meeting
        fields = ("title", "description", "team", "participants", "start_at", "end_at")

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        team_val = None
        data = args[0] if args else None
        if data and hasattr(data, "get"):
            team_val = data.get("team")
        elif self.instance and self.instance.pk:
            team_val = self.instance.team_id

        if team_val:
            try:
                team = Team.objects.get(pk=team_val)
                self.fields["participants"].queryset = team.members.all()
            except Team.DoesNotExist:
                pass

        if self.user and not self.user.is_superuser and not is_admin(self.user):
            self.fields["team"].queryset = self.user.teams.all()
