# Foodgram
Cервис для публикаций рецептов.

С помощью сервиса Foodgram авторизованные пользователи могут добавлять свои рецепты на сайт, смотреть рецепты других пользователей, подписываться на пользователей, добавлять понравившиеся рецепты в список покупок, а также скачивать этот список.

## Стек технологий
Python 3.11
Django 5.1.5
Django REST Framework 3.15.2
PostgreSQL
Docker

## Установка
Для запуска локально, создайте файл `.env` в директории `/backend/` с содержанием:
```
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

DB_NAME=postgres
DB_HOST=db
DB_PORT=5432

SECRET_KEY=django-secret-key
ALLOWED_HOSTS=127.0.0.1, localhost, 0.0.0.0:8000, domain.com
DOMAIN_NAME=domain.com
```

#### Установка Docker
Для запуска проекта вам потребуется установить Docker и docker-compose.

Для установки на ubuntu выполните следующие команды:
```bash
sudo apt install docker docker-compose
```

Про установку на других операционных системах вы можете прочитать в [документации](https://docs.docker.com/engine/install/) и [про установку docker-compose](https://docs.docker.com/compose/install/).

## Как развернуть проект

**Клонируйте репозиторий**:

```bash
git clone git@github.com:abrpcoby/foodgram.git
cd foodgram
```

**Разверните контейнеры**

```bash
docker compose up -d
```

**Выполните миграции и передайте статику с бэкэнда**

```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py collectstatic
```

**Загрузите фикстуры**

```bash
docker compose exec backend python manage.py import_ingredients recipes/data/ingredients.json
docker compose exec backend python manage.py import_tags recipes/data/tags.json
```

**Cоздайте суперпользователя**

```bash
docker compose exec backend python manage.py createsuperuser
```

## Автор

Зуев Павел