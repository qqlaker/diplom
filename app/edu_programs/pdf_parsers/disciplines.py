import re

import fitz
import pandas as pd
from edu_programs.const import DISCIPLINE_TABLE_COLUMNS
from edu_programs.pdf_parsers.base import (
    custom_extract_from_section,
    define_table_coords,
    text_between_header_and_number,
)


def divide_into_blocks(text: str):
    r"""Разделяет текст на блоки, начинающиеся с 'Б\\d+\\..+\\..+'."""
    lines = text.split("\n")

    # Компилируем регулярное выражение для поиска строк, начинающихся с Б+цифры и содержащих минимум две точки
    pattern = re.compile(r"^Б\d+\..+\..+")

    blocks = []
    current_block = []

    for line in lines:
        line = line.strip()  # noqa: PLW2901

        if pattern.match(line):
            if current_block:
                blocks.append(current_block)
            current_block = [line]

        elif line and current_block:
            current_block.append(line)

    # Добавляем последний блок
    if current_block:
        blocks.append(current_block)

    return "\n\n".join(["\n".join(block) for block in blocks])


def get_disciplines_position(text: str, header: str):
    section_text = text_between_header_and_number(text, header, skip=20)
    if section_text is None:
        return None
    search = re.search(
        r"индикаторов их достижения и элементов ОПОП.*?приложении\s+(\d+)", section_text, flags=re.IGNORECASE
    )
    return int(search.group(1)) if search else None


def extract_disciplines_appendix_number(doc: fitz.Document, content_df: pd.DataFrame):
    """Определяет номер приложения, в котором содержится информация о дисциплинах."""
    first_pos = custom_extract_from_section(
        content_df, doc, r"структура\s*и\s*объ(?:е|ё)м\s*опоп\b", get_disciplines_position
    )
    first_pos = 3 if first_pos is None else int(first_pos)
    return first_pos, first_pos + 1


def combine_same_type_text(block: list[str]):
    result = []
    temp = []
    flag = None

    while len(block) > 0:
        item = block.pop(0).strip()

        if flag is None:
            flag = get_record_type(item)
            temp.append(item)
            continue

        next_item_flag = get_record_type(item)
        if flag != next_item_flag:
            result.append(" ".join(temp))
            temp = []
            flag = next_item_flag

        temp.append(item)

    result.append(" ".join(temp))
    return result


def get_record_type(text: str):
    if re.match(r"^(Б\d|ФТД)\.*", text):
        return "Бint"
    if re.match(r"^(УК|ОПК|ПК)-\d+\.\d+", text):
        return "УК-ОПК-ПК"
    if not text:
        return "empty"
    return "text"


def extract_disciplines_table(doc: fitz.Document, start_string: str, end_string: str):
    start_data, end_data = define_table_coords(doc, start_string, end_string)
    start_index = start_data["start_index"]
    end_index = end_data["end_index"]

    results = []
    for i in range(start_index, end_index):
        data = doc[i].get_text().strip()

        for _j in range(3):  # удаление из начала лишнего текста
            data = data.split("\n", 1)[1].strip()

        data = data.replace("\n \n", "\n")

        # Разделяем текст по двум переносам строки (пустым строкам)
        data = divide_into_blocks(data)

        blocks = data.split("\n\n")
        blocks = [item.split("\n") for item in blocks]

        # Если есть блоки по типу ['Б1.В.ДВ.06.02', 'Объемное моделирование пластовых', 'систем', 'ПК-4.1'], объединяем описание в них
        blocks = [combine_same_type_text(item) for item in blocks]
        # Чистка пустых строк
        blocks = [item for item in blocks if len(item) == 3]  # noqa: PLR2004

        results.extend(blocks)

    return pd.DataFrame(results, columns=DISCIPLINE_TABLE_COLUMNS).dropna(subset=[DISCIPLINE_TABLE_COLUMNS[1]])


def process_disciplines_table(df: pd.DataFrame):
    return df.rename(
        columns={
            "Индекс": "Код",
            "Наименование": "Название",
            "Формируемые компетенции": "Компетенции",
        }
    )


def extract_disciplines(doc: fitz.Document, content_df: pd.DataFrame):
    pos = extract_disciplines_appendix_number(doc, content_df)
    df = extract_disciplines_table(doc, f"Приложение {pos[0]}\n", f"Приложение {pos[1]}\n")
    return process_disciplines_table(df)
