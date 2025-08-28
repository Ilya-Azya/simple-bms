from django.conf import settings
from django.db import models
from django.utils.crypto import get_random_string

User = settings.AUTH_USER_MODEL


class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    invite_code = models.CharField(max_length=20, unique=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="TeamMembership",
        related_name="teams"
    )

    def save(self, *args, **kwargs):
        if not self.invite_code:
            code = get_random_string(8)
            while Team.objects.filter(invite_code=code).exists():
                code = get_random_string(8)
            self.invite_code = code
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}"


class TeamMembership(models.Model):
    class Role(models.TextChoices):
        MEMBER = "Member", "member"
        MANAGER = "Manager", "manager"
        ADMIN = "Admin", "admin"

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="team_membership")
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("team", "user")

    def __str__(self):
        return f"{self.user} in {self.team} as {self.role}"
