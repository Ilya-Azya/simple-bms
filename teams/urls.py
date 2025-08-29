from django.urls import path

from . import views
from .views import team_list, create_team

app_name = "teams"

urlpatterns = [
    path("", team_list, name="team_list"),
    path("create/", create_team, name="team_create"),
    path("join/", views.join_team, name="join_team"),
]
