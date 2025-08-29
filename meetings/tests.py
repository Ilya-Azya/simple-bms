from datetime import timedelta, datetime

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from meetings.forms import MeetingForm
from meetings.models import Meeting
from teams.models import Team, TeamMembership

User = get_user_model()


def aware(dt: datetime):
    return timezone.make_aware(dt) if timezone.is_naive(dt) else dt


def make_times(offset_hours=0, dur_hours=1):
    start = timezone.now() + timedelta(hours=offset_hours)
    end = start + timedelta(hours=dur_hours)
    return start, end


@pytest.mark.django_db
def test_meeting_str():
    team = Team.objects.create(name="T")
    user = User.objects.create_user(username="u1", email="u1@test.com", password="pass")
    start, end = make_times()
    m = Meeting.objects.create(
        title="Daily", team=team, start_at=start, end_at=end, created_by=user
    )
    s = str(m)
    assert "Daily" in s
    assert m.start_at.isoformat() in s
    assert m.end_at.isoformat() in s


@pytest.mark.django_db
def test_meeting_end_before_start_invalid():
    team = Team.objects.create(name="T")
    start, end = make_times()
    with pytest.raises(ValidationError) as e:
        Meeting.objects.create(title="bad", team=team, start_at=end, end_at=start)
    assert "End of meeting should be later than start" in str(e.value)


@pytest.mark.django_db
def test_meeting_overlap_same_team_invalid():
    team = Team.objects.create(name="T")
    user = User.objects.create_user(username="u1", email="u1@test.com", password="pass")
    s1, e1 = make_times(1, 2)
    s2 = s1 + timedelta(minutes=30)
    e2 = e1 + timedelta(minutes=30)

    Meeting.objects.create(
        title="A", team=team, start_at=s1, end_at=e1, created_by=user
    )
    with pytest.raises(ValidationError) as e:
        Meeting.objects.create(title="B", team=team, start_at=s2, end_at=e2)
    assert "Intersects with another meeting" in str(e.value)


@pytest.mark.django_db
def test_meeting_overlap_different_team_ok():
    team1 = Team.objects.create(name="T1")
    team2 = Team.objects.create(name="T2")
    user = User.objects.create_user(username="u1", email="u1@test.com", password="pass")
    s1, e1 = make_times(1, 2)

    Meeting.objects.create(
        title="A", team=team1, start_at=s1, end_at=e1, created_by=user
    )
    Meeting.objects.create(
        title="B", team=team2, start_at=s1, end_at=e1, created_by=user
    )
    assert Meeting.objects.count() == 2


@pytest.mark.django_db
def test_participant_overlap_invalid_via_model_clean():
    team = Team.objects.create(name="T")
    u = User.objects.create_user(username="u", email="u@test.com", password="pass")

    s1, e1 = make_times(1, 2)
    s2, e2 = s1 + timedelta(minutes=30), e1 + timedelta(minutes=30)

    m1 = Meeting.objects.create(
        title="A", team=team, start_at=s1, end_at=e1, created_by=u
    )
    m1.participants.add(u)

    m2 = Meeting(title="B", team=team, start_at=s2, end_at=e2, created_by=u)
    m2._participants_for_validation = [u]
    with pytest.raises(ValidationError) as e:
        m2.save()
    assert "has another meeting at that time" in str(e.value)


@pytest.mark.django_db
def test_meeting_end_equal_start_invalid():
    team = Team.objects.create(name="T")
    u = User.objects.create_user(username="u", email="u@test.com", password="pass")
    start = timezone.now()
    end = start

    with pytest.raises(ValidationError) as e:
        Meeting.objects.create(
            title="bad", team=team, start_at=start, end_at=end, created_by=u
        )
    assert "End of meeting should be later than start" in str(e.value)


@pytest.mark.django_db
def test_form_invalid_end_before_start():
    team = Team.objects.create(name="T")
    s, e = make_times()
    data = {
        "title": "bad",
        "description": "",
        "team": team.id,
        "participants": [],
        "start_at": e,
        "end_at": s,
    }
    form = MeetingForm(data=data)
    assert not form.is_valid()
    assert "End of meeting should be later than start" in str(form.errors)


@pytest.mark.django_db
def test_form_participants_queryset_depends_on_team_in_data():
    team = Team.objects.create(name="T")
    u1 = User.objects.create_user(username="u1", email="u1@test.com", password="pass")
    u2 = User.objects.create_user(username="u2", email="u2@test.com", password="pass")
    TeamMembership.objects.create(team=team, user=u1, role=TeamMembership.Role.MEMBER)
    TeamMembership.objects.create(team=team, user=u2, role=TeamMembership.Role.MEMBER)

    s, e = make_times()
    form = MeetingForm(
        data={
            "title": "X",
            "description": "",
            "team": team.id,
            "participants": [],
            "start_at": s,
            "end_at": e,
        }
    )
    qs_ids = set(form.fields["participants"].queryset.values_list("id", flat=True))
    assert {u1.id, u2.id}.issubset(qs_ids)


