def is_admin(user):
    return user.is_authenticated and user.role == "Team Admin"


def is_manager(user):
    return user.is_authenticated and user.role == "Manager"


def can_manage_task(user, task):
    if not user.is_authenticated:
        return False
    if is_admin(user):
        return True
    if is_manager(user) and user.default_team_id == task.team_id:
        return True
    return False


def can_edit_task(user, task):
    if not user.is_authenticated:
        return False
    if is_admin(user):
        return True
    if task.created_by_id == user.id:
        return True
    return False
