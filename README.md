# Проект Foodgram
[![example event parameter](https://github.com/mdmashdrmsh/foodgram-project-react/actions/workflows/foodgram_workflow.yml/badge.svg)](https://github.com/mdmashdrmsh/foodgram-project-react/actions/workflows/foodgram_workflow.yml)

[![Python](https://img.shields.io/badge/-Python-464646?style=flat-square&logo=Python)](https://www.python.org/)
[![Django](https://img.shields.io/badge/-Django-464646?style=flat-square&logo=Django)](https://www.djangoproject.com/)
[![Django REST Framework](https://img.shields.io/badge/-Django%20REST%20Framework-464646?style=flat-square&logo=Django%20REST%20Framework)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/-PostgreSQL-464646?style=flat-square&logo=PostgreSQL)](https://www.postgresql.org/)
[![Nginx](https://img.shields.io/badge/-NGINX-464646?style=flat-square&logo=NGINX)](https://nginx.org/ru/)
[![gunicorn](https://img.shields.io/badge/-gunicorn-464646?style=flat-square&logo=gunicorn)](https://gunicorn.org/)
[![docker](https://img.shields.io/badge/-Docker-464646?style=flat-square&logo=docker)](https://www.docker.com/)
[![GitHub%20Actions](https://img.shields.io/badge/-GitHub%20Actions-464646?style=flat-square&logo=GitHub%20actions)](https://github.com/features/actions)
[![Yandex.Cloud](https://img.shields.io/badge/-Yandex.Cloud-464646?style=flat-square&logo=Yandex.Cloud)](https://cloud.yandex.ru/)

Foodgram - это продуктовый помощник, сайт, на котором пользователи могут публиковать рецепты, добавлять их в список избранного, так же формировать и выгружать список покупок для выбранных рецептов. Имеется возможность подписываться на авторов. 

Проект доступен по адресу http://foodgram-buaykov.sytes.net/ (51.250.87.39)

## Установка и запуск проекта на локальной машине

Клонировать репозиторий на свой ПК
```
git clone git@github.com:mdmashdrmsh/foodgram-project-react.git
```
Установить виртуальное окружение
```
python -m venv venv
```
Активировать виртуальное окружение
Linux:
```
source venv/bin/activate
```
Windows:
```
source venv/Scripts/activate
```
Перейти в директорию /infra и создать .env файл для хранения переменных виртуального окружения
```
cd infra
touch .env
```
Заполнить файл .env по примеру:
```
DB_ENGINE=django.db.backends.postgresql # указываем, что используем СУБД Postgresql
DB_NAME=postgres # имя БД
POSTGRES_USER=postgres # логин юзера БД
POSTGRES_PASSWORD=postgres # пароль юзера БД
DB_HOST=db # название сервиса (контейнера) на локальной машине указать 127.0.0.1
DB_PORT=5432 # порт для работы с БД
SECRET_KEY=<секретный ключ из settings.py>
```
Перейти в каталог backend, установить зависимости
```
cd ../backend
pip install -r requirements.txt
```
Выполнить миграции
```
python manage.py migrate
```
Создать суперпользователя Django
```
python manage.py createsuperuser
```
Импортировать ингредиенты в БД
```
python manage.py import_ingredients
```
Собрать статику
```
python manage.py collectstatic --no-input
```
Для запуска фронтенд-части проекта установить Node.js v11.13.0-x64
Перейти в каталог фронтенда и запустить npm
```
cd fronend/
npm install
npm start
```
Запустить локальный сервер
```
cd backend/
python manage.py runserver
```

## Запуск проекта на удаленном сервере
Для запуска проекта на удаленном сервере он упаковывается в контейнеры Docker. 
Зайти на удаленный сервер, устаноивить Docker и Docker Compose. Создать или вручную скопировать на сервер конфигурационные файлы docker-compose.yml и nginx.conf из каталога infra/ . Запустить Docker Dompose
```
sudo docker-compose up -d --build
```
В это время Docker Compose создаст четыре контейнера:
- backend
- db
- frontend
- nginx

Далее создать миграции в контейнере backend
```
sudo docker-compose exec backend bash
python manage.py makemigrations users
python manage.py makemigrations recipes
python manage.py migrate
```

Если при работе с проектом на локальной машине Вы заполняли БД тестовыми данными, то их можно перенести дампом json на сервер
Создать дамп на локальной машине
```
python manage.py dumpdata > dump.json
```
Скопировать файл dump.json с локальной машины на сервер
```
scp dump.json <server_user>@<server_ip>:/home/<user>/.../<папка_проекта_с_manage.py>/
```
На сервере
```
sudo docker-compose exec backend bash
python manage.py shell
>>> from django.contrib.contenttypes.models import ContentType
>>> ContentType.objects.all().delete()
>>> quit()
python manage.py loaddata dump.json
python manage.py collectstatic --no-input
```
## Документация
Доступ к документации API на локальной машине
```
cd infra
docker-compose up
```
По адресу http://localhost/api/docs/ будет доступна документация