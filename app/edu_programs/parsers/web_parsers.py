from __future__ import annotations

import re
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup
from loguru import logger

from edu_programs.const import ALLOWED_EDU_STANDARDS, ALLOWED_PROF_STANDARDS, POSSIBLE_DEGREES, VSU_OP_FILES


def make_request(
    method,
    url,
    params=None,
    proxy=None,
    payload=None,
    headers=None,
    cookies={},  # noqa: B006
    retry_statuses=None,
    attempts=5,
    request_name="",
    timeout=6,
    stream=None,  # noqa: ARG001
) -> requests.Response:
    """Метод для выполнения запроса в несколько попыток."""
    if headers is None:
        headers = {}
    if payload is None:
        payload = {}
    if params is None:
        params = {}
    if retry_statuses is None:
        retry_statuses = [503]

    response = None
    status_code = 0

    while status_code != 200:  # noqa: PLR2004
        if attempts <= 0:
            logger.info(f"Исчерпано кол-во попыток запроса {request_name}")
            break
        try:
            logger.info(f"{method} | {request_name} | {proxy}")

            response = requests.request(
                method,
                url,
                params=params,
                headers=headers,
                cookies=cookies,
                json=payload,
                proxies=proxy,
                timeout=timeout,
            )
            status_code = response.status_code
            logger.info(f"Response status_code: {status_code}\n")

            if response is not None and response.status_code != 200:  # noqa: PLR2004
                logger.info(f"status code {response.status_code} | Попытка повторного запроса...")
                attempts -= 1

        except Exception as e:
            logger.warning(e)
            logger.info("Exception | Попытка повторного запроса...")
            attempts -= 1

    return response


def remove_brackets(text):
    # Удаляем содержимое круглых скобок с поддержкой вложенности
    while re.search(r"\([^()]*\)", text):
        text = re.sub(r"\([^()]*\)", "", text)

    # Удаляем содержимое квадратных скобок (без вложенности)
    text = re.sub(r"\[.*?\]", "", text)

    # Удаляем возможные двойные пробелы после удаления
    return re.sub(r"\s+", " ", text).strip()


def download_pdf(url: str, save_path: str):
    try:
        response = make_request(method="GET", url=url, stream=True)
        response.raise_for_status()  # Проверяем, что запрос успешен

        with open(save_path, "wb+") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

    except Exception:  # noqa: S110
        pass


def parse_fgos_edu(method: str, url: str, inner_class: str):
    results = []

    next_page = True
    page = 1
    while next_page:
        response = make_request(method=method, url=url, params={"page": page}, request_name="fgos_standards_inner")
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "html.parser")
        if (
            page > 15  # noqa: PLR2004
            or (inner_class == "me-2" and soup.find_next("li", attrs={"class": "page-item next disabled"}))
            or (inner_class == "w80 me-2" and page > 3)  # noqa: PLR2004
        ):
            next_page = False

        programs = soup.find_all("div", attrs={"class": "item d-flex"})

        for item in programs:
            inner_item = item.find_next("div", attrs={"class": "d-flex"})
            full_code = inner_item.find_next("div", attrs={"class": inner_class}).text.strip(".").split(".")

            if inner_class == "me-2":  # noqa: SIM102
                if not (
                    ALLOWED_PROF_STANDARDS[full_code[0]] == "all"
                    or full_code[1] in ALLOWED_PROF_STANDARDS[full_code[0]]
                ):
                    continue

            inner_item = item.find_next("div", attrs={"class": "d-flex"})
            results.append(
                {
                    "name": inner_item.find_all("div")[2].text,
                    "code": inner_item.find_next("div", attrs={"class": inner_class}).text.strip(".").split(".")[-1],
                },
            )
        page += 1

    return results


