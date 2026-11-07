from django.urls import include, path

urlpatterns = [
    path("", include("questions.urls")),
    path("", include("core.urls")),
]
