import fitz  # PyMuPDF
from celery import chain, shared_task
from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File
from loguru import logger

from edu_programs.models import (
    EducationGroup,
    EduDegree,
    FederalStateEducationStandard,
    ProfessionalStandard,
    ProfessionalStandardGroup,
    Program,
    University,
)
from edu_programs.parsers.pdf_parsers import vsu_document_parser
from edu_programs.parsers.web_parsers import (
    extract_fgos_education_standards,  # парсинг программ с сайта фгос
    extract_fgos_professional_standards,  # парсинг стандартов с сайта фгос
    extract_vsu_education_programs,  # парсинг с сайта вгу
)


def save_professional_standards(standards_df, program):
    """Связывает профессиональные стандарты с программой."""
    if standards_df is None or standards_df.empty:
        return

    for _, row in standards_df.iterrows():
        code = row["Код"].split(".")
        group_code, code = code[0], code[1]
        try:
            standard = ProfessionalStandard.objects.get(code=code, professional_standard_group__code=group_code)
            program.professional_standards.add(standard)
        except ProfessionalStandard.DoesNotExist:
            logger.warning(f"Профессиональный стандарт с кодом {group_code}.{code} не найден")


@shared_task(bind=True)
def parse_fgos_professional_standards(self):
    """Создает модели ProfessionalStandard на основе данных с сайта ФГОС."""
    try:
        standards_data = extract_fgos_professional_standards()

        created_count = 0
        for data in standards_data:
            # Проверяем, существует ли уже стандарт с таким кодом
            if not (
                ProfessionalStandard.objects.filter(
                    code=data["code"],
                    professional_standard_group__name=data["group_name"],
                )
                .select_related("professional_standard_group__name")
                .exists()
            ):
                group, _ = ProfessionalStandardGroup.objects.get_or_create(
                    code=data["group_code"],
                    defaults={"name": data["group_name"], "code": data["group_code"]},
                )
                ProfessionalStandard.objects.create(
                    name=data["name"],
                    professional_standard_group=group,
                    code=data["code"],
                )
                created_count += 1

    except Exception as e:
        logger.exception(f"Ошибка при парсинге профессиональных стандартов: {e}")
        raise self.retry(exc=e) from None

    else:
        return f"Создано {created_count} профессиональных стандартов"


@shared_task(bind=True)
def parse_fgos_education_standards(self):
    """Создает модели FederalStateEducationStandard на основе данных с сайта ФГОС."""
    try:
        standards_data = extract_fgos_education_standards()

        created_count = 0
        for data in standards_data:
            # Проверяем, существует ли уже стандарт с таким кодом
            if not (
                FederalStateEducationStandard.objects.filter(
                    code=data["code"],
                    edu_degree__code=data["degree_code"],
                    edu_group__code=data["group_code"],
                )
                .select_related("edu_degree__code", "edu_group__code")
                .exists()
            ):
                edu_group, _ = EducationGroup.objects.get_or_create(
                    code=data["group_code"],
                    defaults={"name": data["group_name"], "code": data["group_code"]},
                )
                edu_degree = EduDegree.objects.get(code=data["degree_code"])
                FederalStateEducationStandard.objects.create(
                    name=data["name"],
                    edu_group=edu_group,
                    edu_degree=edu_degree,
                    code=data["code"],
                )
                created_count += 1

    except Exception as e:
        logger.exception(f"Ошибка при парсинге образовательных стандартов: {e}")
        raise self.retry(exc=e) from None

    else:
        return f"Создано {created_count} образовательных стандартов"


@shared_task(bind=True)
def parse_vsu_education_programs(self):  # noqa: ARG001
    """Создает модели Program на основе данных с сайта ВУЗа."""
    programs_data = extract_vsu_education_programs(download=True)
    university = University.objects.get(abbreviation="ВГУ")

    created_count = 0

    for data in programs_data:
        # Проверяем, существует ли уже программа с такими же данными
        try:
            with fitz.open(data["file_path"]) as doc:
                page_text = doc[0].get_text(sort=True)
                if not page_text:
                    logger.info(f"{data['file_path']} | нет текста на странице")
                    continue
                document_parse_data = vsu_document_parser(page_text, university)

            if "faculty" not in document_parse_data:
                logger.warning(f"Факультет не найден | {data['file_path'].stem}")
                continue

            if not (
                Program.objects.filter(
                    code=data["code"],
                    edu_degree__code=data["degree_code"],
                    edu_group__code=data["group_code"],
                    profile=data.get("profile", ""),
                    approval_year=int(data.get("year")),
                    faculty__name=document_parse_data["faculty"],
                )
                .select_related("edu_degree__code", "edu_group__code")
                .exists()
            ) and data.get("file_path"):
                # data["file_path"].unlink()  # noqa: ERA001

                try:
                    edu_group = EducationGroup.objects.get(code=data["group_code"])
                except ObjectDoesNotExist:
                    logger.warning(f"Общая группа ОП - {data['group_code']} - отсутствует в базе")
                    continue
                edu_degree = EduDegree.objects.get(code=data["degree_code"])

                with open(data["file_path"], "rb") as f:
                    program = Program.objects.create(
                        name=data["name"],
                        edu_group=edu_group,
                        edu_degree=edu_degree,
                        code=data["code"],
                        university=university,
                        profile=data.get("profile", ""),
                        approval_year=data.get("year"),
                        document=File(f, name=data["file_path"].name),
                        faculty=document_parse_data["faculty"],
                    )
                created_count += 1

                # Сохраняем связанные проф.стандарты
                save_professional_standards(document_parse_data["professional_standards"], program)

                program.save()

        except Exception as e:
            logger.exception(f"Ошибка при парсинге образовательных программ: {e}")
            continue

    return f"Создано {created_count} образовательных программ"


@shared_task(bind=True)
def initial_setup_tasks(self):
    """Выполняет все задачи сбора данных последовательно."""
    try:
        chain(
            parse_fgos_professional_standards.s(),
            parse_fgos_education_standards.s(),
            parse_vsu_education_programs.s(),
        ).apply_async(queue="default")
    except Exception as e:
        logger.exception(f"Ошибка при выполнении начальных задач: {e}")
        raise self.retry(exc=e) from None
    else:
        return "Все начальные задачи успешно запущены"


# Порядок запуска
# 1) parse_fgos_professional_standards
# 2) parse_fgos_education_standards
# 3) parse_vsu_education_programs
