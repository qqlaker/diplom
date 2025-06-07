import locale
from os import getenv
from pathlib import Path

from celery.schedules import timedelta


locale.setlocale(locale.LC_TIME, "ru_RU.UTF-8")


BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = getenv("SECRET_KEY")

DEBUG = getenv("DEBUG") == "True"

if DEBUG:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0", "diplom"]  # noqa: S104
    CSRF_TRUSTED_ORIGINS = []
else:
    ALLOWED_HOSTS = ["diplom"]
    CSRF_TRUSTED_ORIGINS = []


INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_celery_results",
    "django_celery_beat",
    "django_filters",
    "rest_framework",
    "rest_framework.authtoken",
    "drf_spectacular",
    "simple_history",
    "core",
    "edu_programs.apps.EduProgramsConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
]


ROOT_URLCONF = "settings.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "settings.wsgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": getenv("POSTGRES_DB"),
        "USER": getenv("POSTGRES_USER"),
        "PASSWORD": getenv("POSTGRES_PASSWORD"),
        "HOST": getenv("POSTGRES_HOST", "db"),
        "PORT": getenv("POSTGRES_PORT", "5432"),
    },
}


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


LANGUAGE_CODE = "ru-ru"

TIME_ZONE = "Europe/Moscow"

USE_I18N = True

USE_TZ = True

USE_L10N = True


CELERY_RESULT_BACKEND = "django-db"
CELERY_BROKER_URL = getenv("REDIS_URL")
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Europe/Moscow"
CELERY_ENABLE_UTC = True
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60

CELERY_TASK_QUEUES = {
    "documents": {
        "exchange": "high_priority",
        "exchange_type": "direct",
        "routing_key": "high_priority",
        "queue_arguments": {"x-max-priority": 10},
    },
    "default": {
        "exchange": "default",
        "exchange_type": "direct",
        "routing_key": "default",
        "queue_arguments": {"x-max-priority": 10},
    },
}

CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 4


STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "mediafiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Reaper API",
    "VERSION": "1.0.0",
}

JAZZMIN_SETTINGS = {
    "show_ui_builder": True,
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": False,
    "accent": "accent-primary",
    "navbar": "navbar-white navbar-light",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": True,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": True,
    "theme": "united",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-outline-primary",
        "secondary": "btn-outline-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
    "actions_sticky_top": False,
}


ANALYTICS_CONFIG = {
    "DEMAND_WEIGHTS": {
        "employment": 0.6,
        "disciplines": 0.4,
    },
    "UNIQUE_WEIGHTS": {
        "competencies": 0.7,
        "disciplines": 0.3,
    },
}


CELERY_BEAT_SCHEDULE = {
    "parse_fgos_professional_standards": {
        "task": "edu_programs.tasks.parse_fgos_professional_standards",
        "schedule": timedelta(days=1),
        "options": {"queue": "default"},
        "enabled": False,
    },
    "parse_fgos_education_standards": {
        "task": "edu_programs.tasks.parse_fgos_education_standards",
        "schedule": timedelta(days=1),
        "options": {"queue": "default"},
        "enabled": False,
    },
    "parse_vsu_education_programs": {
        "task": "edu_programs.tasks.parse_vsu_education_programs",
        "schedule": timedelta(days=1),
        "options": {"queue": "default"},
        "enabled": False,
    },
}
