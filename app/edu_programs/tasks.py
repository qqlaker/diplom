import logging

import fitz  # PyMuPDF
from celery import shared_task
from pandas import DataFrame

from edu_programs.models import Competency, Discipline, ProfessionalStandard, Program
from edu_programs.pdf_parsers.base import find_page_with_text
from edu_programs.pdf_parsers.competencies import extract_competencies
from edu_programs.pdf_parsers.content import (
    check_and_update_page_numbers,
    extract_content_to_pandas,
)
from edu_programs.pdf_parsers.disciplines import extract_disciplines
from edu_programs.pdf_parsers.prof_standards import extract_professional_standards
from edu_programs.pdf_parsers.program_info import extract_program_info


logger = logging.getLogger(__name__)


def save_competencies(competencies_data: dict):
    """Сохраняет компетенции в базу данных и связывает с программой."""
    saved_competencies = {}

    for comp_type, df in competencies_data.items():
        for _, row in df.iterrows():
            code = row["Код"].strip()
            description = row["Формулировка компетенции"].strip()

            competency, _created = Competency.objects.update_or_create(
                code=code,
                defaults={
                    "type": comp_type,
                    "description": description,
                },
            )
            saved_competencies[code] = competency

    return saved_competencies


def save_professional_standards(standards_df: DataFrame, program: Program):
    """Сохраняет профессиональные стандарты и связывает с программой."""
    saved_standards = {}

    for _, row in standards_df.iterrows():
        code = row["Код профессионального стандарта"].strip()
        title = row["Название"].strip()
        domain = row["Сфера деятельности"].strip()
        order_number = row["Номер приказа утверждения"].strip()
        order_date = row["Дата утверждения"].date()

        standard, created = ProfessionalStandard.objects.update_or_create(
            code=code,
            defaults={
                "title": title,
                "domain": domain,
                "order_number": order_number,
                "order_date": order_date,
            },
        )
        saved_standards[code] = standard
        program.professional_standards.add(standard)

    return saved_standards


def save_disciplines(disciplines_df: DataFrame, saved_competencies: dict, program: Program):
    """Сохраняет дисциплины и их связи с компетенциями и программой."""
    saved_disciplines = {}

    for _, row in disciplines_df.iterrows():
        code = row["Код"].strip()
        name = row["Название"].strip()

        discipline, created = Discipline.objects.update_or_create(
            code=code,
            defaults={"name": name},
        )

        comp_codes = [c.strip() for c in row["Компетенции"].split(";") if c.strip()]
        for comp_code in comp_codes:
            if comp_code in saved_competencies:
                discipline.competencies.add(saved_competencies[comp_code])

        saved_disciplines[code] = discipline
        program.disciplines.add(discipline)

    return saved_disciplines


@shared_task(bind=True)
def process_uploaded_document(self, program_id: int):  # noqa: ARG001
    logger.info(f"Обработка документа ID: {program_id} запущена")  # noqa: G004

    try:
        program = Program.objects.get(id=program_id)
        if not program.document or program.is_processed:
            return True

        # Парсим документ
        with fitz.open(program.document.path) as doc:
            # Извлекаем содержание
            content_page = find_page_with_text(doc, "содержание")
            content_df = extract_content_to_pandas(content_page)
            content_df = check_and_update_page_numbers(content_df, doc)

            # Извлекаем данные
            competencies = extract_competencies(doc, content_df)
            professional_standards = extract_professional_standards(doc, content_df)
            disciplines = extract_disciplines(doc, content_df)
            program_info = extract_program_info(doc, content_df)

        # Обновляем основную информацию о программе
        program.code = program_info.get("Код направления", "")
        program.name = program_info.get("Название направления", "")
        program.profile = program_info.get("Профиль образовательной программы", "")
        program.qualification = program_info.get("Присваиваемая квалификация", "")
        program.duration_years = int(program_info.get("Срок обучения"))
        program.total_credits = int(program_info.get("Общее количество зачётных единиц"))
        program.language = program_info.get("Язык обучения", "Русский")
        program.contact_hours_min = int(program_info.get("Минимальный объём контактной работы (в часах)"))
        program.approval_year = program_info.get("Год утверждения")

        # Сохраняем связанные данные
        saved_competencies = save_competencies(competencies)
        save_professional_standards(professional_standards, program)
        save_disciplines(disciplines, saved_competencies, program)

        # Помечаем программу как обработанную
        program.is_processed = True
        program.processing_error = None
        program.save()

    except Exception as e:
        logger.exception(f"Ошибка обработки программы {program_id}: {e!s}", exc_info=True)  # noqa: G004, G202, TRY401
        program.is_processed = False
        program.processing_error = str(e)
        program.save(error=True)

    else:
        return True
