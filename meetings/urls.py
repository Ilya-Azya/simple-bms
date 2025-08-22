from django.urls import path

from . import views

app_name = "meetings"

urlpatterns = [
    path("", views.MeetingListView.as_view(), name="meeting_list"),
    path("create/", views.MeetingCreateView.as_view(), name="meeting_create"),
    path("<int:pk>/", views.MeetingDetailView.as_view(), name="meeting_detail"),
    path("<int:pk>/edit/", views.MeetingUpdateView.as_view(), name="meeting_edit"),
    path("<int:pk>/delete/", views.MeetingDeleteView.as_view(), name="meeting_delete"),
]
