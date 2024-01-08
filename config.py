DROP_DB_ON_START = True
MEXC_HOST = 'https://api.mexc.com'
DB_URL = 'sqlite:///DB/tokens.db'
TOKENS_ON_HOLD = ['USDT', 'MX', 'MATH']  # todo проверять до операций торгов - можно менять!
STEPS = {
    'spot': False,
    'convert': True,
    'threshold': False,
}
TIMING = {
    'price_check': 10,      # Время в сек. на анализ порога в $5
    'spot': 10,             # Время в сек. на торговлю
    'convert': 20,          # Время в сек. на конвертацию в MX
    'threshold': 2,         # Количество операций по достижению минимального порога сделки
    'delay': 1,             # Задержки в сек. между операциями
    'check': 10,            # Время в мин. для проверки наличия новых токенов
}