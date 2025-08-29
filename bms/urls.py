"""
URL configuration for bms project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.contrib.auth.views import LogoutView, LoginView
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path("", TemplateView.as_view(template_name="base.html"), name="home"),
    path(
        "login/",
        LoginView.as_view(template_name="login.html", next_page="tasks:task_list"),
        name="login",
    ),
    path("logout/", LogoutView.as_view(next_page="login"), name="logout"),
    path("admin/", admin.site.urls),
    path("users/", include("accounts.urls")),
    path("tasks/", include("tasks.urls")),
    path("meetings/", include("meetings.urls")),
    path("evaluations/", include("evaluations.urls")),
    path("calendar/", include("calendarapp.urls")),
    path("teams/", include("teams.urls")),
]
