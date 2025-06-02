import re

import fitz
import pandas as pd
from edu_programs.const import CONTENT_PAGE_COUNT_LIMIT, VSU_CONTENT_COLUMNS
from edu_programs.pdf_parsers.base import clean_text


def extract_text_content_to_pandas(text: str):
    lines = text.split("\n")
    cleaned_lines = [line.strip() for line in lines if line.strip()]

    # Удаляем лишние элементы (номера страниц в начале и конце)
    cleaned_lines = [line for i, line in enumerate(cleaned_lines) if i > 2]

    # Собираем данные
    data = []
    current_item = ""
    page_num = None

    for line in cleaned_lines:
        # Проверяем, является ли строка номером страницы
        if re.fullmatch(r"\d+", line):
            page_num = line
            if current_item:
                # Удаляем точки и лишние пробелы из названия раздела
                clean_item = re.sub(r"[\.\s]+$", "", current_item.strip())
                clean_item = re.sub(r"\s+", " ", clean_item)
                data.append((clean_item, page_num))
                current_item = ""
        elif current_item:
            current_item += " " + line
        else:
            current_item = line

    # Создаем DataFrame
    df = pd.DataFrame(data, columns=["СОДЕРЖАНИЕ", "Col1"])

    # Удаляем строки с пустыми значениями
    return df.dropna()


def extract_content_to_pandas(page: fitz.Page):
    try:
        content_table = page.find_tables().tables[0]
        content_df = content_table.to_pandas()
    except IndexError:
        content_df = extract_text_content_to_pandas(page.get_text().strip())

    if "содержание" not in [item.lower() for item in content_df.columns]:
        content_df = content_df.columns.to_frame().T._append(content_df, ignore_index=True)  # noqa: SLF001

    content_df.columns = VSU_CONTENT_COLUMNS[1:]
    content_df[[VSU_CONTENT_COLUMNS[:1][0], "section"]] = content_df["section"].str.split(" ", n=1, expand=True)

    content_df["index"] = content_df["index"].str.strip(".")
    content_df = content_df.map(clean_text)
    content_df = content_df.reindex(columns=VSU_CONTENT_COLUMNS)

    return content_df[~content_df.iloc[:, 0].str.lower().str.contains(r"приложени(?:я|е)", na=False)]


def check_and_update_page_numbers(df, doc):
    updated_rows = []

    for _, row in df.iterrows():
        possible_title = [
            clean_text(f"{row['index']}. {row['section']}".lower().replace("е", "о").replace("ё", "о")),
            clean_text(f"{row['index']} {row['section']}".lower().replace("е", "о").replace("ё", "о")),
        ]

        actual_page = None
        for i in range(3, CONTENT_PAGE_COUNT_LIMIT):
            page_text = clean_text(doc[i].get_text().lower().replace("е", "о").replace("ё", "о"))

            for title in possible_title:
                if title in page_text:
                    actual_page = i + 1

        new_row = row.copy()
        new_row["page"] = actual_page if actual_page is not None else row["page"]
        updated_rows.append(new_row)

    return pd.DataFrame(updated_rows)
