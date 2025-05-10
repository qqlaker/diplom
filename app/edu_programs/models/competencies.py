from core.models import BaseModel
from django.db import models

from .education import EducationalProgram


class ProfessionalStandard(BaseModel):
    """Модель профессионального стандарта."""

    program = models.ForeignKey(
        EducationalProgram,
        on_delete=models.CASCADE,
        related_name="professional_standards",
        verbose_name="Образовательная программа",
    )
    code = models.CharField(max_length=50, unique=True, verbose_name="Код")
    name = models.CharField(max_length=500, verbose_name="Название")
    registration_number = models.CharField(
        max_length=50,
        verbose_name="Регистрационный номер",
    )
    approval_date = models.DateField(verbose_name="Дата утверждения")

    class Meta:
        verbose_name = "Профессиональный стандарт"
        verbose_name_plural = "Профессиональные стандарты"
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code} {self.name}"


class Competence(BaseModel):
    """Модель компетенции образовательной программы."""

    TYPE_CHOICES = [
        ("general", "Общая"),
        ("professional", "Профессиональная"),
        ("digital", "Цифровая"),
    ]

    program = models.ForeignKey(
        EducationalProgram,
        on_delete=models.CASCADE,
        related_name="competences",
        verbose_name="Образовательная программа",
    )
    code = models.CharField(max_length=50, verbose_name="Код")
    name = models.CharField(max_length=1000, verbose_name="Формулировка")
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        verbose_name="Тип компетенции",
    )

    class Meta:
        verbose_name = "Компетенция"
        verbose_name_plural = "Компетенции"
        ordering = ["program", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["program", "code"],
                name="unique_competence_code",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.code} {self.name[:50]}..."
