from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.csrf import csrf_failure as django_csrf_failure
from django.views.decorators.http import require_http_methods

from .forms import LoginForm, ProfileForm, SignupForm


class SignIn(LoginView):
    template_name = "core/login.html"
    authentication_form = LoginForm


@require_http_methods(["GET", "POST"])
def signup(request):
    form = SignupForm(request.POST if request.method == "POST" else None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.save())
        return redirect("questions:index")
    return render(request, "core/signup.html", {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def profile(request):
    form = ProfileForm(request.POST if request.method == "POST" else None, request.FILES or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Профиль сохранён.")
        return redirect("core:profile")
    return render(request, "core/profile.html", {"form": form})


def csrf_failure(request, reason=""):
    if request.path.startswith("/api/"):
        return JsonResponse({"error": "Обновите страницу и повторите запрос."}, status=403)
    return django_csrf_failure(request, reason=reason)
