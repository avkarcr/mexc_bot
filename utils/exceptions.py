class DBInteractionException(Exception):
    """Исключение для контроля ошибок взаимодействия с БД."""

    pass

class DateTimeParseException(Exception):
    """Исключение для контроля ошибок парсинга даты."""

    pass

class MexcAPIException(Exception):
    """Исключение для контроля ошибок работы с API MEXC."""

    pass
