from pathlib import Path


BASE_DIR = Path().cwd()
VSU_CONTENT_COLUMNS = ["index", "section", "page"]
VSU_OP_FILES = BASE_DIR / "edu_programs" / "parsers" / "files"

CONTENT_PAGE_COUNT_LIMIT = 30
DISCIPLINE_TABLE_COLUMNS = ["Индекс", "Наименование", "Формируемые компетенции"]
POSSIBLE_DEGREES = [
    {"name": "бакалавриат", "code": "03", "fgosvo_index": "24"},
    {"name": "магистратура", "code": "04", "fgosvo_index": "25"},
    {"name": "специалитет", "code": "05", "fgosvo_index": "26"},
]
ALLOWED_PROF_STANDARDS = {"06": "all", "40": ["011"]}
ALLOWED_EDU_STANDARDS = ["01", "02", "09"]
ALLOWED_FACULTIES = ["компьютерных наук", "математический", "прикладной математики, информатики и механики"]
