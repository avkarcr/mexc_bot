class APIErrorException(Exception):
    """Исключение для контроля ошибок взаимодействия с API."""

    pass


class TelegramSendError(Exception):
    """Исключение для ошибки отправки сообщения в телеграмм."""

    pass
