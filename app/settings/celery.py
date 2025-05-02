import os

from celery import Celery


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.base")

app = Celery("Diplom")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.update(worker_max_tasks_per_child=100)

app.conf.task_queue_max_priority = 10
app.conf.task_default_priority = 5

app.autodiscover_tasks()
