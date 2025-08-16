from django import forms

from .models import Task, Comment


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["title", "description", "team", "status", "deadline"]
        widgets = {
            "deadline": forms.DateInput(attrs={"type": "date"}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["text"]
        widgets = {
            "text": forms.Textarea(attrs={"rows": 2, "placeholder": "Write comment..."})
        }
