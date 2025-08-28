from datetime import date, datetime, timezone

import pytest
from django.urls import reverse

from accounts.models import User
from meetings.models import Meeting
from tasks.models import Task
from teams.models import Team


@pytest.fixture
def user(db):
    return User.objects.create_user(username="user1", email="user1@example.com", password="pass1234")


@pytest.fixture
def team(db):
    return Team.objects.create(name="Test Team")


@pytest.mark.django_db
def test_month_view_basic(client, user, team):
    url = reverse("calendarapp:month_view", kwargs={"year": 2025, "month": 8})
    response = client.get(url)
    assert response.status_code == 200
    assert "month_days" in response.context
    assert "day_events" in response.context


@pytest.mark.django_db
def test_month_view_with_events(client, user, team):
    t1 = Task.objects.create(
        title="Task 1",
        created_by=user,
        team=team,
        deadline=date(2025, 8, 28)
    )
    m1 = Meeting.objects.create(
        title="Meeting 1",
        team=team,
        created_by=user,
        start_at=datetime(2025, 8, 28, 10, 0, tzinfo=timezone.utc),
        end_at=datetime(2025, 8, 28, 11, 0, tzinfo=timezone.utc)
    )
    url = reverse("calendarapp:month_view", kwargs={"year": 2025, "month": 8})
    response = client.get(url)
    assert response.status_code == 200
    day_events = response.context["day_events"]
    assert t1.deadline in day_events
    assert m1.start_at.date() in day_events


@pytest.mark.django_db
def test_day_view_basic(client, user, team):
    url = reverse("calendarapp:day_view", kwargs={"year": 2025, "month": 8, "day": 28})
    response = client.get(url)
    assert response.status_code == 200
    assert response.context["tasks"].count() == 0
    assert response.context["meetings"].count() == 0


@pytest.mark.django_db
def test_day_view_with_events(client, user, team):
    t1 = Task.objects.create(
        title="Task 1",
        created_by=user,
        team=team,
        deadline=date(2025, 8, 28)
    )
    m1 = Meeting.objects.create(
        title="Meeting 1",
        team=team,
        created_by=user,
        start_at=datetime(2025, 8, 28, 10, 0, tzinfo=timezone.utc),
        end_at=datetime(2025, 8, 28, 11, 0, tzinfo=timezone.utc)
    )
    url = reverse("calendarapp:day_view", kwargs={"year": 2025, "month": 8, "day": 28})
    response = client.get(url)
    assert response.status_code == 200
    tasks = response.context["tasks"]
    meetings = response.context["meetings"]
    assert t1 in tasks
    assert m1 in meetings


@pytest.mark.django_db
def test_month_view_multiple_tasks_same_day(client, user, team):
    t1 = Task.objects.create(title="Task 1", created_by=user, team=team, deadline=date(2025, 8, 28))
    t2 = Task.objects.create(title="Task 2", created_by=user, team=team, deadline=date(2025, 8, 28))
    url = reverse("calendarapp:month_view", kwargs={"year": 2025, "month": 8})
    response = client.get(url)
    day_events = response.context["day_events"]
    assert len(day_events[date(2025, 8, 28)]) == 2
