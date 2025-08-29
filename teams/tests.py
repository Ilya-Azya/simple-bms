import pytest
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.urls import reverse

from teams.forms import TeamForm
from teams.models import Team, TeamMembership

User = get_user_model()


@pytest.fixture
def admin(db):
    return User.objects.create_user(
        username="admin", email="admin@test.com", password="pass1234", role="Team Admin"
    )


@pytest.fixture
def normal_user(db):
    return User.objects.create_user(
        username="user1", email="user@test.com", password="pass1234", role="User"
    )


@pytest.fixture
def team(db, admin):
    team = Team.objects.create(name="Team 1")
    TeamMembership.objects.create(user=admin, team=team, role=TeamMembership.Role.ADMIN)
    return team


@pytest.fixture
def client_logged_in(client):
    def _login(user):
        client.login(username=user.username, password="pass1234")
        return client

    return _login


@pytest.mark.django_db
def test_team_form_valid():
    form_data = {"name": "New Team"}
    form = TeamForm(data=form_data)
    assert form.is_valid()
    team = form.save()
    assert team.name == "New Team"
    assert team.invite_code is not None


@pytest.mark.django_db
def test_team_form_duplicate_name(team):
    form_data = {"name": team.name}
    form = TeamForm(data=form_data)
    assert not form.is_valid()
    assert "team with this name already exists" in str(form.errors).lower()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_fixture,can_access", [("admin", True), ("normal_user", False)]
)
def test_team_list_view(request, client_logged_in, user_fixture, can_access):
    user = request.getfixturevalue(user_fixture)
    client = client_logged_in(user)
    url = reverse("teams:team_list")
    response = client.get(url)
    if can_access:
        assert response.status_code == 200
        assert "teams/team_list.html" in [t.name for t in response.templates]
    else:
        assert response.status_code == 302


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_fixture,can_create", [("admin", True), ("normal_user", False)]
)
def test_create_team_view(request, client_logged_in, user_fixture, can_create):
    user = request.getfixturevalue(user_fixture)
    client = client_logged_in(user)
    url = reverse("teams:team_create")
    data = {"name": "Team Create Test"}
    response = client.post(url, data)
    if can_create:
        assert response.status_code == 200 or response.status_code == 302
        assert Team.objects.filter(name="Team Create Test").exists()
    else:
        assert response.status_code == 302


@pytest.mark.django_db
def test_join_team_success(client_logged_in, normal_user, team):
    client = client_logged_in(normal_user)
    url = reverse("teams:join_team")
    response = client.post(url, {"code": team.invite_code})
    membership = TeamMembership.objects.filter(user=normal_user, team=team).first()
    assert membership is not None
    assert membership.role == TeamMembership.Role.MEMBER
    assert response.status_code == 302


@pytest.mark.django_db
def test_join_team_already_member(client_logged_in, admin, team):
    client = client_logged_in(admin)
    url = reverse("teams:join_team")
    response = client.post(url, {"code": team.invite_code})
    memberships = TeamMembership.objects.filter(user=admin, team=team)
    assert memberships.count() == 1
    assert response.status_code == 302


@pytest.mark.django_db
def test_join_team_invalid_code(client_logged_in, normal_user):
    client = client_logged_in(normal_user)
    url = reverse("teams:join_team")
    response = client.post(url, {"code": "INVALIDCODE"})
    assert response.status_code == 200
    messages = list(get_messages(response.wsgi_request))
    assert any("Команда не найдена" in str(m) for m in messages)