@pytest.mark.django_db
def test_form_team_queryset_limited_for_non_admin_user():
    user = User.objects.create_user(username="u", email="u@test.com", password="pass")
    t1 = Team.objects.create(name="T1")
    Team.objects.create(name="T2")
    TeamMembership.objects.create(team=t1, user=user, role=TeamMembership.Role.MEMBER)

    form = MeetingForm(user=user)
    team_ids = set(form.fields["team"].queryset.values_list("id", flat=True))
    assert team_ids == {t1.id}


@pytest.mark.django_db
def test_form_team_queryset_for_admin_not_limited():
    admin = User.objects.create_user(
        username="admin", email="a@test.com", password="pass", role="Team Admin"
    )
    t1 = Team.objects.create(name="T1")
    t2 = Team.objects.create(name="T2")

    form = MeetingForm(user=admin)
    team_ids = set(form.fields["team"].queryset.values_list("id", flat=True))
    assert {t1.id, t2.id}.issubset(team_ids)


@pytest.mark.django_db
def test_form_participants_queryset_from_instance_on_edit():
    team = Team.objects.create(name="T")
    u = User.objects.create_user(username="u", email="u@test.com", password="pass")
    TeamMembership.objects.create(team=team, user=u, role=TeamMembership.Role.MEMBER)

    s, e = make_times()
    meeting = Meeting.objects.create(
        title="X", team=team, start_at=s, end_at=e, created_by=u
    )
    form = MeetingForm(instance=meeting)
    qs_ids = set(form.fields["participants"].queryset.values_list("id", flat=True))
    assert u.id in qs_ids


@pytest.mark.django_db
def test_form_rejects_non_team_participant():
    team = Team.objects.create(name="T")
    u_in = User.objects.create_user(username="in", email="in@test.com", password="pass")
    u_out = User.objects.create_user(
        username="out", email="out@test.com", password="pass"
    )

    TeamMembership.objects.create(team=team, user=u_in, role=TeamMembership.Role.MEMBER)

    s, e = make_times()
    form = MeetingForm(
        data={
            "title": "X",
            "description": "",
            "team": team.id,
            "participants": [u_out.id],
            "start_at": s,
            "end_at": e,
        }
    )

    assert not form.is_valid()
    assert "Select a valid choice" in str(form.errors)


@pytest.mark.django_db
def test_list_view_login_required(client):
    resp = client.get(reverse("meetings:meeting_list"))
    assert resp.status_code in (302, 301)


@pytest.mark.django_db
def test_list_view_user_perms_flags(client):
    t1 = Team.objects.create(name="T1")
    t2 = Team.objects.create(name="T2")
    user = User.objects.create_user(
        username="u", email="u@test.com", password="pass", role="Team Admin"
    )
    s1, e1 = make_times(1, 1)
    s2, e2 = make_times(2, 1)
    m1 = Meeting.objects.create(
        title="A", team=t1, start_at=s1, end_at=e1, created_by=user
    )
    m2 = Meeting.objects.create(
        title="B", team=t2, start_at=s2, end_at=e2, created_by=user
    )

    client.login(username="u", password="pass")
    resp = client.get(reverse("meetings:meeting_list"))
    assert resp.status_code == 200
    perms = resp.context["user_perms"]
    assert perms[m1.pk] is True
    assert perms[m2.pk] is True


@pytest.mark.django_db
def test_detail_view_context_flags(client):
    team = Team.objects.create(name="T")
    manager = User.objects.create_user(
        username="mgr", email="mgr@test.com", password="pass"
    )
    member = User.objects.create_user(
        username="mem", email="mem@test.com", password="pass"
    )
    TeamMembership.objects.create(
        team=team, user=manager, role=TeamMembership.Role.MANAGER
    )
    TeamMembership.objects.create(
        team=team, user=member, role=TeamMembership.Role.MEMBER
    )
    s, e = make_times()
    meeting = Meeting.objects.create(
        title="A", team=team, start_at=s, end_at=e, created_by=manager
    )

    client.login(username="mgr", password="pass")
    resp = client.get(reverse("meetings:meeting_detail", args=[meeting.pk]))
    assert resp.status_code == 200
    assert resp.context["is_manager_or_admin"] is True
    assert resp.context["is_member"] is True


@pytest.mark.django_db
def test_create_view_for_member_forbidden(client):
    team = Team.objects.create(name="T")
    member = User.objects.create_user(username="m", email="m@test.com", password="pass")
    TeamMembership.objects.create(
        team=team, user=member, role=TeamMembership.Role.MEMBER
    )

    s, e = make_times()
    client.login(username="m", password="pass")
    resp = client.post(
        reverse("meetings:meeting_create"),
        data={
            "title": "X",
            "description": "",
            "team": team.id,
            "participants": [],
            "start_at": s,
            "end_at": e,
        },
    )
    assert resp.status_code == 403


