from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_safe

from .forms import AnswerForm, QuestionForm
from .models import Answer, Question, Tag
from .pagination import paginate

QUESTIONS_PER_PAGE = 20
ANSWERS_PER_PAGE = 30


@require_safe
def index(request):
    query = request.GET.get("q", "").strip()[:100]
    page = paginate(Question.objects.newest(query, request.user), request, QUESTIONS_PER_PAGE)
    return render(request, "questions/index.html", {"page_obj": page, "query": query})


@require_safe
def hot(request):
    page = paginate(Question.objects.popular(request.user), request, QUESTIONS_PER_PAGE)
    return render(request, "questions/hot.html", {"page_obj": page})


@require_safe
def by_tag(request, tag):
    tag = get_object_or_404(Tag, name__iexact=tag)
    page = paginate(Question.objects.by_tag(tag, request.user), request, QUESTIONS_PER_PAGE)
    return render(request, "questions/tag.html", {"page_obj": page, "tag": tag})


@require_http_methods(["GET", "HEAD", "POST"])
def detail(request, question_id):
    question = get_object_or_404(Question.objects.cards(request.user), pk=question_id)
    form = AnswerForm(request.POST if request.method == "POST" else None)
    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if form.is_valid():
            answer = form.save(request.user, question)
            return redirect(answer.page_url(ANSWERS_PER_PAGE))
    page = paginate(Answer.objects.for_question(question, request.user), request, ANSWERS_PER_PAGE)
    return render(request, "questions/question.html", {"question": question, "page_obj": page, "form": form})


@login_required
@require_http_methods(["GET", "HEAD", "POST"])
def ask(request):
    form = QuestionForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        return redirect(form.save(request.user))
    return render(request, "questions/ask.html", {"form": form})
