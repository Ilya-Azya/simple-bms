from django import forms
from django.contrib.auth import get_user_model

from core.permissions import is_admin
from teams.models import Team
from .models import Meeting

User = get_user_model()


class MeetingForm(forms.ModelForm):
    class Meta:
        model = Meeting
        fields = ("title", "description", "team", "participants", "start_at", "end_at")

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        team_val = None
        data = kwargs.get("data")
        if data:
            team_val = data.get("team")
        elif self.instance.pk:
            team_val = self.instance.team_id

        if team_val:
            try:
                team = Team.objects.get(pk=team_val)
                self.fields["participants"].queryset = team.members.all()
            except Team.DoesNotExist:
                self.fields["participants"].queryset = User.objects.none()
        elif self.instance.pk and self.instance.team:
            self.fields["participants"].queryset = self.instance.team.members.all()
        else:
            self.fields["participants"].queryset = User.objects.none()
        if self.user and not self.user.is_superuser and not is_admin(self.user):
            self.fields["team"].queryset = self.user.teams.all()

    def clean_participants(self):
        participants = self.cleaned_data.get("participants", [])
        team = self.cleaned_data.get("team")
        if team:
            for u in participants:
                if not team.members.filter(pk=u.pk).exists():
                    raise forms.ValidationError(f"User {u.email} is not in the team")
        return participants

    def save(self, commit=True):
        meeting = super().save(commit=False)
        if commit:
            meeting.save()
            self.save_m2m()
        return meeting
