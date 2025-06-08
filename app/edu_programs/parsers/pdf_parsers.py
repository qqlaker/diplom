import re
from difflib import get_close_matches

import pandas as pd
from loguru import logger

from edu_programs.models import Faculty, University


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

    if program_info and "Факультет" in program_info and str(program_info["Факультет"]) != "None":
        faculty_name = program_info["Факультет"]
        all_faculties = Faculty.objects.filter(university=university)
        faculty_names = [f.name for f in all_faculties]

        matches = get_close_matches(faculty_name, faculty_names, n=1, cutoff=0.6)
        if matches:
            result["faculty"] = all_faculties.get(name=matches[0])
        else:
            logger.warning(f"Факультет не найден | {faculty_name}")

    return result
