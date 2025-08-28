from teams.models import TeamMembership


def is_admin(user):
    return user.role == "Team Admin" or user.role == "team admin"


def has_role_in_team(user, team, roles):
    return TeamMembership.objects.filter(user=user, team=team, role__in=roles).exists()


def is_team_admin(user, team):
    return has_role_in_team(user, team, [TeamMembership.Role.ADMIN])


def is_team_manager(user, team):
    return has_role_in_team(user, team, [TeamMembership.Role.MANAGER])


def can_edit_task(user, task):
    return (
            task.created_by == user
            or is_team_admin(user, task.team)
            or is_team_manager(user, task.team)
    )


def can_manage_task(user, task):
    return is_team_admin(user, task.team)
