from django.apps import AppConfig


class EduProgramsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "edu_programs"

    def ready(self):
        # Импортируем сигналы только после полной загрузки приложения
        import edu_programs.signals  # noqa: F401
