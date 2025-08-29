from django.urls import path

from . import views

app_name = "calendarapp"

urlpatterns = [
    path("day/<int:year>/<int:month>/<int:day>/", views.day_view, name="day_view"),
    path("month/<int:year>/<int:month>/", views.month_view, name="month_view"),
]
