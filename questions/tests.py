from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import IntegrityError, connection, transaction
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from core.models import Profile
from .models import Answer, AnswerLike, Question, QuestionLike, Tag


class QuestionPageTests(TestCase):
    def test_empty_pages_and_missing_objects(self):
        tag = Tag.objects.create(name="python")
        self.assertContains(self.client.get("/"), "Пока нет ни одного вопроса")
        self.assertContains(self.client.get("/hot/"), "Пока нет ни одного вопроса")
        self.assertContains(self.client.get(tag.get_absolute_url()), "Вопросов с этим тегом пока нет")
        for url in ["/tag/missing/", "/question/123/", "/question/no-id/", "/question/-1/"]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 404)

    def test_ranking_search_and_relationship_counts(self):
        author = get_user_model().objects.create_user("reader")
        tagged = Question.objects.create(author=author, title="Миграции", text="Индекс PostgreSQL")
        recent = Question.objects.create(author=author, title="CSS", text="Стили")
        tag = Tag.objects.create(name="django")
        tagged.tags.add(tag)
        QuestionLike.objects.create(user=author, question=tagged)
        Answer.objects.bulk_create([Answer(author=author, question=tagged, text="Ответ") for _ in range(3)])

        self.assertEqual(self.client.get("/").context["page_obj"][0], recent)
        best = self.client.get("/hot/").context["page_obj"][0]
        self.assertEqual((best, best.score, best.answer_count), (tagged, 1, 3))
        self.assertEqual(list(self.client.get("/tag/DJANGO/").context["page_obj"]), [tagged])
        self.assertEqual(list(self.client.get("/?q=postgresql").context["page_obj"]), [tagged])
        self.assertContains(self.client.get(recent.get_absolute_url()), "На этот вопрос пока никто не ответил")

    def test_query_count_is_independent_of_page_size_and_inline_rows(self):
        user = get_user_model().objects.create_superuser("admin", "a@example.org", "test-password")
        self.client.force_login(user)
        q = Question.objects.create(author=user, title="Вопрос", text="Текст")
        Answer.objects.create(author=user, question=q, text="Первый ответ")
        urls = ["/", q.get_absolute_url(), reverse("admin:questions_question_change", args=[q.pk])]

        def query_count(url):
            with CaptureQueriesContext(connection) as queries:
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
            return len(queries)

        # Прогреваем кэш ContentType и прав административной панели.
        for url in urls:
            query_count(url)
        small = [query_count(url) for url in urls]
        Question.objects.bulk_create([Question(author=user, title=f"Вопрос {i}") for i in range(25)])
        Answer.objects.bulk_create([Answer(author=user, question=q, text=f"Ответ {i}") for i in range(35)])
        self.assertEqual([query_count(url) for url in urls], small)
        for url, size in [("/", 6), (q.get_absolute_url(), 6)]:
            self.assertEqual(len(self.client.get(url, {"page": 2}).context["page_obj"]), size)
            self.assertEqual(self.client.get(url, {"page": "ошибка"}).context["page_obj"].number, 1)


class FillDatabaseTests(TestCase):
    def test_repeated_fill_and_vote_constraints(self):
        for run in range(1, 3):
            call_command("fill_db", 2, verbosity=0)
            self.assertEqual(get_user_model().objects.count(), run * 2)
            self.assertEqual(Profile.objects.count(), run * 2)
            self.assertEqual(Tag.objects.count(), run * 2)
            self.assertEqual(Question.objects.count(), run * 20)
            self.assertEqual(Answer.objects.count(), run * 200)
            self.assertEqual(QuestionLike.objects.count() + AnswerLike.objects.count(), run * 400)
        for model in [QuestionLike, AnswerLike]:
            duplicate = model.objects.first()
            duplicate.pk = None
            with self.assertRaises(IntegrityError), transaction.atomic():
                duplicate.save()
