from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class GlobalRole(models.TextChoices):
        USER = "User", "user"
        MANAGER = "Manager", "manager"
        TEAM_ADMIN = "Team Admin", "team admin"

    role = models.CharField(max_length=20, choices=GlobalRole.choices, default=GlobalRole.USER,
                            help_text="Global role (not in a current command)")

    # default_team = models.ForeignKey()

    def __str__(self):
        return f"{self.username} ({self.role})"
