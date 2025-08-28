from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from core.permissions import is_admin
from .forms import TeamForm
from .models import Team, TeamMembership


@login_required
def team_list(request):
    if not is_admin(request.user):
        messages.error(request, "You have not permissions for create a team")
        return redirect('tasks:task_list')

    teams = Team.objects.all()
    return render(request, 'teams/team_list.html', {'teams': teams})


@login_required
def create_team(request):
    if not is_admin(request.user):
        messages.error(request, "You have not permissions for create a team")
        return redirect('teams:team_list')

    invite_code = None
    if request.method == 'POST':
        form = TeamForm(request.POST)
        if form.is_valid():
            team = form.save()
            invite_code = team.invite_code
    else:
        form = TeamForm()

    return render(request, 'teams/team_form.html', {'form': form, 'invite_code': invite_code})


def join_team(request):
    if request.method == "POST":
        code = request.POST.get("code")
        team = Team.objects.filter(invite_code=code).first()
        if not team:
            messages.error(request, "Команда не найдена")
        else:
            membership, created = TeamMembership.objects.get_or_create(
                team=team,
                user=request.user,
                defaults={"role": TeamMembership.Role.MEMBER}
            )
            if created:
                messages.success(request, f"Вы присоединились к {team.name}")
            else:
                messages.info(request, f"Вы уже состоите в команде {team.name}")

            request.user.default_team = team
            request.user.save()

            return redirect("home")

    return render(request, "teams/join.html")
