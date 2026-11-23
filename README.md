# Ответы · ДЗ 3 по веб-разработке VK Education

Учебный сайт вопросов и ответов на Django 5.2 и PostgreSQL 16. Ленты, поиск, теги, рейтинг и ответы читаются из базы. Добавлять и редактировать записи можно в русскоязычной админке. Пользовательские формы из ДЗ 2 сохраняют демонстрационное поведение.

## Подготовка окружения

Команды выполняются из корня ветки `hw-3`. Создайте два файла конфигурации. В примере ниже Python генерирует новый секрет Django и пароль БД. Команды рассчитаны на первый запуск.

```bash
python3 - <<'PY'
from pathlib import Path
from secrets import token_urlsafe

template = Path(".env.example").read_text()
template = template.replace("DJANGO_SECRET_KEY=\n", f"DJANGO_SECRET_KEY={token_urlsafe(48)}\n")
template = template.replace("POSTGRES_PASSWORD=\n", f"POSTGRES_PASSWORD={token_urlsafe(32)}\n")
for filename, host in [(".env.local", "127.0.0.1"), (".env.docker", "db")]:
    with open(filename, "x") as env_file:
        env_file.write(template.replace("POSTGRES_HOST=127.0.0.1", f"POSTGRES_HOST={host}"))
PY
```

## Запуск в Docker

```bash
docker compose up --build -d
docker compose exec web python manage.py createsuperuser
```

Перейдите на [главную страницу](http://localhost:8000/) или в [админку](http://localhost:8000/admin/). При запуске веб-контейнер дожидается готовности PostgreSQL и применяет миграции. Команда `docker compose down` останавливает сервисы. Именованный том `pgdata` хранит БД между запусками.

## Запуск Django на компьютере

Понадобятся Python 3.12 и PostgreSQL. Можно поднять только базу через Compose и запустить Django локально.

```bash
docker compose up -d --wait db
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Для уже установленного PostgreSQL укажите в `.env.local` имя существующей базы, её владельца, пароль и порт. При таком запуске шаг с Compose можно пропустить.

## Заполнение и проверка

Сразу после миграций сайт работает с пустой базой. Для быстрого просмотра выполните `python manage.py fill_db 5`. Для проверки объёма из задания выполните команду ниже. В Docker добавьте перед ней `docker compose exec web`.

```bash
python manage.py fill_db 10000
```

Каждый запуск добавляет записи одной транзакцией. При коэффициенте 10 000 добавится 10 000 пользователей с профилями, 100 000 вопросов, 1 000 000 ответов, 10 000 тегов и 2 000 000 лайков. Если нужны значения строго выше этих порогов за один запуск, укажите 10 001. Минимальный коэффициент для пустой базы равен 2. Для одного пользователя есть только 110 разных объектов на требуемые 200 лайков.

| Адрес | Что проверить |
| --- | --- |
| `/` | Новые вопросы по дате, поиск по заголовку и тексту, 20 вопросов на страницу |
| `/hot/` | Вопросы по числу лайков, при равенстве выше новый вопрос |
| `/tag/<тег>/` | Вопросы с выбранным тегом. Ссылка есть в карточке и боковой колонке |
| `/question/<id>/` | Текст вопроса, число и список ответов, 30 ответов на страницу |
| `/admin/` | Управление записями, профиль внутри пользователя, ответы внутри вопроса |

Добавьте `?page=2` к адресу для перехода на вторую страницу. Генератор создаёт по 37 ответов у первого вопроса каждой десятки. Отсутствующий вопрос или тег возвращает HTTP 404. Отладочная панель подключается при `DJANGO_DEBUG=1`.

Для автоматической проверки страниц, количества SQL-запросов, объёмов заполнения и ограничений лайков выполните `DJANGO_DEBUG=0 python manage.py test`. Пользователю PostgreSQL для запуска тестов требуется право создания тестовой базы.

[Условия ДЗ 3](https://github.com/Highoc/web-tasks/blob/master/homeworks/markdown/task-3.md)
