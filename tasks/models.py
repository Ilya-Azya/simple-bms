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
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_task")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="tasks")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    deadline = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.status})"