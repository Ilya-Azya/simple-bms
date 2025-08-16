from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404, redirect

from .forms import TaskForm, CommentForm
from .models import Task


def team_admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied("Login required")
        if request.user.role not in ["Team Admin", "Manager"]:
            raise PermissionDenied("No permissions")
        return view_func(request, *args, **kwargs)

    return wrapper


def task_list(request):
    user = request.user
    if user.role in ["Team Admin", "Manager"]:
        tasks = Task.objects.all()
    else:
        tasks = Task.objects.filter(team=user.default_team)
    return render(request, "tasks/task_list.html", {"tasks": tasks})


def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk)
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

    return render(request, "tasks/task_detail.html", {
        "task": task,
        "comments": task.comments.all(),
        "form": form,
    })


@team_admin_required
def task_create(request):
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.team = request.user.default_team
            task.save()
            return redirect("task_list")
    else:
        form = TaskForm()
    return render(request, "tasks/task_form.html", {"form": form})


@team_admin_required
def task_edit(request, pk):
    task = get_object_or_404(Task, pk=pk, team=request.user.default_team)
    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect("task_detail", pk=task.pk)
    else:
        form = TaskForm(instance=task)
    return render(request, "tasks/task_form.html", {"form": form})


@team_admin_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, team=request.user.default_team)
    if request.method == "POST":
        task.delete()
        return redirect("task_list")
    return render(request, "tasks/task_confirm_delete.html", {"task": task})
