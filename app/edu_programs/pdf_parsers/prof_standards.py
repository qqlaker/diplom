import re
from datetime import datetime

import fitz
import pandas as pd
from edu_programs.pdf_parsers.base import (
    custom_extract_from_section,
    extract_table_between_strings,
    merge_rows_with_empty_first_column,
    text_between_header_and_number,
)
from loguru import logger


def get_prof_standards_position(text: str, header: str):
    section_text = text_between_header_and_number(text, header, skip=10)
    if section_text is None:
        return None
    if "отсутств" in section_text:
        return "отсутствуют"
    search = re.search(
        r"используемых\s*при\s*формировании\s*ОПОП\s*приведен\s*в*?приложении\s+(\d+)",
        section_text,
        flags=re.IGNORECASE,
    )
    return int(search.group(1)) if search else None


def extract_prof_standards_appendix_number(doc: fitz.Document, content_df: pd.DataFrame):
    """Определяет номер приложения, в котором содержится информация о профессиональных стандартах."""
    first_pos = custom_extract_from_section(
        content_df,
        doc,
        r"перечень\s*профессиональных\s*стандартов\b",
        get_prof_standards_position,
    )
    if first_pos == "отсутствуют":
        return None
    first_pos = 1 if first_pos is None else int(first_pos)
    return first_pos, first_pos + 1


def split_standard_info(text: str):
    # Инициализация результата
    result = {
        "Название": "",
        "Дата утверждения": "",
        "Номер приказа утверждения": "",
    }

    # Извлечение названия стандарта (между « и »)
    title_match = re.search(r"«(.+?)»", text)
    if title_match:
        result["Название"] = title_match.group(1)

    # Извлечение номера приказа и даты утверждения
    approval_match = re.search(r"от (\d{1,2} [а-я]+ \d{4}) г\. № ([\d-]+[а-я]*)", text)
    if approval_match:
        result["Дата утверждения"] = approval_match.group(1)
        result["Номер приказа утверждения"] = approval_match.group(2)

    # Преобразование дат в объекты datetime (опционально)
    try:
        if result["Дата утверждения"]:
            date_str = result["Дата утверждения"].replace("г.", "").strip()
            result["Дата утверждения"] = datetime.strptime(date_str, "%d %B %Y")  # noqa: DTZ007
    except ValueError:
        pass

    return result


def transform_prof_standards_table(df: pd.DataFrame):
    result = pd.DataFrame(
        columns=[
            "№ п/п",
            "Код профессионального стандарта",
            "Наименование профессионального стандарта",
            "Сфера деятельности",
        ],
    )

    current_sphere = ""
    row_num = 1

    for _, row in df.iterrows():
        # Проверка, является ли строка заголовком сферы деятельности
        if row.iloc[0] and not row.iloc[1] and not row.iloc[2]:
            current_sphere = row.iloc[0]
        # Проверка, является ли строка записью стандарта
        elif row.iloc[0] and row.iloc[1] and row.iloc[2]:
            new_row = {
                "№ п/п": str(row_num),
                "Код профессионального стандарта": row.iloc[1],
                "Наименование профессионального стандарта": row.iloc[2],
                "Сфера деятельности": current_sphere,
            }
            result = pd.concat([result, pd.DataFrame([new_row])], ignore_index=True)
            row_num += 1

    return result


def process_prof_standards_table(df: pd.DataFrame):
    df = df.drop(columns="№ п/п")
    df.rename(
        columns={
            "Код профессионального стандарта": "Код",
            "Наименование профессионального стандарта": "Название",
        },
    )
    # извлечение названия, номера приказа утверждения, даты утверждения из столбца
    extracted_data = df["Наименование профессионального стандарта"].apply(lambda x: pd.Series(split_standard_info(x)))
    df = pd.concat([df, extracted_data], axis=1)
    return df.drop(columns="Наименование профессионального стандарта")


def extract_professional_standards(doc: fitz.Document, content_df: pd.DataFrame):
    pos = extract_prof_standards_appendix_number(doc, content_df)
    if pos is None:
        logger.info("Профессиональные стандарты отсутствуют")
        return None
    df = extract_table_between_strings(doc, f"Приложение {pos[0]}\n", f"Приложение {pos[0]}\n")
    df = merge_rows_with_empty_first_column(df)
    df = transform_prof_standards_table(df)
    return process_prof_standards_table(df)
