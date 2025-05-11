from xls2xlsx import XLS2XLSX
from openpyxl import load_workbook
import os
import requests
import datetime
import asyncio
import logging
import traceback
import tempfile

from dbrequests import delete_outdated_schedules, update_schedule

# Настройка логирования в stdout
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

time_from_pair = {
    "1 пара": "8:20-9:50",
    "2 пара": "10:00-11:30",
    "3 пара": "11:45-13:15",
    "4 пара": "14:00-15:30",
    "5 пара": "15:45-17:15",
    "6 пара": "17:20-18:50",
    "7 пара": "18:55-20:15",
}

user_agent = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36"
}
url_site = "https://www.vyatsu.ru/studentu-1/spravochnaya-informatsiya/zanyatost-auditoriy.html"

async def get_content(url):
    logger.info(f"Запрос контента с {url}")
    response = requests.get(url, headers=user_agent)
    response.raise_for_status()
    return response

async def get_urls(response):
    list_urls = []
    text: str = response.text

    while True:
        index = text.find('href="/reports/')
        if index == -1:
            break
        start_index = index + len('href="')
        end_index = text.find('"', start_index)
        url = "https://www.vyatsu.ru" + text[start_index:end_index]

        if url.endswith(".xls"):
            try:
                date_str = url[-12:-4]
                last_date = datetime.date(
                    year=int(date_str[-4:]),
                    month=int(date_str[-6:-4]),
                    day=int(date_str[-8:-6]),
                )
                current_date = datetime.date.today()
                if current_date < last_date and (last_date - current_date).days < 180:  # Увеличено до 180 дней
                    list_urls.append(url)
                    logger.info(f"Найдена актуальная ссылка: {url}")
            except Exception as e:
                logger.error(f"Ошибка обработки ссылки {url}: {e}")
                logger.error(traceback.format_exc())
        text = text[end_index:]
    return list_urls

async def download(url: str) -> str:
    response = requests.get(url, headers=user_agent)
    response.raise_for_status()
    filename = url[-25:]
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xls") as temp_file:
        temp_file.write(response.content)
        temp_path = temp_file.name
    logger.info(f"Скачан файл {filename} в {temp_path}")
    return temp_path

async def convert_xls_to_xlsx(path: str) -> str:
    x2x = XLS2XLSX(path)
    xlsx_path = path + "x"
    x2x.to_xlsx(xlsx_path)
    logger.info(f"Конвертирован {path} в {xlsx_path}")
    return xlsx_path

async def parsing_url(url: str) -> None:
    try:
        path = await download(url)
        try:
            xlsx_path = await convert_xls_to_xlsx(path)
            os.remove(path)
            logger.info(f"Удален временный файл {path}")

            wookbook = load_workbook(xlsx_path)
            worksheet = wookbook.active

            for i in range(3, worksheet.max_column):
                cabinet_number: str = worksheet.cell(row=2, column=i).value
                if not cabinet_number:
                    continue

                for j in range(3, worksheet.max_row):
                    time_lesson: str = worksheet.cell(row=j, column=2).value
                    if not time_lesson:
                        continue
                    time_lesson = time_lesson.strip()
                    if time_lesson not in time_from_pair:
                        logger.warning(f"Неизвестное время пары: {time_lesson}")
                        continue
                    time_lesson = time_from_pair[time_lesson]

                    date = worksheet.cell(row=j, column=1).value
                    index_for_day = j - 1
                    while date is None:
                        date = worksheet.cell(row=index_for_day, column=1).value
                        index_for_day -= 1
                    date = date.strip()[-8:]  # dd.mm.yy
                    date_obj = datetime.datetime.strptime(date, "%d.%m.%y")
                    date = date_obj.strftime("%Y-%m-%d")  # Конвертация в YYYY-MM-DD

                    value: str = worksheet.cell(row=j, column=i).value
                    if value and "Резервирование" in value:
                        value = None

                    if value:
                        list_value = value.split("\n") if "\n" in value else [value]
                        list_value = [v.strip() for v in list_value]

                        for ii in range(len(list_value)):
                            if len(list_value[ii].split()[0]) <= 3:
                                list_value[ii] = " ".join(list_value[ii].split()[1:])

                        name_of_group = []
                        name_teacher = []
                        name_of_discipline = []

                        for value in list_value:
                            text_split = value.split()
                            if text_split[-1].count(".") == 2:
                                name_teacher.append(" ".join(text_split[-2:]))
                                text_split = text_split[:-2]
                            else:
                                name_teacher.append(None)

                            if text_split[0][-1] == ",":
                                name_of_group.append(" ".join(text_split[:3]))
                                text_split = text_split[3:]
                            else:
                                name_of_group.append(text_split[0])
                                text_split = text_split[1:]

                            name_of_discipline.append(" ".join(text_split))

                        if len(list_value) == 1:
                            await update_schedule(
                                date,
                                time_lesson,
                                cabinet_number,
                                name_of_group,
                                name_teacher,
                                name_of_discipline,
                            )
                        else:
                            await update_schedule(
                                date,
                                time_lesson,
                                cabinet_number,
                                name_of_group,
                                name_teacher,
                                name_of_discipline,
                                many=True,
                            )
                    else:
                        await update_schedule(
                            date, time_lesson, cabinet_number, None, None, None, empty=True
                        )

            os.remove(xlsx_path)
            logger.info(f"Удален файл {xlsx_path}")
        except Exception as e:
            logger.error(f"Ошибка парсинга файла {url}: {e}")
            logger.error(traceback.format_exc())
        finally:
            if os.path.exists(path):
                os.remove(path)
                logger.info(f"Удален временный файл {path}")
    except Exception as e:
        logger.error(f"Ошибка обработки URL {url}: {e}")
        logger.error(traceback.format_exc())

async def start_parsing_xlsx():
    await delete_outdated_schedules()
    try:
        response = await get_content(url_site)
        urls = await get_urls(response)
        for url in urls:
            await parsing_url(url)
    except Exception as e:
        logger.error(f"Ошибка парсинга: {e}")
        logger.error(traceback.format_exc())

async def start_parsing():
    await start_parsing_xlsx()
