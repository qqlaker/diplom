from django.core.files.storage import FileSystemStorage
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


# Кастомное хранилище для документов
opop_storage = FileSystemStorage(location="uploads/opop/")


class University(models.Model):
    name = models.CharField(_("Полное наименование вуза"), max_length=255)
    abbreviation = models.CharField(_("Сокращённое название"), max_length=50)
    location = models.CharField(_("Местоположение"), max_length=255)
    website = models.URLField(_("Ссылка на официальный сайт"))

    class Meta:
        verbose_name = _("Университет")
        verbose_name_plural = _("Университеты")

    def __str__(self):
        return self.abbreviation


class Faculty(models.Model):
    university = models.ForeignKey(
        University,
        on_delete=models.CASCADE,
        verbose_name=_("ВУЗ"),
    )
    name = models.CharField(_("Полное название факультета"), max_length=255)
    abbreviation = models.CharField(_("Сокращение"), max_length=50)

    class Meta:
        verbose_name = _("Факультет")
        verbose_name_plural = _("Факультеты")

    def __str__(self):
        return self.abbreviation


class ProfessionalStandard(models.Model):
    code = models.CharField(_("Код профессионального стандарта"), max_length=20)
    title = models.CharField(_("Название стандарта"), max_length=255)
    domain = models.CharField(_("Сфера деятельности"), max_length=255)
    order_number = models.CharField(_("Номер приказа утверждения"), max_length=50)
    order_date = models.DateField(_("Дата утверждения"))

    class Meta:
        verbose_name = _("Профессиональный стандарт")
        verbose_name_plural = _("Профессиональные стандарты")

    def __str__(self):
        return self.title


class Competency(models.Model):
    COMPETENCY_TYPES = [
        ("UK", _("Универсальная")),
        ("OPK", _("Общепрофессиональная")),
        ("PK", _("Профессиональная")),
    ]

    type = models.CharField(_("Тип компетенции"), max_length=3, choices=COMPETENCY_TYPES)
    code = models.CharField(_("Код компетенции"), max_length=20)
    description = models.TextField(_("Описание компетенции"))

    class Meta:
        verbose_name = _("Компетенция")
        verbose_name_plural = _("Компетенции")

    def __str__(self):
        return f"{self.code} ({self.get_type_display()})"


class Discipline(models.Model):
    code = models.CharField(_("Код дисциплины"), max_length=20)
    name = models.CharField(_("Название дисциплины"), max_length=255)
    competencies = models.ManyToManyField(
        Competency,
        verbose_name=_("Компетенции"),
    )

    class Meta:
        verbose_name = _("Дисциплина")
        verbose_name_plural = _("Дисциплины")

    def __str__(self):
        return self.name


class Program(models.Model):
    university = models.ForeignKey(
        University,
        on_delete=models.CASCADE,
        verbose_name=_("ВУЗ"),
    )
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.CASCADE,
        verbose_name=_("Факультет"),
    )
    code = models.CharField(_("Код направления подготовки"), max_length=20, blank=True)
    name = models.CharField(_("Название направления подготовки"), max_length=255, blank=True)
    profile = models.TextField(_("Профиль образовательной программы"), blank=True)
    approval_year = models.IntegerField(
        _("Год утверждения"),
        blank=True,
        null=True,
        validators=[
            MinValueValidator(1900),
            MaxValueValidator(2100),
        ],
    )
    qualification = models.CharField(_("Присваиваемая квалификация"), max_length=100, blank=True)
    duration_years = models.IntegerField(_("Срок обучения в годах"), blank=True, null=True)
    total_credits = models.IntegerField(_("Общее количество зачётных единиц"), blank=True, null=True)
    language = models.CharField(_("Язык обучения"), max_length=100, blank=True)
    contact_hours_min = models.IntegerField(_("Минимальный объём контактной работы (в часах)"), blank=True, null=True)
    professional_standards = models.ManyToManyField(
        ProfessionalStandard,
        verbose_name=_("Профессиональные стандарты"),
        blank=True,
    )
    disciplines = models.ManyToManyField(
        Discipline,
        verbose_name=_("Дисциплины"),
        blank=True,
    )
    document = models.FileField(
        _("Файл документа ОПОП"),
        upload_to="opop_documents/",
        unique=True,
        storage=opop_storage,
        blank=True,
        null=True,
    )
    is_processed = models.BooleanField(_("Обработан"), default=False)
    processing_error = models.TextField(_("Ошибка обработки"), blank=True, default="")

    class Meta:
        verbose_name = _("Образовательная программа")
        verbose_name_plural = _("Образовательные программы")

    def __str__(self) -> str:
        return f"{self.code} - {self.name}" if self.code else f"Программа (ID: {self.id})"

    def save(self, *args, **kwargs):
        # При первом сохранении с документом сбрасываем флаг обработки
        error = kwargs.pop("error", None)
        if self.document and not self.is_processed and not error:
            self.is_processed = False
            self.processing_error = None
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Переопределяем метод delete для корректного удаления файла."""
        self.document.delete(save=False)  # Удаляет файл через storage
        super().delete(*args, **kwargs)
