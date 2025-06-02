from pathlib import Path

from celery import current_app
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from loguru import logger

from edu_programs.models import Program


@receiver(post_save, sender=Program)
def start_document_processing(sender, instance, created, **kwargs):  # noqa: ANN001, ANN003, ARG001
    """Автоматически запускает обработку документа при его добавлении/изменении."""
    if instance.document and not instance.is_processed:
        # Запускаем асинхронную задачу обработки документа
        current_app.send_task(
            "edu_programs.tasks.process_uploaded_document",
            args=[instance.id],
            queue="documents",
        )


@receiver(post_delete, sender=Program)
def auto_delete_file_on_delete(sender, instance, **kwargs):  # noqa: ANN001, ANN003, ARG001
    """Удаляет файл из файловой системы при удалении объекта Program."""
    if instance.document and Path.is_file(instance.document.path):
        try:
            Path.unlink(instance.document.path)
        except Exception as e:
            logger.error(f"Ошибка при удалении файла {instance.document.path}: {e}")
