# Проект Foodgram


## Стек Технология

[![Django](https://img.shields.io/badge/Django-v4.2.11-blue?style=flat-square&logo=Django)](https://www.djangoproject.com/)
[![Django REST Framework](https://img.shields.io/badge/Django%20REST%20Framework-v3.15.1-blue?style=flat-square&logo=Django%20REST%20Framework)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-v13.0-blue?style=flat-square&logo=PostgreSQL)](https://www.postgresql.org/)
[![nginx](https://img.shields.io/badge/NGINX-v1.21.3-blue?style=flat-square&logo=nginx)](https://nginx.org/ru/)
[![Djoser](https://img.shields.io/badge/djoser-v2.1.0-blue?style=flat-square&logo=djoser)](https://djoser.readthedocs.io/en/latest/getting_started.html)
[![django-filter](https://img.shields.io/badge/django--filter-v24.2-blue?style=flat-square&logo=django-filter)](https://django-filter.readthedocs.io/en/stable/)
[![gunicorn](https://img.shields.io/badge/gunicorn-v20.1.0-blue?style=flat-square&logo=gunicorn)](https://gunicorn.org/)
[![docker](https://img.shields.io/badge/Docker-v25.0.3-blue?style=flat-square&logo=docker)](https://www.docker.com/)
[![docker compose](https://img.shields.io/badge/docker%20compose-v2.24.6-blue?style=flat-square&logo=docker)](https://docs.docker.com/compose/)
[![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-v3.2.5-blue?style=flat-square&logo=GitHub%20actions)](https://github.com/features/actions)

Проект Foodgram разработан для обеспечения пользователей платформой, где они могут делиться и находить новые рецепты, подписываться на понравившихся авторов и удобно планировать покупки для приготовления блюд.

## Описание проекта Foodgram
Foodgram - это современная платформа для публикации, обмена и поиска рецептов, разработанная для любителей кулинарии и гурманов. Сочетая в себе функциональность социальной сети и полезные инструменты планирования, Foodgram обеспечивает пользователей интуитивно понятным и удобным интерфейсом, который позволяет:

**Публикация и обмен рецептами:**
Foodgram позволяет пользователям создавать, публиковать и обмениваться рецептами своих любимых блюд. С поддержкой изображений, описания рецептов и списка ингредиентов, пользователи могут поделиться своими кулинарными творениями и вдохновить других участников платформы.

**Подписка на авторов:**
Пользователи могут подписываться на авторов, чьи рецепты им особенно нравятся. Это позволяет пользователям быть в курсе последних обновлений и находить новые интересные рецепты от предпочитаемых авторов.

**Избранное и покупки:**
Foodgram позволяет пользователям сохранять понравившиеся рецепты в список избранных и составлять список покупок для приготовления выбранных блюд. Это удобный способ планировать покупки и следить за необходимыми ингредиентами.

**Скачивание списка покупок:**
Для удобства пользователей, Foodgram предоставляет возможность скачивать список покупок ингредиентов для рецептов, добавленных в список покупок. Этот список можно использовать при походе в магазин, чтобы не забыть ни одного необходимого ингредиента.

## Подготовка и запуск проекта
### Склонировать репозиторий на локальную машину:
```git
git clone git@github.com:labanurkamal/foodgram-project-react.git
```
## Для работы с удаленным сервером:
**Выполните вход на свой удаленный сервер**
1. **Обновите репозиторий пакетов:**
   ```bash
   sudo apt update
   ```
**Установка Docker на Linux**

2. **Установите curl — консольную утилиту, которая умеет скачивать файлы по команде пользователя:**
   ```bash
   sudo apt install curl
   ```

3. **Скачайте скрипт для установки Docker с официального сайта:**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh 
   ```

4. **Запустите сохранённый скрипт с правами суперпользователя:**
   ```bash
   sudo sh ./get-docker.sh 
   ```

5. **Установите Docker Compose:**
   ```bash
   sudo apt install docker-compose-plugin
   ```

6. **Проверьте, что Docker работает:**
   ```bash
   sudo systemctl status docker
   ```
## Запуск проекта в удаленном сервере:

**Скопируйте файлы docker-compose.yml и nginx.conf из директории infra на сервер:**
   ```bash
   scp docker-compose.yml <username>@<host>:/home/<username>/docker-compose.yml
   scp nginx.conf <username>@<host>:/home/<username>/nginx.conf
   ```
**Cоздайте .env файл и впишите:**
   ```bash
      SECRET_KEY=<секретный ключ проекта>
      DEBUG=<отладочный режим>
      ALLOWED_HOSTS=<список хостов>
      POSTGRES_DB=example
      POSTGRES_USER=example_user
      POSTGRES_PASSWORD=example_password
   ```

## Сборка проекта на сервере:
   ```bash
    sudo docker compose up -d
   ```
   - Собрать статические файлы:
   ```bash
    sudo docker-compose exec backend python manage.py collectstatic --noinput
   ```
   - Применить миграции:
   ```bash
    sudo docker-compose exec backend python manage.py migrate --noinput
   ```
   - Загрузить ингридиенты и тега в базу данных:  
   ```bash
    sudo docker compose exec backend python manage.py data_command --path "data/tags.json"
    sudo docker compose exec backend python manage.py data_command --path "data/ingredients.json"
   ```
   - Создать суперпользователя Django:
   ```bash
    sudo docker-compose exec backend python manage.py createsuperuser
   ```
## Проект в интернете
Проект запущен и доступен по [адресу](https://food-solutions.zapto.org/recipes)