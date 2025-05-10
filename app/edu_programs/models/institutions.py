from core.models import BaseModel
from django.db import models


class University(BaseModel):
    """Модель высшего учебного заведения."""

    name = models.CharField(max_length=255, verbose_name="Название")
    short_name = models.CharField(max_length=50, verbose_name="Аббревиатура")
    established = models.PositiveIntegerField(verbose_name="Год основания")

    class Meta:
        verbose_name = "ВУЗ"
        verbose_name_plural = "ВУЗы"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.short_name


class Faculty(BaseModel):
    """Модель факультета."""

    university = models.ForeignKey(
        University,
        on_delete=models.CASCADE,
        related_name="faculties",
        verbose_name="ВУЗ",
    )
    name = models.CharField(max_length=255, verbose_name="Название")
    code = models.CharField(max_length=20, verbose_name="Код факультета")

    class Meta:
        verbose_name = "Факультет"
        verbose_name_plural = "Факультеты"
        constraints = [
            models.UniqueConstraint(
                fields=["university", "code"],
                name="unique_faculty_code",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.university.short_name} | {self.name}"
