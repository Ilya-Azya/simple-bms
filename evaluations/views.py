import logging
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import CreateView, ListView, TemplateView

from accounts.models import User
from tasks.models import Task
from .forms import EvaluationForm
from .models import Evaluation

logger = logging.getLogger(__name__)


def get_task_performer(task):
    for name in ("assignee", "assigned_to", "performer", "owner", "user", "responsible"):
        if hasattr(task, name):
            try:
                val = getattr(task, name)
                if val:
                    return val
            except Exception:
                continue

    for f in task._meta.get_fields():
        try:
            remote = getattr(getattr(f, "remote_field", None), "model", None)
            if remote == User and not getattr(f, "many_to_many", False):
                try:
                    val = getattr(task, f.name)
                    if val:
                        return val
                except Exception:
                    continue
        except Exception:
            continue

    if hasattr(task, "created_by"):
        try:
            cb = getattr(task, "created_by")
            if cb:
                return cb
        except Exception:
            pass

    return None


def is_user_in_team(user, team):
    try:
        if hasattr(team, "default_users"):
            rel = getattr(team, "default_users")
            try:
                return rel.filter(pk=user.pk).exists()
            except Exception:
                try:
                    return user in rel.all()
                except Exception:
                    pass
    except Exception:
        pass

    try:
        if hasattr(team, "memberships"):
            rel = getattr(team, "memberships")
            try:
                return rel.filter(user=user).exists()
            except Exception:
                try:
                    return rel.filter(user_id=user.pk).exists()
                except Exception:
                    for m in rel.all()[:50]:
                        if getattr(m, "user", None) == user or getattr(m, "user_id", None) == user.pk:
                            return True
    except Exception:
        pass

    try:
        for f in team._meta.get_fields():
            if getattr(f, "many_to_many", False):
                remote = getattr(getattr(f, "remote_field", None), "model", None)
                if remote == User:
                    try:
                        rel = getattr(team, f.name)
                        return rel.filter(pk=user.pk).exists()
                    except Exception:
                        try:
                            return user in rel.all()
                        except Exception:
                            continue
    except Exception:
        pass
    try:
        if hasattr(user, "default_team") and getattr(user, "default_team_id", None) == getattr(team, "id", None):
            return True
    except Exception:
        pass

    return False


# ----------------- Views -----------------
class EvaluationCreateView(LoginRequiredMixin, CreateView):
    model = Evaluation
    form_class = EvaluationForm
    template_name = "evaluations/evaluation_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.task = get_object_or_404(Task, pk=kwargs.get("task_id"))
        status = getattr(self.task, "status", None)
        status_norm = str(status).strip().lower() if status is not None else ""
        done_values = ("done", "finished", "completed")
        if status_norm not in done_values:
            logger.info(
                "Evaluation blocked: task not done",
                extra={
                    "task_id": self.task.pk,
                    "status": status,
                    "status_norm": status_norm,
                    "user": getattr(request.user, "email", None),
                },
            )
            messages.error(request, "Оценивать можно только выполненные задачи.")
            return redirect("tasks:task_detail", pk=self.task.pk)

        user = request.user
        role_raw = getattr(user, "role", None)
        role_norm = str(role_raw).strip().lower() if role_raw is not None else ""
        allowed = False

        if "admin" in role_norm or "manager" in role_norm:
            allowed = True
        else:
            team = getattr(self.task, "team", None)
            membership = False
            if team is not None:
                membership = is_user_in_team(user, team)
                if membership:
                    allowed = True

        if not allowed:
            logger.info(
                "Evaluation blocked: user not allowed",
                extra={
                    "user": getattr(user, "email", None),
                    "role_raw": role_raw,
                    "role_norm": role_norm,
                    "task_id": self.task.pk,
                    "team_membership": membership,
                },
            )
            messages.error(request, "У вас нет прав оценивать эту задачу.")
            return redirect("tasks:task_detail", pk=self.task.pk)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["task_obj"] = self.task
        ctx["performer"] = get_task_performer(self.task)
        return ctx

    def form_valid(self, form):
        eval_obj = form.save(commit=False)
        eval_obj.task = self.task
        eval_obj.evaluator = self.request.user

        performer = get_task_performer(self.task)
        if performer:
            eval_obj.user = performer
        else:
            eval_obj.user = getattr(self.task, "created_by", None)

        eval_obj.save()
        messages.success(self.request, "Оценка сохранена.")
        return redirect("evaluations:my_evaluations")


class MyEvaluationsListView(LoginRequiredMixin, ListView):
    model = Evaluation
    template_name = "evaluations/my_evaluations.html"
    context_object_name = "evaluations"
    paginate_by = 20

    def get_queryset(self):
        return Evaluation.objects.filter(user=self.request.user).select_related("task", "evaluator")


class MyEvaluationAverageView(LoginRequiredMixin, TemplateView):
    template_name = "evaluations/my_average.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        qs = Evaluation.objects.filter(user=user)

        start_s = self.request.GET.get("start")
        end_s = self.request.GET.get("end")

        try:
            if start_s:
                start = datetime.fromisoformat(start_s)
            else:
                start = timezone.now() - timedelta(days=30)
            if end_s:
                end = datetime.fromisoformat(end_s)
            else:
                end = timezone.now()
        except Exception:
            start = timezone.now() - timedelta(days=30)
            end = timezone.now()

        if isinstance(start, datetime) and start.time() == datetime.min.time():
            if timezone.is_naive(start):
                start = timezone.make_aware(start)
        if isinstance(end, datetime) and end.time() == datetime.min.time():
            if timezone.is_naive(end):
                end = timezone.make_aware(end) + timedelta(days=1, seconds=-1)
            else:
                end = end + timedelta(days=1, seconds=-1)

        qs = qs.filter(created_at__gte=start, created_at__lte=end)
        agg = qs.aggregate(avg_score=Avg("score"), cnt=Count("id"))
        ctx["avg_score"] = round(agg["avg_score"], 2) if agg["avg_score"] is not None else None
        ctx["count"] = agg["cnt"]
        ctx["start"] = start
        ctx["end"] = end
        ctx["evaluations"] = qs.select_related("evaluator", "task")
        return ctx
