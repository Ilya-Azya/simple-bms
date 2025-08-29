from django import forms

from core.permissions import is_admin
from teams.models import Team
from .models import Task, Comment


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["title", "description", "team", "deadline", "status"]
        widgets = {
            "deadline": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, editing=False, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if user:
            if is_admin(user):
                self.fields["team"].queryset = Team.objects.all()
            else:
                self.fields["team"].queryset = user.teams.all()
        if not editing:
            self.fields.pop("status", None)


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["text"]
        widgets = {
            "text": forms.Textarea(attrs={"rows": 2, "placeholder": "Write comment..."})
        }
