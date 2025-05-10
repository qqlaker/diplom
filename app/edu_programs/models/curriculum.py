from core.models import BaseModel
from django.db import models

from .competencies import Competence
from .education import EducationalProgram


class Discipline(BaseModel):
    """Модель учебной дисциплины."""

    program = models.ForeignKey(
        EducationalProgram,
        on_delete=models.CASCADE,
        related_name="disciplines",
        verbose_name="Образовательная программа",
    )
    name = models.CharField(max_length=500, verbose_name="Название")
    code = models.CharField(max_length=50, verbose_name="Код дисциплины")
    semester = models.PositiveSmallIntegerField(verbose_name="Семестр")
    credits = models.PositiveSmallIntegerField(verbose_name="Кредиты")
    competences = models.ManyToManyField(
        Competence,
        related_name="disciplines",
        blank=True,
        verbose_name="Формируемые компетенции",
    )

    class Meta:
        verbose_name = "Дисциплина"
        verbose_name_plural = "Дисциплины"
        ordering = ["program", "semester", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["program", "code"],
                name="unique_discipline_code",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.code} {self.name}"
