from django.contrib import messages
from django.shortcuts import render, redirect

from .models import Team


def join_team(request):
    if request.method == "POST":
        code = request.POST.get("code")
        team = Team.objects.filter(code=code).first()
        if not team:
            messages.error(request, "Команда не найдена")
        else:
            request.user.default_team = team
            request.user.save()
            messages.success(request, f"Вы присоединились к {team.name}")
            return redirect("home")
    return render(request, "teams/join.html")
