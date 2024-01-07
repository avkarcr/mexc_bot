DROP_DB_ON_START = True
MEXC_HOST = 'https://api.mexc.com'
DB_URL = 'sqlite:///DB/tokens.db'
TOKENS_ON_HOLD = ['USDT', 'BNB', 'MX', 'MATH']  # todo проверять до операций торгов - можно менять!
TIMING = {
    'price_check': 10,      # Время в сек. на анализ порога в $5
    'spot': 10,             # Время в сек. на торговлю
    'convert': 20,          # Время в сек. на конвертацию в MX
    'buy_to_cover': 2,      # Количество операций обратного откупа
    'delay': 1,             # Задержки в сек. между операциями
    'check': 10,            # Время в мин. для проверки наличия новых токенов
}