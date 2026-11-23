from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_safe

from .models import Answer, Question, Tag
from .pagination import paginate

QUESTIONS_PER_PAGE = 20
ANSWERS_PER_PAGE = 30


@require_safe
def index(request):
    query = request.GET.get("q", "").strip()[:100]
    page = paginate(Question.objects.newest(query), request, QUESTIONS_PER_PAGE)
    return render(request, "questions/index.html", {"page_obj": page, "query": query})


@require_safe
def hot(request):
    page = paginate(Question.objects.popular(), request, QUESTIONS_PER_PAGE)
    return render(request, "questions/hot.html", {"page_obj": page})


@require_safe
def by_tag(request, tag):
    tag = get_object_or_404(Tag, name__iexact=tag)
    page = paginate(Question.objects.by_tag(tag), request, QUESTIONS_PER_PAGE)
    return render(request, "questions/tag.html", {"page_obj": page, "tag": tag})


@require_safe
def detail(request, question_id):
    question = get_object_or_404(Question.objects.cards(), pk=question_id)
    page = paginate(Answer.objects.for_question(question), request, ANSWERS_PER_PAGE)
    return render(request, "questions/question.html", {"question": question, "page_obj": page})


@require_safe
def ask(request):
    return render(request, "questions/ask.html")
