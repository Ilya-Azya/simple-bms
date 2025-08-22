from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from teams.models import TeamMembership
from .forms import MeetingForm
from .models import Meeting


class MeetingListView(LoginRequiredMixin, ListView):
    model = Meeting
    template_name = "meetings/meeting_list.html"
    context_object_name = "meetings"
    paginate_by = 20


class MeetingDetailView(LoginRequiredMixin, DetailView):
    model = Meeting
    template_name = "meetings/meeting_detail.html"
    context_object_name = "meeting"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting = self.get_object()
        user = self.request.user
        context["is_member"] = meeting.team.memberships.filter(user=user).exists()
        return context


class MeetingPermissionMixin(UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True

        obj = getattr(self, "object", None) or getattr(self, "meeting", None)
        if obj is None:
            return True

        team = obj.team
        membership = team.memberships.filter(user=user).first()
        if membership and membership.role in (TeamMembership.Role.MANAGER, TeamMembership.Role.ADMIN):
            return True

        return False


class MeetingCreateView(LoginRequiredMixin, CreateView):
    model = Meeting
    form_class = MeetingForm
    template_name = "meetings/meeting_form.html"

    def form_valid(self, form):
        user = self.request.user
        team = form.cleaned_data.get("team")

        if user.is_superuser:
            form.instance.created_by = user
            return super().form_valid(form)

        membership = team.memberships.filter(user=user).first()
        if membership and membership.role in (TeamMembership.Role.MANAGER, TeamMembership.Role.ADMIN):
            form.instance.created_by = user
            return super().form_valid(form)

        form.add_error(None, "You have no permissions for this team")
        return self.form_invalid(form)

    def get_success_url(self):
        return reverse("meetings:meeting_detail", kwargs={"pk": self.object.pk})


class MeetingUpdateView(LoginRequiredMixin, MeetingPermissionMixin, UpdateView):
    model = Meeting
    form_class = MeetingForm
    template_name = "meetings/meeting_form.html"

    def get_success_url(self):
        return reverse("meetings:meeting_detail", kwargs={"pk": self.object.pk})


class MeetingDeleteView(LoginRequiredMixin, MeetingPermissionMixin, DeleteView):
    model = Meeting
    template_name = "meetings/meeting_confirm_delete.html"
    success_url = reverse_lazy("meetings:meeting_list")
