import re  # noqa: INP001

import fitz
import pandas as pd
from edu_programs.pdf_parsers.base import clean_text, custom_extract_from_section, text_between_header_and_number


def get_qualification(text: str, header: str):
    section_text = text_between_header_and_number(text, header)
    if section_text is None:
        return None

    # Разделяем по двоеточию и берем вторую часть
    parts = section_text.split(":", 1)
    if len(parts) < 2:  # noqa: PLR2004
        return None

    qualification = parts[1]

    # Очищаем результат
    qualification = qualification.strip()

    # Удаляем точку в конце если есть
    qualification = qualification.removesuffix(".")

    return qualification or None


def get_duration_years(text: str, header: str):
    section_text = text_between_header_and_number(text, header, skip=6)
    if section_text is None:
        return None
    return int(m[1]) if (m := re.search(r"(\d+)\s*(?:год[ау]?|лет|г\.?)", section_text, flags=re.IGNORECASE)) else None


def get_total_credits(text: str, header: str):
    section_text = text_between_header_and_number(text, header, skip=6)
    if section_text is None:
        return None
    return (
        int(m[1])
        if (m := re.search(r"(\d+)\s*зач[ёе]тн[а-яё]*\s*единиц", section_text, flags=re.IGNORECASE))
        else None
    )


def get_contact_hours(text: str, header: str):
    section_text = text_between_header_and_number(text, header, skip=5)
    if section_text is None:
        return None
    return (
        int(m[1])
        if (m := re.search(r"(\d+)\s*(?:академических\s*)?час[а-яё]*", section_text, flags=re.IGNORECASE))
        else None
    )


def extract_program_info(doc: fitz.Document, content_df: pd.DataFrame):
    result = {
        "Код направления": None,
        "Название направления": None,
        "Профиль образовательной программы": None,
        "Присваиваемая квалификация": None,
        "Срок обучения": None,
        "Общее количество зачётных единиц": None,
        "Язык обучения": "Русский",
        "Минимальный объём контактной работы (в часах)": None,
        "Год утверждения": None,  # TODO добавить парсинг года  # noqa: FIX002, TD002, TD004
    }
    # код и название
    pattern = r"направлению подготовки(?:/[\w\s]+)?[\s/]+(\d{2}\.\d{2}\.\d{2})[\s]+([^\n,.]+)"
    match = re.search(pattern, clean_text(doc[3].get_text()))
    if match:
        result["Код направления"] = match.group(1)
        result["Название направления"] = match.group(2).rsplit("представля", 1)[0].strip()

    # профиль
    pattern = r"Профиль образовательной программы[^\w]*(?:в рамках направления подготовки)?[^\w]*([\w\s-]+)\."
    for page in doc:
        text = clean_text(page.get_text())
        match = re.search(pattern, text)
        if match:
            result["Профиль образовательной программы"] = match.group(1).strip().capitalize()
            break

    # Присваиваемая квалификация
    result["Присваиваемая квалификация"] = custom_extract_from_section(
        content_df,
        doc,
        r"\bквалификац(?:ия|ии|ию|ией|ий)\b",
        get_qualification,
    )
    # срок обучения
    result["Срок обучения"] = custom_extract_from_section(
        content_df,
        doc,
        r"\bсрок\b",
        get_duration_years,
    )
    # Общее количество зачётных единиц
    result["Общее количество зачётных единиц"] = custom_extract_from_section(
        content_df,
        doc,
        r"\объ(?:е|ё)м программы\b",
        get_total_credits,
    )
    # Минимальный объём контактной работы (в часах)
    result["Минимальный объём контактной работы (в часах)"] = custom_extract_from_section(
        content_df,
        doc,
        r"\контактн(?:ой|ая) работ(?:ы|а)\b",
        get_contact_hours,
    )

    return result
