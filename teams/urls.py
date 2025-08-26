from django.urls import path

from . import views

app_name = "teams"

urlpatterns = [
    path("join/", views.join_team, name="join_team"),
]
