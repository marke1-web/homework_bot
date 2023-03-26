import logging
import os
import sys
import time
from datetime import datetime
from http import HTTPStatus

import requests
from dotenv import load_dotenv
import telegram

from exceptions import (
    EndpointUnavailableError,
    ResponseError,
    RequestError,
    SendMessageError,
    WrongStatusError,
)


logger = logging.getLogger(__name__)

load_dotenv()


PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RETRY_PERIOD = 600
ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}


HOMEWORK_VERDICTS = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания.",
}


def check_tokens() -> bool:
    """Проверяем, что все необходимые переменные окружения существуют."""
    tokens = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    for token in tokens:
        if not token:
            logging.critical(
                f"Отсутствует обязательная переменная окружения: {token}"
            )
            return False
    return True


def send_message(bot, message):
    """Отправляет сообщение `message` в указанный telegram-чат."""
    try:
        logger.info("Попытка отправить сообщение в чат.")
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug("Сообщение доставлено успешно!.")

    except telegram.TelegramError:
        logger.error("Не удалось отправить сообщение в Telegram.")
        raise SendMessageError("Не удалось отправить сообщение в Telegram.")


def get_api_answer(timestamp):
    """Отправляет запрос к эндпоинту с временной меткой."""
    headers = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}
    params = {"from_date": timestamp}
    try:
        logger.info(f"Отправка запроса к  Практикуму с параметрами: {params}.")
        homework_status = requests.get(ENDPOINT, headers=headers,
                                       params=params)
        if homework_status.status_code == HTTPStatus.NOT_FOUND:
            raise EndpointUnavailableError(
                "Эндпоинт Практикум недоступен. Код ошибки: 404."
            )
        if homework_status.status_code != HTTPStatus.OK:
            raise ResponseError(
                f"При запросе к сервису Практикуму возникла ошибка."
                f"Код ошибки: {homework_status.status_code}."
            )
        return homework_status.json()
    except requests.exceptions.RequestException as error:
        raise RequestError(f"Сбой при запросе к сервису Практикума: {error}.")


def check_response(response):
    """
    Проверка ответа API на корректность.
    доступный в ответе по ключу `homeworks`.
    """
    if not isinstance(response, dict):
        raise TypeError(
            f"Ответ сервиса не является словарем. Ответ сервиса {response}."
        )

    if not response.get("current_date"):

        raise KeyError("В полученном ответе отсутствует ключ `current_date`.")

    if not response.get("homeworks"):
        raise KeyError("В полученном ответе отсутствует ключ `homeworks`.")

    homeworks = response.get("homeworks")

    if not isinstance(homeworks, list):
        raise TypeError(
            f"Значение по ключу `homeworks` не является списком."
            f"Ответ сервиса: {homeworks}"
        )

    if not homeworks:

        logger.info("Значение по ключу `homeworks` - пустой список.")

    return homeworks


def parse_status(homework):
    """Получает на вход одну домашнюю работу, возвращает ее статус."""
    homework_name = homework.get("homework_name")
    status = homework.get("status")

    if not (status and homework_name):
        raise KeyError(
            "В ответе отсутствуют ключи `homework_name` и/или `status`"
        )

    if status not in HOMEWORK_VERDICTS:
        raise WrongStatusError("Получен некорректный статус работы.")

    verdict = HOMEWORK_VERDICTS.get(status)

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def get_timestamp(time) -> int:
    """.
    Функция в качестве параметра получает работу и возвращает время
    последнего изменения статуса этой работы в формате Unix time.
    """
    time_update_date = time.get("date_updated")
    time_update_datetime = datetime.strptime(
        time_update_date, "%Y-%m-%dT%H:%M:%SZ"
    )
    time_update_timestamp = int(time_update_datetime.timestamp())
    return time_update_timestamp


def main() -> None:
    """Основная логика работы бота."""
    if not check_tokens():
        sys.exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    while True:
        try:
            response: dict = get_api_answer(timestamp)
            homework: dict = check_response(response)
            if homework:
                message: str = parse_status(homework[0])
                send_message(bot, message)
            else:
                message: str = "Нет новых данных за послденюю неделю"

        except Exception as error:
            message = f"Сбой в работе программы: {error}"
            logging.error(message)
            send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == "__main__":
    main()
