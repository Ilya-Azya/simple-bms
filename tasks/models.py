from django.conf import settings
from django.db import models

from accounts.models import User
from teams.models import Team


class Task(models.Model):
    class Status(models.TextChoices):
        OPEN = "Open", "open"
        IN_PROGRESS = "In Progress", "in progress"
        DONE = "Done", "done"

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_task"
    )
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="tasks")
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.OPEN
    )
    deadline = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.status})"


class Comment(models.Model):
    task = models.ForeignKey(
        "tasks.Task", on_delete=models.CASCADE, related_name="comments"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments"
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.author.username}: {self.text[:30]}"
