from django.contrib import admin

from .models import Evaluation


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ("task", "user", "score", "evaluator", "created_at")
    list_filter = ("score", "created_at")
    search_fields = ("task__title", "user__email", "evaluator__email")
