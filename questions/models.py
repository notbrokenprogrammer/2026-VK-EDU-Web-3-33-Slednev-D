from django.conf import settings
from django.db import models
from django.db.models import Count, OuterRef, Q, Subquery
from django.db.models.functions import Coalesce, Lower
from django.urls import reverse


class TagQuerySet(models.QuerySet):
    def popular(self):
        return self.annotate(uses=Count("questions")).order_by("-uses", "name")


class Tag(models.Model):
    name = models.SlugField("Название", max_length=64, allow_unicode=True, unique=True)
    objects = TagQuerySet.as_manager()

    class Meta:
        verbose_name = "тег"
        verbose_name_plural = "теги"
        constraints = [models.UniqueConstraint(Lower("name"), name="unique_tag_casefold")]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("questions:tag", args=[self.name])


class QuestionQuerySet(models.QuerySet):
    def cards(self):
        # Независимые подзапросы исключают перемножение ответов и оценок.
        answers = Answer.objects.filter(question_id=OuterRef("pk")).values("question_id").annotate(n=Count("*"))
        likes = QuestionLike.objects.filter(question_id=OuterRef("pk")).values("question_id").annotate(n=Count("*"))
        return self.select_related("author__profile").prefetch_related("tags").annotate(
            answer_count=Coalesce(Subquery(answers.values("n")), 0),
            score=Coalesce(Subquery(likes.values("n")), 0),
        )

    def newest(self, query=""):
        questions = self.cards()
        if query:
            questions = questions.filter(Q(title__icontains=query) | Q(text__icontains=query))
        return questions.order_by("-created_at", "-pk")

    def popular(self):
        return self.cards().order_by("-score", "-created_at", "-pk")

    def by_tag(self, tag):
        return self.popular().filter(tags=tag)

    def top_authors(self):
        return self.values("author__username").annotate(total=Count("*")).order_by("-total", "author__username")


class Question(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Автор")
    title = models.CharField("Заголовок", max_length=150)
    text = models.TextField("Текст вопроса")
    created_at = models.DateTimeField("Дата публикации", auto_now_add=True)
    tags = models.ManyToManyField(Tag, verbose_name="Теги", related_name="questions", blank=True)
    objects = QuestionQuerySet.as_manager()

    class Meta:
        verbose_name = "вопрос"
        verbose_name_plural = "вопросы"
        indexes = [models.Index(fields=["-created_at", "-id"])]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("questions:detail", args=[self.pk])


class AnswerQuerySet(models.QuerySet):
    def for_question(self, question):
        return self.filter(question=question).select_related("author__profile").annotate(
            score=Count("likes")
        ).order_by("-accepted", "created_at", "pk")


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers", verbose_name="Вопрос")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Автор")
    text = models.TextField("Текст ответа")
    created_at = models.DateTimeField("Дата публикации", auto_now_add=True)
    accepted = models.BooleanField("Правильный ответ", default=False)
    objects = AnswerQuerySet.as_manager()

    class Meta:
        verbose_name = "ответ"
        verbose_name_plural = "ответы"

    def __str__(self):
        return self.text[:80]


class QuestionLike(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Пользователь")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="likes", verbose_name="Вопрос")

    class Meta:
        verbose_name = "лайк вопроса"
        verbose_name_plural = "лайки вопросов"
        constraints = [models.UniqueConstraint(fields=["user", "question"], name="unique_question_like")]

    def __str__(self):
        return f"Лайк вопроса №{self.question_id} от пользователя №{self.user_id}"


class AnswerLike(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Пользователь")
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name="likes", verbose_name="Ответ")

    class Meta:
        verbose_name = "лайк ответа"
        verbose_name_plural = "лайки ответов"
        constraints = [models.UniqueConstraint(fields=["user", "answer"], name="unique_answer_like")]

    def __str__(self):
        return f"Лайк ответа №{self.answer_id} от пользователя №{self.user_id}"
