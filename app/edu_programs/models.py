from core.models import BaseModel
from django.core.files.storage import FileSystemStorage
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


fgos_storage = FileSystemStorage(location="uploads/fgos/")
opop_storage = FileSystemStorage(location="uploads/opop/")


class University(BaseModel):
    name = models.CharField(_("Полное наименование вуза"), max_length=255)
    abbreviation = models.CharField(_("Сокращённое название"), max_length=50, unique=True)

    class Meta:
        verbose_name = _("Университет")
        verbose_name_plural = _("Университеты")

    def __str__(self):
        return self.abbreviation


class Faculty(BaseModel):
    university = models.ForeignKey(
        University,
        on_delete=models.CASCADE,
        verbose_name=_("ВУЗ"),
    )
    name = models.CharField(_("Полное название факультета"), max_length=255)
    abbreviation = models.CharField(_("Сокращение"), max_length=50, unique=True)

    class Meta:
        verbose_name = _("Факультет")
        verbose_name_plural = _("Факультеты")

    def __str__(self):
        return self.abbreviation


class ProfessionalStandardGroup(BaseModel):
    name = models.CharField(_("Название группы"), max_length=255)
    code = models.CharField(_("Код группы"), max_length=20, unique=True)

    class Meta:
        verbose_name = _("Обобщенная группа ПС")
        verbose_name_plural = _("Обобщенные группы ПС")

    def __str__(self):
        return self.name


class EducationGroup(BaseModel):
    name = models.CharField(_("Название группы"), max_length=255)
    code = models.CharField(_("Код группы"), max_length=20, unique=True)

    class Meta:
        verbose_name = _("Обобщенная группа ОП")
        verbose_name_plural = _("Обобщенные группы ОП")

    def __str__(self):
        return self.name


class ProfessionalStandard(BaseModel):
    name = models.CharField(_("Название стандарта"), max_length=255)
    professional_standard_group = models.ForeignKey(
        ProfessionalStandardGroup,
        on_delete=models.CASCADE,
        verbose_name=_("Обобщенная группа проф-стандартов"),
        max_length=255,
    )
    code = models.CharField(_("Код профессионального стандарта"), max_length=20)

    class Meta:
        verbose_name = _("Профессиональный стандарт")
        verbose_name_plural = _("Профессиональные стандарты")

    def __str__(self):
        return self.name


class EduDegree(BaseModel):
    name = models.CharField(_("Наименование"), max_length=100)
    code = models.CharField(_("Код степени образования"), max_length=20)

    class Meta:
        verbose_name = _("Степень образования")
        verbose_name_plural = _("Степень образования")

    def __str__(self):
        return self.name


class FederalStateEducationStandard(BaseModel):  # образовательные программы с сайта ФГОС
    name = models.CharField(_("Название"), max_length=255)
    edu_group = models.ForeignKey(
        EducationGroup,
        on_delete=models.CASCADE,
        verbose_name=_("Обобщенная группа образовательных программ"),
    )
    edu_degree = models.ForeignKey(
        EduDegree,
        verbose_name=_("Степень образования"),
        on_delete=models.CASCADE,
        blank=True,
    )
    code = models.CharField(_("Код"), max_length=20)

    class Meta:
        verbose_name = _("Федеральный образовательный стандарт ФГОС")
        verbose_name_plural = _("Федеральные образовательные стандарты ФГОС")

    def __str__(self) -> str:
        return (
            f"{self.edu_group.code}.{self.edu_degree.code}.{self.code} - {self.name}"
            if self.code
            else f"Образовательный стандарт (ID: {self.id})"
        )


class Program(BaseModel):  # образовательные программы с сайта ВУЗов
    name = models.CharField(_("Название направления подготовки"), max_length=255, blank=True)
    edu_group = models.ForeignKey(
        EducationGroup,
        on_delete=models.CASCADE,
        verbose_name=_("Обобщенная группа образовательных программ"),
    )
    edu_degree = models.ForeignKey(
        EduDegree,
        verbose_name=_("Степень образования"),
        on_delete=models.CASCADE,
        blank=True,
    )
    code = models.CharField(_("Код"), max_length=20)
    university = models.ForeignKey(University, on_delete=models.CASCADE, verbose_name=_("ВУЗ"))
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, verbose_name=_("Факультет"))
    profile = models.TextField(_("Профиль образовательной программы"), blank=True)
    approval_year = models.IntegerField(
        _("Год начала подготовки"),
        blank=True,
        null=True,
        validators=[
            MinValueValidator(1900),
            MaxValueValidator(3000),
        ],
    )
    professional_standards = models.ManyToManyField(
        ProfessionalStandard,
        verbose_name=_("Профессиональные стандарты"),
        blank=True,
    )
    document = models.FileField(
        _("Файл документа ОПОП"),
        upload_to="opop_documents/",
        unique=True,
        storage=opop_storage,
        blank=True,
        null=True,
        max_length=500,
    )

    class Meta:
        verbose_name = _("Образовательная программа ВУЗа")
        verbose_name_plural = _("Образовательные программы ВУЗов")

    def __str__(self) -> str:
        return (
            f"{self.edu_group.code}.{self.edu_degree.code}.{self.code} - {self.name}"
            if self.code
            else f"Программа (ID: {self.id})"
        )

    def delete(self, *args, **kwargs):
        """Переопределяем метод delete для корректного удаления файла."""
        self.document.delete(save=False)  # Удаляет файл через storage
        super().delete(*args, **kwargs)
