import fitz
import pandas as pd
from rapidfuzz import fuzz, process


def clean_text(text):
    """Очищает текст от переносов строк и дефисов."""
    if isinstance(text, str):
        return text.replace("\n", " ").replace("- ", "").replace("  ", " ")
    return text


def text_between_header_and_number(text: str, header: str, skip: int = 0):  # skip - пропустить N цифр
    # Находим начало раздела
    if not header:  # можно не передавать header, если нужно искать сначала страницы
        header_pos = 0
    else:
        header_pos = text.find(header)
        if header_pos == -1:
            return None

    # Находим конец раздела - следующая цифра после заголовка
    skipped = 0
    next_number_pos = None
    for i in range(header_pos + len(header), len(text)):
        if text[i].isdigit():
            next_number_pos = i
            if skipped == skip:
                break
            skipped += 1

    # Вырезаем текст раздела
    if next_number_pos is None:
        section_text = text[header_pos + len(header) :]
    else:
        section_text = text[header_pos + len(header) : next_number_pos]

    return section_text


def merge_rows_with_empty_first_column(df: pd.DataFrame):
    # Получаем список всех столбцов
    columns = df.columns.tolist()

    # Инициализируем список для хранения объединенных строк
    merged_data = []
    current_row = None

    for _, row in df.iterrows():
        # Если первый столбец не пустой
        if row[columns[0]]:
            # Если есть текущая строка, сохраняем ее
            if current_row is not None:
                merged_data.append(current_row)

            # Начинаем новую строку
            current_row = row.to_dict()
        elif current_row is not None:
            for col in columns[1:]:  # Объединяем все столбцы кроме первого
                if row[col]:  # Если значение не пустое
                    if current_row[col]:  # Если в текущей строке уже есть значение
                        current_row[col] += " " + row[col]
                    else:
                        current_row[col] = row[col]

    # Добавляем последнюю строку, если она есть
    if current_row is not None:
        merged_data.append(current_row)

    # Создаем новый DataFrame
    return pd.DataFrame(merged_data, columns=columns).map(clean_text)


def custom_extract_from_section(content_df, doc, section_pattern, extract_func) -> None:
    rows = content_df[content_df["section"].str.contains(section_pattern, case=False, regex=True, na=False)]
    extracted_data = None

    if len(rows) > 0:
        if not str(rows.iloc[0]["page"]).isdigit():
            return None  # попадаем сюда если названия разделов не соответствуют содержанию

        row_index = int(rows.iloc[0]["page"]) - 1
        section = rows.iloc[0]["section"]

        for i in range(row_index, row_index + 3):  # проверяем текущую страницу и две следующих
            text = clean_text(doc[i].get_text())

            if i != row_index:
                section = ""

            extracted_data = extract_func(text, section)

            if extracted_data is not None:
                return extracted_data

    return extracted_data


def define_table_coords(doc: fitz.Document, start_string: str, end_string: str):
    start_string_data = {"page": None, "coords": None}
    end_string_data = {"page": None, "coords": None}

    for page in doc:
        start_possible_items = page.search_for(start_string)
        if len(start_possible_items) > 0:
            start_string_data["page"] = page.number
            start_string_data["coords"] = start_possible_items[-1]

        try:
            if "Таблица" not in start_string:
                raise ValueError  # noqa: TRY301
            possible_variants = [end_string, f"{start_string[:-1]}{int(start_string.split(' ')[1].split('.')[1]) + 1}"]
        except ValueError:
            possible_variants = [end_string]

        for variant in possible_variants:
            end_possible_items = page.search_for(variant)
            if len(end_possible_items) > 0:
                end_string_data["page"] = page.number
                end_string_data["coords"] = end_possible_items[0]
                continue

    if start_string_data["page"] is None or end_string_data["page"] is None:
        return None

    start_index = start_string_data["page"]
    end_index = end_string_data["page"]

    if start_string_data["coords"][1] > 760:
        start_index += 1
    if end_string_data["coords"][1] < 60:
        end_index -= 1

    start_data = {"start_index": start_index, "start_coords": start_string_data["coords"]}
    end_data = {"end_index": end_index, "end_coords": end_string_data["coords"]}

    return start_data, end_data


def extract_table_between_strings(
    doc: fitz.Document,
    start_string: str,
    end_string: str,
    clip_area: fitz.Rect | None = None,
):
    start_data, end_data = define_table_coords(doc, start_string, end_string)

    tables = doc[start_data["start_index"]].find_tables(clip=clip_area).tables
    table_df = None
    for table in tables:
        table_df = table.to_pandas()

    # присоединение оставшейся части таблицы
    for page in doc[start_data["start_index"] + 1 : end_data["end_index"] + 1]:
        tables = page.find_tables(clip=clip_area).tables

        for table in tables:
            # Избегаем таблиц, которые по координатам выше, чем end_string
            if page.number == end_data["end_index"] and table.bbox[1] > end_data["end_coords"][1]:
                continue

            new_table_df = table.to_pandas()

            # Если названия колонок извлеклись неправильно, убираем данные на первую строку датафрейма
            new_table_df = new_table_df.columns.to_frame().T._append(new_table_df, ignore_index=True)  # noqa: SLF001

            new_table_df.columns = table_df.columns
            table_df = pd.concat([table_df, new_table_df], ignore_index=True)
            break

    table_df = table_df.replace(to_replace=r"^Col\d+$", value="", regex=True)
    table_df.columns = table_df.columns.map(clean_text)
    table_df = table_df.map(clean_text)

    # Если первая строка содержит правильные названия колонок
    if table_df.iloc[0, 0] == "Код":
        # Делаем первую строку заголовками
        table_df.columns = table_df.iloc[0]
        # Удаляем первую строку
        table_df = table_df[1:].reset_index(drop=True)

    return table_df


def find_page_with_text(doc, text: str):
    content_page = None
    for page in doc:
        page_text = page.get_text()
        if text in page_text.lower():
            content_page = page
            break
    return content_page


def find_relevant_strings(source, choices, limit=None, score_cutoff=50):
    """Находит текст, наиболее релевантный исходному.

    Параметры:
    - source: исходная строка для сравнения
    - choices: список строк, среди которых ищем похожие
    - limit: максимальное количество возвращаемых результатов (None - все)
    - score_cutoff: минимальный порог схожести (0-100)

    Возвращает список кортежей (строка, оценка) отсортированных по убыванию схожести
    """
    return process.extract(
        source,
        choices,
        scorer=fuzz.WRatio,  # Используем взвешенное отношение (лучший алгоритм для общего случая)
        limit=limit,
        score_cutoff=score_cutoff,
    )
