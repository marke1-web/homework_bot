class EndpointUnavailableError(Exception):
    """Ошибка, вызванная недоступностью эндпоинта."""

    pass


class HomeworkServiceError(Exception):
    """Ошибка, связанная с работой сервиса проверки домашних заданий."""

    pass


class MissingTokenError(Exception):
    """Ошибка, вызванная отсутствием токена."""

    pass


class ResponseError(Exception):
    """Ошибка, вызванная некорректным ответом от API."""

    pass


class RequestError(Exception):
    """Ошибка, возникшая при запросе к API."""

    pass


class SendMessageError(Exception):
    """Ошибка, возникшая при отправке сообщения в telegram-чат."""

    pass


class WrongStatusError(Exception):
    """Ошибка, вызванная некорректным статусом проверки домашней работы."""

    pass
