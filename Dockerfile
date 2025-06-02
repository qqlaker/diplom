FROM python:3.12-slim

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

COPY /scripts/wait-for-it.sh /wait-for-it.sh
RUN chmod +x wait-for-it.sh

COPY /scripts/start.sh /start.sh
RUN chmod +x /start.sh

COPY /scripts/start-dev.sh /start-dev.sh
RUN chmod +x /start-dev.sh

COPY poetry.lock pyproject.toml /

RUN apt-get update && \
    apt-get install -y locales && \
    sed -i 's/# ru_RU.UTF-8 UTF-8/ru_RU.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen ru_RU.UTF-8 && \
    update-locale LANG=ru_RU.UTF-8

ENV LANG=ru_RU.UTF-8
ENV LC_ALL=ru_RU.UTF-8

RUN pip install poetry==1.8.2 \
  && poetry config virtualenvs.create false \
  && poetry install --no-dev --no-root

WORKDIR /app

COPY app ./
