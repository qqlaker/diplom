import re
from difflib import get_close_matches

import pandas as pd
from loguru import logger

from edu_programs.models import Faculty, University


def levenshtein_distance(a: str, b: str):
    n = len(a)
    m = len(b)

    if n == 0:
        return m
    if m == 0:
        return n

    prev = list(range(m + 1))
    curr = [0] * (m + 1)

    for i in range(1, n + 1):
        curr[0] = i
        for j in range(1, m + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            deletion = prev[j] + 1
            insertion = curr[j - 1] + 1
            substitution = prev[j - 1] + cost
            curr[j] = min(deletion, insertion, substitution)
        prev = curr.copy()

    return curr[m]


def get_matches(faculty_name: str, faculty_names: list[str], cutoff: float = 0.6):
    best_match = None
    best_similarity = 0.0

    for name in faculty_names:
        dist = levenshtein_distance(faculty_name, name)
        max_len = max(len(faculty_name), len(name))

        similarity = 1.0 if max_len == 0 else 1 - dist / max_len

        if similarity >= cutoff and similarity > best_similarity:
            best_similarity = similarity
            best_match = name

    return best_match


def extract_professional_standards(page_text: str):
    standards_pattern = re.compile(r"(\d{2}\.\d{3})\s+([А-ЯA-Z-][А-ЯA-Z-\s]*[А-ЯA-Z-])(?=\s|$)")
    standards = [
        [
            item[0].strip().replace("\n", ""),
            item[1].strip().replace("\n", "").lower().capitalize(),
        ]
        for item in standards_pattern.findall(page_text)
    ]
    return pd.DataFrame(data=standards, columns=["Код", "Название"])


def extract_program_info(page_text: str):
    faculty_pattern = re.compile(r"Факультет:\s*([^\n]+)")
    faculty_match = faculty_pattern.search(page_text)
    faculty = faculty_match.group(1).strip() if faculty_match else None
    return {"Факультет": faculty}


def vsu_document_parser(page_text: str, university: University):
    result = {}

    result["professional_standards"] = extract_professional_standards(page_text)
    program_info = extract_program_info(page_text)

    # Находим факультет с помощью расстояния Левенштейна
    if program_info and "Факультет" in program_info:
        faculty_name = program_info["Факультет"]
        all_faculties = Faculty.objects.filter(university=university)
        faculty_names = [f.name for f in all_faculties]

        # Используем свою функцию, которая вычисляет схожесть между словами с помощью расстояния Левенштейна
        matches = get_close_matches(faculty_name, faculty_names, n=1, cutoff=0.6)
        if matches:
            result["faculty"] = all_faculties.get(name=matches[0])
        else:
            logger.warning(f"Факультет не найден | {faculty_name}")

    return result
