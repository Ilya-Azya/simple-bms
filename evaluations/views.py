from datetime import timedelta, datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import CreateView, ListView, TemplateView

from core.permissions import is_admin, has_role_in_team
from tasks.models import Task
from teams.models import TeamMembership
from .forms import EvaluationForm
from .models import Evaluation


class EvaluationCreateView(LoginRequiredMixin, CreateView):
    model = Evaluation
    form_class = EvaluationForm
    template_name = "evaluations/evaluation_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.task = get_object_or_404(Task, pk=kwargs.get("task_id"))

        if str(getattr(self.task, "status", "")).strip().lower() not in ("done", "finished", "completed"):
            messages.error(request, "Only completed tasks can be assessed.")
            return redirect("tasks:task_detail", pk=self.task.pk)

        user = request.user
        team = getattr(self.task, "team", None)

        allowed = False
        if is_admin(user):
            allowed = True
        elif team and has_role_in_team(user, team, [TeamMembership.Role.MANAGER, TeamMembership.Role.ADMIN]):
            allowed = True

        if not allowed:
            messages.error(request, "You do not have permission to rate this task.")
            return redirect("tasks:task_detail", pk=self.task.pk)

        if Evaluation.objects.filter(task=self.task, evaluator=user).exists():
            messages.warning(request, "You have already rated this task.")
            return redirect("tasks:task_detail", pk=self.task.pk)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["task_obj"] = self.task

        team = getattr(self.task, "team", None)
        if team:
            memberships = team.memberships.all()
            if memberships.exists():
                ctx["performers"] = [m.user for m in memberships]
            else:
                ctx["performers"] = [getattr(self.task, "assigned_to", getattr(self.task, "created_by", None))]
        else:
            ctx["performers"] = [getattr(self.task, "assigned_to", getattr(self.task, "created_by", None))]

        return ctx

    def form_valid(self, form):
        user_evaluator = self.request.user
        team = getattr(self.task, "team", None)

        if team:
            users_to_rate = [m.user for m in team.memberships.all()]
        else:
            users_to_rate = [getattr(self.task, "assigned_to", getattr(self.task, "created_by", None))]

        for u in users_to_rate:
            Evaluation.objects.create(
                task=self.task,
                evaluator=user_evaluator,
                user=u,
                score=form.cleaned_data["score"],
                comment=form.cleaned_data["comment"],
            )

        messages.success(self.request, "Оценка сохранена для всех участников.")
        return redirect("evaluations:my_evaluations")


class MyEvaluationsListView(LoginRequiredMixin, ListView):
    model = Evaluation
    template_name = "evaluations/my_evaluations.html"
    context_object_name = "evaluations"
    paginate_by = 20

    def get_queryset(self):
        return (
            Evaluation.objects.filter(user=self.request.user)
            .select_related("task", "evaluator")
        )


class MyEvaluationAverageView(LoginRequiredMixin, TemplateView):
    template_name = "evaluations/my_average.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        start_s = self.request.GET.get("start")
        end_s = self.request.GET.get("end")

        try:
            start = datetime.fromisoformat(start_s) if start_s else timezone.now() - timedelta(days=30)
            end = datetime.fromisoformat(end_s) if end_s else timezone.now()
        except ValueError:
            start = timezone.now() - timedelta(days=30)
            end = timezone.now()

        if timezone.is_naive(start):
            start = timezone.make_aware(start)
        if timezone.is_naive(end):
            end = timezone.make_aware(end) + timedelta(days=1, seconds=-1)
        else:
            end = end + timedelta(days=1, seconds=-1)

        qs = Evaluation.objects.filter(user=user, created_at__gte=start, created_at__lte=end).select_related("task",
                                                                                                             "evaluator")

        agg = qs.aggregate(avg_score=Avg("score"), cnt=Count("id"))

        ctx.update({
            "avg_score": round(agg["avg_score"], 2) if agg["avg_score"] is not None else None,
            "count": agg["cnt"],
            "start": start,
            "end": end,
            "evaluations": qs,
        })
        return ctx
