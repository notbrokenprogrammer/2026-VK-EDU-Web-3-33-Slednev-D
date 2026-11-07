from django.http import Http404
from django.shortcuts import render
from django.views.decorators.http import require_safe

from .mock_data import ANSWERS_BY_QUESTION, POPULAR_QUESTIONS, QUESTIONS
from .pagination import paginate

QUESTIONS_PER_PAGE = 20
ANSWERS_PER_PAGE = 30


@require_safe
def index(request):
    query = request.GET.get("q", "").strip()[:100]
    needle = query.casefold()
    questions = [
        question for question in QUESTIONS
        if needle in question["title"].casefold() or needle in question["text"].casefold()
    ]
    page = paginate(questions, request, QUESTIONS_PER_PAGE)
    return render(request, "questions/index.html", {"page_obj": page, "query": query})


@require_safe
def hot(request):
    page = paginate(POPULAR_QUESTIONS, request, QUESTIONS_PER_PAGE)
    return render(request, "questions/hot.html", {"page_obj": page})


@require_safe
def by_tag(request, tag):
    tag = tag.casefold()
    questions = [question for question in POPULAR_QUESTIONS if tag in question["tags"]]
    page = paginate(questions, request, QUESTIONS_PER_PAGE)
    return render(request, "questions/tag.html", {"page_obj": page, "tag": tag})


@require_safe
def detail(request, question_id):
    question = next((question for question in QUESTIONS if question["id"] == question_id), None)
    if question is None:
        raise Http404("Такого вопроса нет.")

    answers = ANSWERS_BY_QUESTION.get(question_id, [])
    page = paginate(answers, request, ANSWERS_PER_PAGE)
    return render(request, "questions/question.html", {"question": question, "page_obj": page})


@require_safe
def ask(request):
    return render(request, "questions/ask.html")
