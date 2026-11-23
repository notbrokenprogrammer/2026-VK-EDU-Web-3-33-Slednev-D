from array import array
from itertools import batched
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.test.utils import override_settings
from faker import Faker

from core.models import Profile
from questions.models import Answer, AnswerLike, Question, QuestionLike, Tag

BATCH_SIZE = 5000
TOPICS = ("django", "python", "postgresql", "bootstrap", "html", "css", "docker", "git")


def insert(model, rows, collect_ids=False):
    ids = array("q")
    for batch in batched(rows, BATCH_SIZE):
        created = model.objects.bulk_create(batch)
        if collect_ids:
            ids.extend(row.pk for row in created)
    return ids


def votes(model, field, target_ids, user_ids, count):
    # Каждый проход по объектам сдвигает автора на одну позицию.
    for number in range(count):
        turn, target = divmod(number, len(target_ids))
        user = user_ids[(target + turn) % len(user_ids)]
        yield model(user_id=user, **{field: target_ids[target]})


class Command(BaseCommand):
    help = "Добавляет тестовых пользователей, вопросы, ответы, теги и лайки."

    def add_arguments(self, parser):
        parser.add_argument("ratio", type=int)

    @override_settings(DEBUG=False)  # Не сохраняем текст массовых INSERT в журнале отладки.
    @transaction.atomic
    def handle(self, *args, ratio, **options):
        if ratio < 2:
            raise CommandError("Нужен ratio от 2: один пользователь может оценить только 110 разных объектов.")

        # Проверяем внешние ключи по ходу загрузки, не копим миллионы событий до COMMIT.
        with connection.cursor() as cursor:
            cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")

        fake = Faker("ru_RU")
        run_id = uuid4().hex[:12]
        User = get_user_model()
        users = insert(User, (
            User(username=f"reader_{run_id}_{i}", password="!", email=f"{run_id}.{i}@example.org",
                 first_name=fake.first_name(), last_name=fake.last_name())
            for i in range(ratio)
        ), collect_ids=True)
        insert(Profile, (Profile(user_id=user) for user in users))
        tags = insert(Tag, (
            Tag(name=f"{TOPICS[i % len(TOPICS)]}-{run_id}-{i}") for i in range(ratio)
        ), collect_ids=True)

        # Пул текстов Faker сохраняет скорость при генерации миллиона ответов.
        texts = [fake.paragraph(nb_sentences=3) for _ in range(min(2048, ratio * 100))]
        questions = insert(Question, (
            Question(author_id=fake.random.choice(users), title=fake.sentence()[:149].rstrip(".") + "?",
                     text=fake.random.choice(texts))
            for _ in range(ratio * 10)
        ), collect_ids=True)
        insert(Question.tags.through, (
            Question.tags.through(question_id=q, tag_id=tags[i % ratio]) for i, q in enumerate(questions)
        ))

        def answer_rows():
            # В каждой десятке вопросов у первого 37 ответов, у остальных по 7.
            for index, question in enumerate(questions):
                for j in range(37 if index % 10 == 0 else 7):
                    yield Answer(question_id=question, author_id=fake.random.choice(users),
                                 text=fake.random.choice(texts), accepted=j == 0 and index % 3 == 0)

        answers = insert(Answer, answer_rows(), collect_ids=True)
        rated_questions = questions[::2]
        question_votes = len(rated_questions) * min(5, ratio)
        insert(QuestionLike, votes(QuestionLike, "question_id", rated_questions, users, question_votes))
        insert(AnswerLike, votes(AnswerLike, "answer_id", answers, users, ratio * 200 - question_votes))
        self.stdout.write(self.style.SUCCESS(
            f"Добавлено пользователей: {ratio}, вопросов: {len(questions)}, ответов: {len(answers)}, "
            f"тегов: {len(tags)}, оценок: {ratio * 200}."
        ))
