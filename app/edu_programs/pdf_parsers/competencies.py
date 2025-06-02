import re
from collections import OrderedDict

import fitz
import pandas as pd
from edu_programs.pdf_parsers.base import (
    clean_text,
    extract_table_between_strings,
    find_relevant_strings,
    merge_rows_with_empty_first_column,
)


def split_competency_entries(cell_text):
    merged_text = " ".join(cell_text.split("\n"))
    split_result = re.split(r"(УК-\d+\.\d+|ОПК-\d+\.\d+|ПК-\d+\.\d+)", merged_text)[1:]
    entries = []

    for i in range(0, len(split_result), 2):
        if i + 1 < len(split_result):
            code = split_result[i].strip()
            description = split_result[i + 1].strip()
            entries.append(f"{code} {description}")

    return entries


def extract_competencies_table(doc, competency):
    start_string = f"Таблица {competency['table_index']}"
    competency_clip_area = fitz.Rect(80, 0, doc[5].rect.width, doc[5].rect.height)

    # если порядок компетенций в содержании документа будет другой, тут потребуются изменения
    match competency["type"]:
        case "Универсальные компетенции":
            end_string = " Общепрофессиональные компетенции выпускников"
        case "Общепрофессиональные компетенции":
            end_string = " Профессиональные компетенции выпускников"
        case "Профессиональные компетенции":
            end_string = " Структура и содержание ОПОП"
        case _:
            end_string = start_string

    table_df = extract_table_between_strings(doc, start_string, end_string, clip_area=competency_clip_area)
    table_df = merge_rows_with_empty_first_column(table_df)
    table_df = table_df.dropna(subset=["Код"])

    table_df = table_df.map(clean_text)
    table_df.columns = table_df.columns.map(clean_text)
    table_df = table_df.iloc[:, -1:]

    table_df = table_df.reset_index(drop=True)

    table_df = table_df.rename(
        columns={table_df.columns[0]: "Код и формулировка компетенции"}
    )  # переименовываем, так как не у всех компетенций одинаковые названия столбцов

    # Применяем к DataFrame и "разворачиваем" список в отдельные строки
    table_df["Код и формулировка компетенции"] = table_df["Код и формулировка компетенции"].apply(
        split_competency_entries
    )
    table_df = table_df.explode("Код и формулировка компетенции").reset_index(drop=True)
    table_df[["Код", "Формулировка компетенции"]] = table_df["Код и формулировка компетенции"].str.split(
        " ", n=1, expand=True
    )
    return table_df.drop(columns="Код и формулировка компетенции").reset_index(drop=True)


def extract_competencies(doc: fitz.Document, content_df: pd.DataFrame):
    competencies = {
        "UK": {"type": "Универсальные компетенции", "page_start": None, "page_end": None},
        "OPK": {"type": "Общепрофессиональные компетенции", "page_start": None, "page_end": None},
        "PK": {"type": "Профессиональные компетенции", "page_start": None, "page_end": None},
    }

    choices = content_df["section"].tolist()

    for competency_text in competencies.values():
        matches = find_relevant_strings(source=competency_text["type"], choices=choices, limit=1)
        if len(matches) == 0:
            continue

        elem = content_df.loc[content_df["section"] == matches[0][0]].iloc[0]
        competency_text["page_start"] = int(elem["page"])
        next_row_index = content_df.loc[content_df["section"] == matches[0][0]].index + 1
        try:
            competency_text["page_end"] = int(content_df.iloc[next_row_index]["page"].iloc[0])
        except KeyError:
            competency_text["page_end"] = content_df.iloc[-1]["page"]
        competency_text["table_index"] = elem["index"]

    sorted_competencies = OrderedDict(sorted(competencies.items(), key=lambda item: item[1]["page_start"]))

    for i, key in enumerate(sorted_competencies.keys()):
        if i == 0:
            continue
        sorted_competencies[key]["page_end"] += 1

    for comp_code in competencies:  # noqa: PLC0206
        try:
            if sorted_competencies[comp_code]["page_start"] and sorted_competencies[comp_code]["page_end"]:
                competencies[comp_code] = extract_competencies_table(doc, competencies[comp_code])
        except Exception:
            competencies[comp_code] = None

    return competencies
