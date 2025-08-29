import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from tasks.forms import TaskForm, CommentForm
from tasks.models import Task
from teams.models import Team, TeamMembership

User = get_user_model()


@pytest.fixture
def team(db):
    return Team.objects.create(name="Team 1")


@pytest.fixture
def admin(db, team):
    user = User.objects.create_user(
        username="admin", email="admin@test.com", password="pass1234", role="User"
    )
    TeamMembership.objects.create(user=user, team=team, role=TeamMembership.Role.ADMIN)
    return user


@pytest.fixture
def team_admin(db, team):
    user = User.objects.create_user(
        username="team_admin",
        email="team_admin@test.com",
        password="pass1234",
        role="Team Admin",
    )
    user.teams.add(team)
    return user


@pytest.fixture
def team_manager(db, team):
    user = User.objects.create_user(
        username="manager", email="manager@test.com", password="pass1234", role="User"
    )
    TeamMembership.objects.create(
        user=user, team=team, role=TeamMembership.Role.MANAGER
    )
    return user


@pytest.fixture
def normal_user(db, team):
    user = User.objects.create_user(
        username="user1", email="user1@test.com", password="pass1234", role="User"
    )
    TeamMembership.objects.create(user=user, team=team)
    return user


@pytest.fixture
def task(admin, team):
    return Task.objects.create(title="Task", created_by=admin, team=team)


@pytest.fixture
def client_logged_in(client):
    def _login(user):
        client.login(username=user.username, password="pass1234")
        return client

    return _login


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_fixture", ["admin", "team_admin", "team_manager", "normal_user"]
)
def test_task_form_user(request, user_fixture, team):
    user = request.getfixturevalue(user_fixture)
    form_data = {
        "title": "Form Task",
        "description": "desc",
        "team": team.id,
        "status": "Open",
        "deadline": "2030-01-01",
    }
    form = TaskForm(data=form_data, user=user, editing=True)
    assert form.is_valid()


@pytest.mark.django_db
def test_comment_form_valid():
    form_data = {"text": "Comment"}
    form = CommentForm(data=form_data)
    assert form.is_valid()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_fixture", ["admin", "team_admin", "team_manager", "normal_user"]
)
def test_task_list_access(request, user_fixture, client_logged_in):
    user = request.getfixturevalue(user_fixture)
    client = client_logged_in(user)
    url = reverse("tasks:task_list")
    response = client.get(url)
    assert response.status_code == 200
    assert "tasks/task_list.html" in [t.name for t in response.templates]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_fixture", ["admin", "team_admin", "team_manager", "normal_user"]
)
def test_task_detail_access(request, user_fixture, client_logged_in, task):
    user = request.getfixturevalue(user_fixture)
    client = client_logged_in(user)
    url = reverse("tasks:task_detail", kwargs={"pk": task.pk})
    response = client.get(url)
    if user.role not in ["Admin"] and task.team not in user.teams.all():
        assert response.status_code == 403
    else:
        assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_fixture,can_create",
    [
        ("admin", False),
        ("team_admin", True),
        ("team_manager", False),
        ("normal_user", False),
    ],
)
def test_task_create_view(request, user_fixture, can_create, client_logged_in, team):
    user = request.getfixturevalue(user_fixture)
    client = client_logged_in(user)
    url = reverse("tasks:task_create")
    data = {
        "title": "New Task",
        "description": "desc",
        "team": team.id,
        "status": "Open",
        "deadline": "2030-01-01",
    }
    response = client.post(url, data)
    if can_create:
        assert response.status_code == 302
        assert Task.objects.filter(title="New Task").exists()
    else:
        assert response.status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_fixture,can_edit",
    [
        ("admin", True),
        ("team_admin", True),
        ("team_manager", True),
        ("normal_user", False),
    ],
)
def test_task_edit_view(request, user_fixture, can_edit, client_logged_in, task, team):
    user = request.getfixturevalue(user_fixture)
    client = client_logged_in(user)
    url = reverse("tasks:task_edit", kwargs={"pk": task.pk})
    data = {
        "title": "Edited Task",
        "description": "desc",
        "team": team.id,
        "status": "Open",
        "deadline": "2030-01-01",
    }
    response = client.post(url, data)
    if can_edit:
        assert response.status_code == 302
        task.refresh_from_db()
        assert task.title == "Edited Task"
    else:
        assert response.status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_fixture,can_delete",
    [
        ("admin", True),
        ("team_admin", True),
        ("team_manager", False),
        ("normal_user", False),
    ],
)
def test_task_delete_view(request, user_fixture, can_delete, client_logged_in, task):
    user = request.getfixturevalue(user_fixture)
    client = client_logged_in(user)
    url = reverse("tasks:task_delete", kwargs={"pk": task.pk})
    response = client.post(url)
    if can_delete:
        assert response.status_code == 302
        assert not Task.objects.filter(pk=task.pk).exists()
    else:
        assert response.status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_fixture,can_change",
    [
        ("admin", True),
        ("team_admin", True),
        ("team_manager", True),
        ("normal_user", False),
    ],
)
@pytest.mark.parametrize("status", ["Open", "In Progress", "Done"])
def test_change_status_view(
    request, user_fixture, can_change, status, client_logged_in, task
):
    user = request.getfixturevalue(user_fixture)
    client = client_logged_in(user)
    url = reverse("tasks:change_status", kwargs={"pk": task.pk})
    response = client.post(url, {"status": status})
    if can_change:
        assert response.status_code == 302
        task.refresh_from_db()
        assert task.status == status
    else:
        assert response.status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_fixture", ["admin", "team_admin", "team_manager", "normal_user"]
)
def test_add_comment_view(request, user_fixture, client_logged_in, task):
    user = request.getfixturevalue(user_fixture)
    client = client_logged_in(user)
    url = reverse("tasks:task_detail", kwargs={"pk": task.pk})
    data = {"text": f"Comment by {user.username}"}
    response = client.post(url, data)
    assert response.status_code == 302
    assert task.comments.filter(text=f"Comment by {user.username}").exists()
