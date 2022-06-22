# marketplace-api #
Yandex academy test task

# Описание #
В данном проекте реализован CRUD АПИ сервис, с дополнительным функционалом.
Подробное описание доступных запросов можно посмотреть в файле openapi.yaml

# Технологии #
1) Django
2) Django Rest Framework
3) Celery
4) PostgreSQL
5) Docker

# Как запустить #

1) Склонируйте репозиторий: git clone https://github.com/NiroTime/marketplace-api
2) В дерикрории ~/marketplace запустите контейнеры: docker-compose up -d
3) Выполните миграции: docker-compose exec web python manage.py migrate --noinput