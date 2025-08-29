from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect

from core.permissions import (
    can_edit_task,
    can_manage_task,
    is_team_manager,
    is_team_admin,
    is_admin,
)
from .forms import TaskForm, CommentForm
from .models import Task


def task_list(request):
    user = request.user

    if not user.is_authenticated:
        raise PermissionDenied("You should be authenticated")

    if user.role == "Team Admin":
        tasks = Task.objects.all().order_by("-created_at")
    else:
        teams = user.teams.all()
        tasks = Task.objects.filter(team__in=teams).order_by("-created_at")

    paginator = Paginator(tasks, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    tasks_with_perms = []
    for task in page_obj:
        can_eval = (
            is_admin(user)
            or is_team_admin(user, task.team)
            or is_team_manager(user, task.team)
        )
        tasks_with_perms.append((task, can_eval))

    can_create_task = (
        is_admin(user)
        or is_team_admin(user, user.default_team)
        or is_team_manager(user, user.default_team)
    )
    context = {
        "tasks_with_perms": tasks_with_perms,
        "can_create_task": can_create_task,
        "page_obj": page_obj,
    }
    return render(request, "tasks/task_list.html", context)


def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk)

    if task.team not in request.user.teams.all() and not is_admin(request.user):
        raise PermissionDenied("You do not have access to this task")

    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.task = task
            comment.author = request.user
            comment.save()
            return redirect("tasks:task_detail", pk=task.pk)
    else:
        form = CommentForm()

    can_eval_task = (
        is_admin(request.user)
        or is_team_admin(request.user, task.team)
        or is_team_manager(request.user, task.team)
    )
    can_change_status = can_eval_task

    can_delete_change = is_admin(request.user) or task.created_by == request.user

    context = {
        "task": task,
        "comments": task.comments.all(),
        "form": form,
        "can_eval_task": can_eval_task,
        "can_change_status": can_change_status,
        "can_delete_change": can_delete_change,
    }
    return render(request, "tasks/task_detail.html", context)


def task_create(request):
    user = request.user

    if not is_admin(user):
        raise PermissionDenied("You do not have permissions for create a task")

    if request.method == "POST":
        form = TaskForm(request.POST, user=user, editing=False)
        if form.is_valid():
            task = form.save(commit=False)
            team = task.team

            if not (
                is_admin(user)
                or is_team_admin(user, team)
                or is_team_manager(user, team)
            ):
                raise PermissionDenied(
                    "You do not have permissions to create a task in this team"
                )

            task.created_by = user
            task.save()
            return redirect("tasks:task_list")
    else:
        form = TaskForm(user=user, editing=False)
    return render(request, "tasks/task_form.html", {"form": form})


def task_edit(request, pk):
    task = get_object_or_404(Task, pk=pk)

    if not (can_edit_task(request.user, task) or is_admin(request.user)):
        raise PermissionDenied("You have not permissions for edit this task")

    if request.method == "POST":
        form = TaskForm(request.POST, instance=task, user=request.user, editing=True)
        if form.is_valid():
            form.save()
            return redirect("tasks:task_detail", pk=task.pk)
    else:
        form = TaskForm(instance=task, user=request.user, editing=True)
    return render(request, "tasks/task_form.html", {"form": form})


def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)

    if not (can_manage_task(request.user, task) or is_admin(request.user)):
        raise PermissionDenied("You have not permissions for delete this task")

    if request.method == "POST":
        task.delete()
        return redirect("tasks:task_list")
    return render(request, "tasks/task_confirm_delete.html", {"task": task})


def change_status(request, pk):
    task = get_object_or_404(Task, pk=pk)

    if not (
        is_admin(request.user)
        or is_team_admin(request.user, task.team)
        or is_team_manager(request.user, task.team)
    ):
        raise PermissionDenied("You have not permissions for change status")

    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status:
            task.status = new_status
            task.save()
            messages.success(request, f"Status changed on {new_status}")

    return redirect("tasks:task_detail", pk=pk)
