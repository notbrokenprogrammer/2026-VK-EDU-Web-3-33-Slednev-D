from functools import wraps

from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse

from .forms import AcceptedAnswerForm, VoteForm
from .models import Question


def authenticated_post(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if request.method != "POST":
            response = JsonResponse({"error": "Требуется POST."}, status=405)
            response["Allow"] = "POST"
            return response
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Войдите в аккаунт и повторите действие."}, status=401)
        return view(request, *args, **kwargs)
    return wrapped


def invalid(form):
    return JsonResponse({"error": " ".join(str(message) for errors in form.errors.values() for message in errors)}, status=400)


@authenticated_post
@transaction.atomic
def vote(request, pk, model):
    form = VoteForm(request.POST)
    if not form.is_valid():
        return invalid(form)
    target = model.objects.select_for_update().filter(pk=pk).first()
    if target is None:
        return JsonResponse({"error": "Запись не найдена."}, status=404)
    try:
        result = form.save(target, request.user)
    except ValidationError as error:
        return JsonResponse({"error": error.messages[0]}, status=409)
    return JsonResponse(result)


@authenticated_post
@transaction.atomic
def accept(request, pk):
    question = Question.objects.select_for_update().filter(pk=pk).first()
    if question is None:
        return JsonResponse({"error": "Вопрос не найден."}, status=404)
    if request.user.pk != question.author_id:
        return JsonResponse({"error": "Выбрать ответ может только автор вопроса."}, status=403)
    form = AcceptedAnswerForm(request.POST, question)
    if not form.is_valid():
        return invalid(form)
    return JsonResponse(form.save())
