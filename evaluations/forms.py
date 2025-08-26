from django import forms
from django.core.exceptions import ValidationError

from .models import Evaluation


class EvaluationForm(forms.ModelForm):
    class Meta:
        model = Evaluation
        fields = ("score", "comment")
        widgets = {
            "score": forms.NumberInput(attrs={"min": 1, "max": 5}),
            "comment": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_score(self):
        score = self.cleaned_data.get("score")
        if score is None or not (1 <= score <= 5):
            raise ValidationError("Оценка должна быть целым числом от 1 до 5.")
        return score
