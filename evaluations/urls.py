from django.urls import path

from .views import EvaluationCreateView, MyEvaluationsListView, MyEvaluationAverageView

app_name = "evaluations"

urlpatterns = [
    path("create/<int:task_id>/", EvaluationCreateView.as_view(), name="create_evaluation"),
    path("my/", MyEvaluationsListView.as_view(), name="my_evaluations"),
    path("my/average/", MyEvaluationAverageView.as_view(), name="my_evaluations_average"),
]
