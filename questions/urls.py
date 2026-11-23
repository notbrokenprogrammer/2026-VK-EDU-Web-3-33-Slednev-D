from django.urls import path

from . import api, views
from .models import Answer, Question

app_name = "questions"

urlpatterns = [
    path("", views.index, name="index"),
    path("hot/", views.hot, name="hot"),
    path("tag/<str:tag>/", views.by_tag, name="tag"),
    path("question/<int:question_id>/", views.detail, name="detail"),
    path("api/questions/<int:pk>/vote/", api.vote, {"model": Question}, name="vote-question"),
    path("api/answers/<int:pk>/vote/", api.vote, {"model": Answer}, name="vote-answer"),
    path("api/questions/<int:pk>/accept/", api.accept, name="accept"),
    path("ask/", views.ask, name="ask"),
]