@pytest.mark.parametrize("role", ["Team Admin", "MANAGER"])
@pytest.mark.django_db
def test_create_view_allowed_for_admin_or_manager(client, role):
    team = Team.objects.create(name="T")
    user = User.objects.create_user(
        username="u",
        email="u@test.com",
        password="pass",
        role=("Team Admin" if role == "Team Admin" else "User"),
    )
    if role == "MANAGER":
        TeamMembership.objects.create(
            team=team, user=user, role=TeamMembership.Role.MANAGER
        )

    s, e = make_times()
    client.login(username="u", password="pass")
    resp = client.post(
        reverse("meetings:meeting_create"),
        data={
            "title": "X",
            "description": "desc",
            "team": team.id,
            "participants": [],
            "start_at": s,
            "end_at": e,
        },
        follow=True,
    )
    assert resp.status_code in (200, 302)
    m = Meeting.objects.latest("id")
    assert m.title == "X"
    assert m.created_by == user
    assert m.team == team


@pytest.mark.django_db
def test_create_view_saves_participants(client):
    team = Team.objects.create(name="T")
    User.objects.create_user(
        username="admin", email="a@test.com", password="pass", role="Team Admin"
    )
    u1 = User.objects.create_user(username="u1", email="u1@test.com", password="pass")
    TeamMembership.objects.create(team=team, user=u1, role=TeamMembership.Role.MEMBER)

    s, e = make_times()
    client.login(username="admin", password="pass")
    resp = client.post(
        reverse("meetings:meeting_create"),
        data={
            "title": "With participants",
            "description": "",
            "team": team.id,
            "participants": [u1.id],
            "start_at": s,
            "end_at": e,
        },
        follow=True,
    )
    assert resp.status_code in (200, 302)
    m = Meeting.objects.latest("id")
    assert u1 in m.participants.all()


@pytest.mark.django_db
def test_update_view_forbidden_for_member(client):
    team = Team.objects.create(name="T")
    member = User.objects.create_user(username="m", email="m@test.com", password="pass")
    TeamMembership.objects.create(
        team=team, user=member, role=TeamMembership.Role.MEMBER
    )
    s, e = make_times()
    m = Meeting.objects.create(
        title="A", team=team, start_at=s, end_at=e, created_by=member
    )

    client.login(username="m", password="pass")
    resp = client.get(reverse("meetings:meeting_edit", args=[m.pk]))
    assert resp.status_code == 403


@pytest.mark.django_db
def test_update_view_ok_for_team_admin(client):
    team = Team.objects.create(name="T")
    admin = User.objects.create_user(username="a", email="a@test.com", password="pass")
    TeamMembership.objects.create(team=team, user=admin, role=TeamMembership.Role.ADMIN)

    s, e = make_times()
    m = Meeting.objects.create(
        title="A", team=team, start_at=s, end_at=e, created_by=admin
    )

    client.login(username="a", password="pass")
    resp = client.post(
        reverse("meetings:meeting_edit", args=[m.pk]),
        data={
            "title": "Renamed",
            "description": "",
            "team": team.id,
            "participants": [],
            "start_at": s,
            "end_at": e,
        },
        follow=True,
    )
    assert resp.status_code in (200, 302)
    m.refresh_from_db()
    assert m.title == "Renamed"


@pytest.mark.django_db
def test_delete_view_forbidden_for_member(client):
    team = Team.objects.create(name="T")
    member = User.objects.create_user(username="m", email="m@test.com", password="pass")
    user = User.objects.create_user(
        username="user", email="user@test.com", password="pass"
    )
    TeamMembership.objects.create(
        team=team, user=member, role=TeamMembership.Role.MEMBER
    )
    s, e = make_times()
    m = Meeting.objects.create(
        title="A", team=team, start_at=s, end_at=e, created_by=user
    )

    client.login(username="m", password="pass")
    resp = client.get(reverse("meetings:meeting_delete", args=[m.pk]))
    assert resp.status_code == 403


@pytest.mark.django_db
def test_delete_view_ok_for_team_admin(client):
    team = Team.objects.create(name="T")
    admin = User.objects.create_user(username="a", email="a@test.com", password="pass")
    TeamMembership.objects.create(team=team, user=admin, role=TeamMembership.Role.ADMIN)
    s, e = make_times()
    m = Meeting.objects.create(
        title="A", team=team, start_at=s, end_at=e, created_by=admin
    )

    client.login(username="a", password="pass")
    resp_get = client.get(reverse("meetings:meeting_delete", args=[m.pk]))
    assert resp_get.status_code == 200
    resp_post = client.post(
        reverse("meetings:meeting_delete", args=[m.pk]), follow=True
    )
    assert resp_post.status_code in (200, 302)
    assert not Meeting.objects.filter(pk=m.pk).exists()


@pytest.mark.django_db
def test_list_pagination_page2(client):
    team = Team.objects.create(name="T")
    admin = User.objects.create_user(
        username="admin", email="admin@test.com", password="pass", role="Team Admin"
    )

    for i in range(25):
        s, e = make_times(offset_hours=i + 1)
        Meeting.objects.create(
            title=f"M{i}", team=team, start_at=s, end_at=e, created_by=admin
        )
    client.login(username="admin", password="pass")

    resp = client.get(reverse("meetings:meeting_list") + "?page=2")
    assert resp.status_code == 200
    assert len(resp.context["meetings"]) == 5