def extract_fgos_education_standards():
    results = []

    for degree_info in POSSIBLE_DEGREES:
        degree_code = degree_info["code"]
        url_index = degree_info.get("fgosvo_index")
        if not url_index:
            continue
        response = make_request(
            method="GET",
            url=f"https://fgosvo.ru/fgosvo/index/{url_index}",
            request_name="fgos_standards",
        )
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "html.parser")
        fgos_programs = soup.find_all("div", attrs={"class": "item d-flex"})

        for item in fgos_programs:
            group_code = item.find_next("div", attrs={"class": "w112 text-green align-middle"}).text[:2]
            if group_code not in ALLOWED_EDU_STANDARDS:
                continue

            item_link = item.find_next("a", attrs={"class": "item-link"})
            group_name = item_link.text.lower().capitalize()
            url = f"https://fgosvo.ru{item_link['href']}"

            [
                results.append(
                    {
                        "group_name": group_name,
                        "group_code": group_code,
                        "degree_code": degree_code,
                        "name": result["name"],
                        "code": result["code"],
                    },
                )
                for result in parse_fgos_edu("GET", url, "w80 me-2")
            ]

    return results


def extract_fgos_professional_standards():
    results = []

    for page in range(1, 3):
        response = make_request(
            method="GET",
            url=f"https://fgosvo.ru/docs/index/2?page={page}",
            request_name="fgos_professional_standards",
        )
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "html.parser")
        fgos_standards = soup.find_all("div", attrs={"class": "item d-flex"})

        for item in fgos_standards:
            group_code = item.find_next("div", attrs={"class": "w80 text-green align-middle"}).text
            if group_code not in ALLOWED_PROF_STANDARDS:
                continue
            item_link = item.find_next("a", attrs={"class": "item-link"})
            group_name = item_link.text.lower().capitalize()
            url = f"https://fgosvo.ru{item_link['href']}"

            [
                results.append(
                    {
                        "group_name": group_name,
                        "group_code": group_code,
                        "name": result["name"],
                        "code": result["code"],
                    },
                )
                for result in parse_fgos_edu("GET", url, "me-2")
            ]

    return results


def extract_vsu_education_programs(download=True):
    results = []

    response = make_request(method="GET", url="https://www.vsu.ru/sveden/education/oop.html")
    response.encoding = "utf-8"
    soup = BeautifulSoup(response.text, "html.parser")

    tabs = soup.find_all("div", attrs={"class": "tab-pane"})
    for tab in tabs:
        try:
            year = tab["id"].replace("tab", "")
            edu_programs = tab.find_all("tr", attrs={"itemprop": "eduOp"})

            for i, item in enumerate(edu_programs):
                degree = item.find("td", attrs={"itemprop": "eduLevel"}).text
                if degree.rsplit("–")[-1].strip() not in [elem["name"] for elem in POSSIBLE_DEGREES]:
                    continue
                if item.find("td", attrs={"itemprop": "eduForm"}).text != "очная":
                    continue
                code = item.find("td", attrs={"itemprop": "eduCode"}).text.split(".")
                group_code, degree_code, code = code[0], code[1], code[2]
                name = item.find("td", attrs={"itemprop": "eduName"}).text
                profile = re.findall(r'["\'](.*?)["\']', name)
                profile = profile[0] if len(profile) > 0 else None
                name = remove_brackets(name).strip()
                plan_href = item.find("td", attrs={"itemprop": "educationPlan"})
                plan_href = plan_href.find_next("a") if plan_href.text.lower() != "нет" else None
                if plan_href is None:
                    continue
                plan_href = unquote(plan_href.get("href", ""))
                plan_name = plan_href.rsplit("/")[-1]
                if str(plan_name) == "None":
                    continue
                file_path = VSU_OP_FILES / plan_name

                if download:
                    logger.info(f"Скачивание файла номер: {i}")
                    download_pdf(plan_href, file_path)

                results.append(
                    {
                        "group_code": group_code,
                        "degree_code": degree_code,
                        "code": code,
                        "name": name,
                        "year": year,
                        "profile": profile or "",
                        "file_path": file_path,
                    },
                )

        except Exception as e:
            logger.exception(f"Ошибка при обращении к сайту ВГУ: {e}")
            continue

    return results
