from pathlib import Path

from django.db.models.signals import post_delete
from django.dispatch import receiver
from loguru import logger

from edu_programs.models import Program


@receiver(post_delete, sender=Program)
def auto_delete_file_on_delete(sender, instance, **kwargs):  # noqa: ARG001
    """Удаляет файл из файловой системы при удалении объекта Program."""
    if instance.document and Path(instance.document.path).is_file():
        try:
            Path(instance.document.path).unlink()
        except Exception as e:
            logger.error(f"Ошибка при удалении файла {instance.document.path}: {e}")
