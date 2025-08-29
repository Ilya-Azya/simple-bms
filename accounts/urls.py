from django.urls import path

from . import views

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("profile/", views.profile, name="profile"),
    path("delete-confirm/", views.delete_account_confirm, name="delete_confirm"),
    path("delete/", views.delete_account, name="delete_account"),
]
