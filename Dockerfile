FROM python:3.12-slim

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Установка системных зависимостей
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    locales \
    build-essential \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && sed -i 's/# ru_RU.UTF-8 UTF-8/ru_RU.UTF-8 UTF-8/' /etc/locale.gen \
    && locale-gen ru_RU.UTF-8 \
    && update-locale LANG=ru_RU.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

ENV LANG=ru_RU.UTF-8
ENV LC_ALL=ru_RU.UTF-8

# Копирование скриптов и установка прав
COPY /scripts/wait-for-it.sh /wait-for-it.sh
COPY /scripts/start.sh /start.sh
COPY /scripts/start-dev.sh /start-dev.sh
RUN chmod +x /wait-for-it.sh /start.sh /start-dev.sh

# Установка Poetry и зависимостей
COPY poetry.lock pyproject.toml /
RUN pip install poetry==1.8.2 \
    && poetry config virtualenvs.create false \
    && poetry install --no-dev --no-root

WORKDIR /app
COPY app ./
