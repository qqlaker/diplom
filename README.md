# diplom

## How to start project
* Install [Python](https://www.python.org/downloads/).
* Install [poetry](https://python-poetry.org).
* Install [Docker](https://docs.docker.com/engine/install/)
* Install [docker-compose](https://docs.docker.com/compose/install/)
* Create .env file
* Run command `poetry install && poetry shell`
* Run command `make install-pre-commit`
* Run command `make up`
* Run command `make migrate`
* Run command `make createsuperuser`


# Для запуска в production
- Добавляем в docker-compose.yml nginx контейнер, настраиваем конфиг для него.
- В настройках nginx указывается домен
- В настройках django (../app/settings/base.py) меняем ALLOWED_HOSTS и CSRF_TRUSTED_ORIGINS, добавляя ip сервера и домен.
- Можно настроить доступ с ssl и без него. В первом случае потребуется дополнительно добавить сертификаты на сервер и прописать их в nginx конфиге.
- Запускаем проект на сервере по инструкции выше. При правильной настройке должен быть доступ к админке по адресу http(s)://имя домена/admin.
