from core.models import BaseModel
from django.db import models

from .institutions import Faculty


class EducationalProgram(BaseModel):
    """Модель образовательной программы (ОПОП)."""

    DEGREE_CHOICES = [
        ("bachelor", "Бакалавриат"),
        ("master", "Магистратура"),
        ("specialist", "Специалитет"),
    ]

    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.CASCADE,
        related_name="programs",
        verbose_name="Факультет",
    )
    name = models.CharField(max_length=255, verbose_name="Название")
    code = models.CharField(max_length=50, verbose_name="Код программы")
    degree = models.CharField(
        max_length=20,
        choices=DEGREE_CHOICES,
        verbose_name="Уровень образования",
    )
    approval_date = models.DateField(verbose_name="Дата утверждения")
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    description = models.TextField(blank=True, verbose_name="Описание")

    class Meta:
        verbose_name = "Образовательная программа"
        verbose_name_plural = "Образовательные программы"
        ordering = ["faculty", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["faculty", "code"],
                name="unique_program_code",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.code} {self.name}"
