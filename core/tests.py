import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from core import permissions
from core.backends import EmailOrUsernameBackend
from core.context_processors import admin_status
from teams.models import Team, TeamMembership

User = get_user_model()


@pytest.mark.django_db
def test_admin_status_returns_true_for_admin_user():
    user = User.objects.create_user(
        username="admin", email="admin@test.com", password="pass", role="Team Admin"
    )
    request = RequestFactory().get("/")
    request.user = user
    result = admin_status(request)
    assert result["is_admin_user"] is True


@pytest.mark.django_db
def test_admin_status_returns_false_for_non_admin_user():
    user = User.objects.create_user(
        username="user", email="user@test.com", password="pass", role="User"
    )
    request = RequestFactory().get("/")
    request.user = user
    result = admin_status(request)
    assert result["is_admin_user"] is False


@pytest.mark.django_db
def test_backend_authenticate_with_username():
    user = User.objects.create_user(
        username="testuser", email="user@test.com", password="pass"
    )
    backend = EmailOrUsernameBackend()
    authenticated = backend.authenticate(None, username="testuser", password="pass")
    assert authenticated == user


@pytest.mark.django_db
def test_backend_authenticate_with_email():
    user = User.objects.create_user(
        username="testuser", email="user@test.com", password="pass"
    )
    backend = EmailOrUsernameBackend()
    authenticated = backend.authenticate(
        None, username="user@test.com", password="pass"
    )
    assert authenticated == user


@pytest.mark.django_db
def test_backend_authenticate_invalid_credentials():
    User.objects.create_user(
        username="testuser", email="user@test.com", password="pass"
    )
    backend = EmailOrUsernameBackend()
    assert backend.authenticate(None, username="wrong", password="pass") is None
    assert (
        backend.authenticate(None, username="user@test.com", password="wrongpass")
        is None
    )


@pytest.mark.django_db
def test_permissions_admin_and_manager():
    user_admin = User.objects.create_user(
        username="admin", email="admin@test.com", password="pass"
    )
    team = Team.objects.create(name="Team1")
    TeamMembership.objects.create(
        user=user_admin, team=team, role=TeamMembership.Role.ADMIN
    )

    task = team.tasks.create(title="Task", created_by=user_admin, team=team)

    assert permissions.is_team_admin(user_admin, team) is True
    assert permissions.can_manage_task(user_admin, task) is True


@pytest.mark.django_db
def test_permissions_manager_can_edit():
    creator = User.objects.create_user(
        username="creator", email="creator@test.com", password="pass"
    )
    manager = User.objects.create_user(
        username="manager", email="manager@test.com", password="pass"
    )
    team = Team.objects.create(name="Team1")
    TeamMembership.objects.create(
        user=manager, team=team, role=TeamMembership.Role.MANAGER
    )

    task = team.tasks.create(title="Task", created_by=creator, team=team)

    assert permissions.can_edit_task(manager, task) is True
    assert permissions.can_manage_task(manager, task) is False


@pytest.mark.django_db
def test_permissions_creator_can_edit():
    creator = User.objects.create_user(
        username="creator", email="creator@test.com", password="pass"
    )
    team = Team.objects.create(name="Team1")
    task = team.tasks.create(title="Task", created_by=creator, team=team)

    assert permissions.can_edit_task(creator, task) is True
