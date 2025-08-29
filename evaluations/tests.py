import pytest
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.urls import reverse

from evaluations.forms import EvaluationForm
from evaluations.models import Evaluation
from tasks.models import Task
from teams.models import Team, TeamMembership

User = get_user_model()


def test_evaluation_form_valid():
    form = EvaluationForm(data={"score": 4, "comment": "Хорошо"})
    assert form.is_valid()


def test_evaluation_form_invalid_score():
    form = EvaluationForm(data={"score": 10, "comment": "too high"})
    assert not form.is_valid()
    assert "Оценка должна быть целым числом от 1 до 5." in form.errors["score"]


@pytest.mark.django_db
def test_cannot_evaluate_if_task_not_done(client):
    team = Team.objects.create(name="T")
    user = User.objects.create_user(username="u1", email="u1@test.com", password="pass", role="Team Admin")
    task = Task.objects.create(title="T", status="in_progress", created_by=user, team=team)

    client.login(username="u1", password="pass")
    url = reverse("evaluations:create_evaluation", args=[task.id])
    response = client.get(url, follow=True)

    messages = [m.message for m in get_messages(response.wsgi_request)]
    assert "Only completed tasks can be assessed." in messages


@pytest.mark.django_db
def test_cannot_evaluate_without_permissions(client):
    team = Team.objects.create(name="T")
    creator = User.objects.create_user(username="creator", email="c@test.com", password="pass")
    stranger = User.objects.create_user(username="stranger", email="s@test.com", password="pass")

    task = Task.objects.create(title="T", status="done", created_by=creator, team=team)

    client.login(username="stranger", password="pass")
    url = reverse("evaluations:create_evaluation", args=[task.id])
    response = client.get(url, follow=True)

    messages = [m.message for m in get_messages(response.wsgi_request)]
    assert "You do not have permission to rate this task." in messages


@pytest.mark.django_db
def test_cannot_evaluate_twice(client):
    team = Team.objects.create(name="T")
    admin = User.objects.create_user(username="admin", email="a@test.com", password="pass", role="Team Admin")
    task = Task.objects.create(title="T", status="done", created_by=admin, team=team)

    Evaluation.objects.create(task=task, evaluator=admin, user=admin, score=5)

    client.login(username="admin", password="pass")
    url = reverse("evaluations:create_evaluation", args=[task.id])
    response = client.get(url, follow=True)

    messages = [m.message for m in get_messages(response.wsgi_request)]
    assert "You have already rated this task." in messages


@pytest.mark.django_db
def test_successful_evaluation_creation(client):
    team = Team.objects.create(name="T")
    admin = User.objects.create_user(username="admin", email="a@test.com", password="pass", role="Team Admin")
    teammate = User.objects.create_user(username="u2", email="u2@test.com", password="pass")

    TeamMembership.objects.create(team=team, user=teammate, role=TeamMembership.Role.MANAGER)

    task = Task.objects.create(title="T", status="done", created_by=admin, team=team)

    client.login(username="admin", password="pass")
    url = reverse("evaluations:create_evaluation", args=[task.id])
    response = client.post(url, {"score": 5, "comment": "ok"}, follow=True)

    assert response.status_code == 200
    assert Evaluation.objects.count() >= 1


@pytest.mark.django_db
def test_multiple_team_members_get_evaluations(client):
    team = Team.objects.create(name="T")
    admin = User.objects.create_user(username="admin", email="a@test.com", password="pass", role="Team Admin")
    u1 = User.objects.create_user(username="u1", email="u1@test.com", password="pass")
    u2 = User.objects.create_user(username="u2", email="u2@test.com", password="pass")

    TeamMembership.objects.create(team=team, user=u1, role=TeamMembership.Role.MEMBER)
    TeamMembership.objects.create(team=team, user=u2, role=TeamMembership.Role.MEMBER)
    TeamMembership.objects.create(team=team, user=admin, role=TeamMembership.Role.ADMIN)

    task = Task.objects.create(title="T", status="done", created_by=admin, team=team)

    client.login(username="admin", password="pass")
    url = reverse("evaluations:create_evaluation", args=[task.id])

    response = client.post(url, {"score": 4, "comment": "ok"}, follow=True)
    assert response.status_code in (200, 302)

    evaluations = Evaluation.objects.filter(task=task)
    assert evaluations.count() == 3

    users_rated = set(evaluations.values_list("user_id", flat=True))
    expected_ids = {admin.id, u1.id, u2.id}
    assert users_rated == expected_ids


@pytest.mark.django_db
def test_evaluation_requires_team(client):
    user = User.objects.create_user(username="u", email="u@test.com", password="pass")

    with pytest.raises(Exception):
        Task.objects.create(title="No team", status="done", created_by=user)


@pytest.mark.django_db
def test_manager_can_evaluate(client):
    team = Team.objects.create(name="T")
    manager = User.objects.create_user(username="m", email="m@test.com", password="pass")
    task_creator = User.objects.create_user(username="creator", email="c@test.com", password="pass")

    TeamMembership.objects.create(team=team, user=manager, role=TeamMembership.Role.MANAGER)

    task = Task.objects.create(title="T", status="done", created_by=task_creator, team=team)

    client.login(username="m", password="pass")
    url = reverse("evaluations:create_evaluation", args=[task.id])
    response = client.post(url, {"score": 5, "comment": "Super"}, follow=True)

    assert response.status_code == 200
    assert Evaluation.objects.filter(task=task, evaluator=manager).exists()


@pytest.mark.django_db
def test_my_evaluations_list_view(client):
    team = Team.objects.create(name="T")
    user = User.objects.create_user(username="u", email="u@test.com", password="pass")
    task = Task.objects.create(title="T", status="done", created_by=user, team=team)
    Evaluation.objects.create(task=task, evaluator=user, user=user, score=4)

    client.login(username="u", password="pass")
    url = reverse("evaluations:my_evaluations")
    response = client.get(url)

    assert response.status_code == 200
    assert "evaluations" in response.context
    assert len(response.context["evaluations"]) == 1


@pytest.mark.django_db
def test_average_view_with_data(client):
    team = Team.objects.create(name="T")
    user = User.objects.create_user(username="u", email="u@test.com", password="pass")
    task = Task.objects.create(title="T", status="done", created_by=user, team=team)
    Evaluation.objects.create(task=task, evaluator=user, user=user, score=4)
    Evaluation.objects.create(task=task, evaluator=user, user=user, score=2)

    client.login(username="u", password="pass")
    url = reverse("evaluations:my_evaluations_average")
    response = client.get(url)

    assert response.status_code == 200
    assert response.context["avg_score"] == 3.0
    assert response.context["count"] == 2


@pytest.mark.django_db
def test_average_view_invalid_dates(client):
    team = Team.objects.create(name="T")
    user = User.objects.create_user(username="u", email="u@test.com", password="pass")
    task = Task.objects.create(title="T", status="done", created_by=user, team=team)
    Evaluation.objects.create(task=task, evaluator=user, user=user, score=5)

    client.login(username="u", password="pass")
    url = reverse("evaluations:my_evaluations_average") + "?start=wrong&end=wrong"
    response = client.get(url)

    assert response.status_code == 200
    assert response.context["count"] == 1


@pytest.mark.django_db
def test_average_view_no_evaluations(client):
    user = User.objects.create_user(username="u", email="u@test.com", password="pass")

    client.login(username="u", password="pass")
    url = reverse("evaluations:my_evaluations_average")
    response = client.get(url)

    assert response.status_code == 200
    assert response.context["count"] == 0
    assert response.context["avg_score"] is None
