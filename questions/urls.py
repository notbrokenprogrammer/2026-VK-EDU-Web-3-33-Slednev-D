from django.urls import path

from . import views

app_name = "questions"

urlpatterns = [
    path("", views.index, name="index"),
    path("hot/", views.hot, name="hot"),
    path("tag/<str:tag>/", views.by_tag, name="tag"),
    path("question/<int:question_id>/", views.detail, name="detail"),
    path("ask/", views.ask, name="ask"),
]
