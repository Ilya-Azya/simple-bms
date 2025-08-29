from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy, reverse
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)

from core.permissions import is_admin, is_team_admin, is_team_manager
from .forms import MeetingForm
from .models import Meeting


class MeetingListView(LoginRequiredMixin, ListView):
    model = Meeting
    template_name = "meetings/meeting_list.html"
    context_object_name = "meetings"
    paginate_by = 20

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        ctx["user_perms"] = {
            m.pk: is_admin(user)
            or is_team_admin(user, m.team)
            or is_team_manager(user, m.team)
            for m in ctx["meetings"]
        }
        return ctx


class MeetingDetailView(LoginRequiredMixin, DetailView):
    model = Meeting
    template_name = "meetings/meeting_detail.html"
    context_object_name = "meeting"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting = self.get_object()
        user = self.request.user

        context["is_member"] = meeting.team.memberships.filter(user=user).exists()
        context["is_manager_or_admin"] = is_team_admin(
            user, meeting.team
        ) or is_team_manager(user, meeting.team)

        return context


class MeetingPermissionMixin:
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        user = request.user
        team = obj.team

        if not user.is_authenticated:
            raise PermissionDenied

        if not (
            is_admin(user) or is_team_admin(user, team) or is_team_manager(user, team)
        ):
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)


class MeetingCreateView(LoginRequiredMixin, CreateView):
    model = Meeting
    form_class = MeetingForm
    template_name = "meetings/meeting_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = self.request.user
        team = form.cleaned_data.get("team")

        if not (
            is_admin(user) or is_team_admin(user, team) or is_team_manager(user, team)
        ):
            raise PermissionDenied("You have no permissions for this team")

        form.instance.created_by = user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("meetings:meeting_detail", kwargs={"pk": self.object.pk})


class MeetingUpdateView(LoginRequiredMixin, MeetingPermissionMixin, UpdateView):
    model = Meeting
    form_class = MeetingForm
    template_name = "meetings/meeting_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse("meetings:meeting_detail", kwargs={"pk": self.object.pk})


class MeetingDeleteView(LoginRequiredMixin, MeetingPermissionMixin, DeleteView):
    model = Meeting
    template_name = "meetings/meeting_confirm_delete.html"
    success_url = reverse_lazy("meetings:meeting_list")
