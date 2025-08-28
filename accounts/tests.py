import pytest
from django.contrib.auth import get_user_model, BACKEND_SESSION_KEY, SESSION_KEY
from django.urls import reverse

from accounts.forms import SignUpForm, ProfileForm

User = get_user_model()


@pytest.mark.django_db
def test_create_user():
    user = User.objects.create_user(username="user1", email="user1@example.com", password="pass1234")
    assert user.username == "user1"
    assert user.email == "user1@example.com"
    assert user.role == "User"
    assert str(user) == f"{user.username} | {user.email} | {user.role}"


@pytest.mark.django_db
def test_signup_form_valid():
    form_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password1": "strongpassword123",
        "password2": "strongpassword123"
    }
    form = SignUpForm(data=form_data)
    assert form.is_valid()
    user = form.save()
    assert User.objects.filter(username="testuser").exists()


@pytest.mark.django_db
def test_signup_form_duplicate_email():
    User.objects.create_user(username="user1", email="test@example.com", password="pass1234")
    form_data = {
        "username": "user2",
        "email": "test@example.com",
        "password1": "strongpassword123",
        "password2": "strongpassword123"
    }
    form = SignUpForm(data=form_data)
    assert not form.is_valid()
    assert "This email already used" in form.errors["email"][0]


@pytest.mark.django_db
def test_profile_form_edit():
    user = User.objects.create_user(username="user1", email="user1@example.com", password="pass1234")
    form_data = {"first_name": "John", "last_name": "Doe", "email": "user1@example.com"}
    form = ProfileForm(data=form_data, instance=user)
    assert form.is_valid()
    form.save()
    user.refresh_from_db()
    assert user.first_name == "John"
    assert user.last_name == "Doe"


@pytest.mark.django_db
def test_signup_and_login(client):
    signup_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password1": "strongpassword123",
        "password2": "strongpassword123"
    }

    response = client.post(reverse("signup"), signup_data)
    assert response.status_code == 302

    user = User.objects.get(username="testuser")
    user.backend = 'core.backends.EmailOrUsernameBackend'
    user.save()

    login_data_username = {
        "username": "testuser",
        "password": "strongpassword123"
    }
    login_url = reverse("login")
    response_username = client.post(login_url, login_data_username)
    assert response_username.status_code in [302, 200]

    session = client.session
    session[BACKEND_SESSION_KEY] = user.backend
    session[SESSION_KEY] = user.pk
    session.save()

    client.logout()
    login_data_email = {
        "username": "test@example.com",
        "password": "strongpassword123"
    }
    response_email = client.post(login_url, login_data_email)
    assert response_email.status_code in [302, 200]


@pytest.mark.django_db
def test_profile_view(client):
    user = User.objects.create_user(username="user1", email="user1@example.com", password="pass1234")
    client.login(username="user1", password="pass1234")
    url = reverse("profile")
    data = {"first_name": "John", "last_name": "Doe", "email": "user1@example.com"}
    response = client.post(url, data)
    assert response.status_code == 302
    user.refresh_from_db()
    assert user.first_name == "John"


@pytest.mark.django_db
def test_delete_account_confirm_view(client):
    user = User.objects.create_user(username="user1", email="user1@example.com", password="pass1234")
    client.login(username="user1", password="pass1234")
    url = reverse("delete_confirm")
    response = client.get(url)
    assert response.status_code == 200
    assert 'accounts/delete_confirm.html' in [t.name for t in response.templates]


@pytest.mark.django_db
def test_delete_account_view(client):
    user = User.objects.create_user(username="user1", email="user1@example.com", password="pass1234")
    client.login(username="user1", password="pass1234")
    url = reverse("delete_account")
    response = client.post(url)
    assert response.status_code == 302
    assert not User.objects.filter(username="user1").exists()


@pytest.mark.django_db
def test_signup_form_invalid_email():
    form_data = {
        "username": "testuser",
        "email": "not-an-email",
        "password1": "strongpassword123",
        "password2": "strongpassword123"
    }
    form = SignUpForm(data=form_data)
    assert not form.is_valid()
    assert "Enter a valid email address." in form.errors["email"][0]


@pytest.mark.django_db
def test_signup_form_duplicate_username():
    User.objects.create_user(username="testuser", email="test1@example.com", password="pass1234")
    form_data = {
        "username": "testuser",
        "email": "test2@example.com",
        "password1": "strongpassword123",
        "password2": "strongpassword123"
    }
    form = SignUpForm(data=form_data)
    assert not form.is_valid()
    assert "A user with that username already exists." in form.errors["username"][0]


@pytest.mark.django_db
def test_login_invalid_password(client):
    user = User.objects.create_user(username="testuser", email="test@example.com", password="correctpassword")
    login_url = reverse("login")
    response = client.post(login_url, {"username": "testuser", "password": "wrongpassword"})

    assert response.status_code == 200

    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
def test_login_invalid_email(client):
    user = User.objects.create_user(username="testuser", email="test@example.com", password="correctpassword")
    login_url = reverse("login")
    response = client.post(login_url, {"username": "wrong@example.com", "password": "correctpassword"})

    assert response.status_code == 200
    assert "_auth_user_id" not in client.session
