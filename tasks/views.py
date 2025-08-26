from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404, redirect

from core.permissions import is_admin, is_manager, can_edit_task, can_manage_task
from .forms import TaskForm, CommentForm
from .models import Task


def task_list(request):
    user = request.user

    if not user.is_authenticated:
        raise PermissionDenied("You should be authenticated")

    if is_admin(user) or is_manager(user):
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


def task_create(request):
    user = request.user

    if not (is_manager(user) or is_admin(user)):
        raise PermissionDenied("You do not have permissions for create a task")

    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = user
            task.team = user.default_team
            task.save()
            return redirect("tasks:task_list")
    else:
        form = TaskForm()
    return render(request, "tasks/task_form.html", {"form": form})


def task_edit(request, pk):
    task = get_object_or_404(Task, pk=pk, team=request.user.default_team)

    if not can_edit_task(request.user, task):
        raise PermissionDenied("You have not permissions for edit this task")

    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect("tasks:task_detail", pk=task.pk)
    else:
        form = TaskForm(instance=task)
    return render(request, "tasks/task_form.html", {"form": form})


def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, team=request.user.default_team)

    if not can_manage_task(request.user, task):
        raise PermissionDenied("You have not permissions for delete this task")

    if request.method == "POST":
        task.delete()
        return redirect("tasks:task_list")
    return render(request, "tasks/task_confirm_delete.html", {"task": task})
