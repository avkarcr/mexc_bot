# class TokensSaleTime(Base):
#     __tablename__ = 'token_sale_time'
#     id = Column(Integer, primary_key=True)
#     name = Column(String)
#     sale_time = Column(DateTime)
#
# engine = create_engine('sqlite:///token_sale_time.db')
# Base.metadata.create.all(engine)
# Session = sessionmaker(bind=engine)

# def trade_asset_market(mexc_trade, mexc_account, symbol, side):
#     if side == 'BUY':
#         params = {
#             'symbol': symbol + 'USDT',
#             'side': side,
#             'type': 'MARKET',
#             'quoteOrderQty': 6,
#             'quantity': 6,
#         }
#     else:
#         qty = get_balance(mexc_account, symbol)
#         params = {
#             'symbol': symbol + 'USDT',
#             'side': side,
#             'type': 'MARKET',
#             'quoteOrderQty': qty,
#             'quantity': qty,
#         }
#     return mexc_trade.post_order(params)

    # moscow_tz = pytz.timezone('Europe/Moscow')
    # target_time = "01:03:00"
    #
    # while True:
    #     count += 1
    #     now = datetime.datetime.now(moscow_tz).strftime('%H:%M:%S')
    #     print('---------------------------------')
    #     print(f'{now}: Cycle {count % 5}')
    #     if count % 2 == 0:
    #         print('Updating balances...')
    #         mexc.check_balance_changes()
    #
    #     time.sleep(5)

    # trade_asset_market(mexc_trade, mexc_account, dust_asset, 'BUY')
    # time.sleep(1)
    # trade_asset_market(mexc_trade, mexc_account, dust_asset, 'SELL')

    # if dust_asset in assets:
    #     params = {'asset': dust_asset}
    #     capital = mexc_toolkit.mexc_capital(mexc_host, api_key, secret_key)
    #     # resp = capital.post_smallAssets_convert(params=params)
    #     resp = capital.get_smallAssets_list()
    #     for item in resp:
    #         asset = item.get('asset')
    #         balance = item.get('balance')
    #         msg = item.get('message')
    #         print(f'Asset {asset}: Balance: {balance}. Message: {msg}')



import logging
import os
import requests
import time

from dotenv import load_dotenv
from telegram import Bot, TelegramError
from telegram.ext import Updater, Filters, MessageHandler
from http import HTTPStatus

from exceptions import APIErrorException, TelegramSendError


load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 00
ENDPOINT = 'https://api.mexc.com/api/v3/'
HEADERS = {'Authorization': f'OAuth 77777777777'}
START_TIME = 1660900000

STATUSES = []

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s: %(name)s'
)


def send_message(bot, message):
    """Отправка статусного сообщения в телеграмм."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
    except TelegramError as error:
        raise TelegramSendError(
            f'Не удалось отправить сообщение в телеграмм: {error}'
        )
    else:
        logging.info('Отправлено сообщение в телеграмм')


def get_api_answer(current_timestamp):
    """
    Получение ответа API.
    """
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != HTTPStatus.OK:
            msg = 'Ошибка модуля get_api_answer. Свяжитесь с разработчиком'
            raise APIErrorException(msg)
        else:
            return response.json()
    except Exception as error:
        msg = f'Ошибка соединения: {error}'
        raise APIErrorException(msg)


def check_response(response):
    """Проверка ответа API на корректность."""
    if not isinstance(response, dict):
        raise TypeError('Ответ от сервера пришел не в виде dict')
    if response.get('smth') is None:
        msg = 'Ошибка API: в ответе нет ключа'
        raise APIErrorException(msg)
    if response.get('current_date') is None:
        msg = 'Ошибка API: в ответе нет ключа current_date'
        raise APIErrorException(msg)
    if not isinstance(response.get('smth'), list):
        raise TypeError('Ответ вернул объект, отличный от типа list')

    return response.get('smth')


def parse_status(smth):
    """Обработка полученного ответа API."""
    resp = smth.get('smth')
    if resp is None:
        raise KeyError('В ответе сервера нет имени')
    status = smth.get('status')
    if status not in STATUSES:
        raise KeyError('В ответе сервера нет статуса')
    status = STATUSES[status]

    return f'Изменился статус "{resp}": {status}'


def check_tokens():
    """Проверка наличия необходимых токенов"""
    return all((TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def inform_user(bot, bot_instructions):
    """Делаем логи и информируем пользователя в телеграмм о результатах."""
    if bot_instructions['send_to_telegram']:
        last_msg = bot_instructions['last_message']
        current_msg = bot_instructions['current_message']
        log_type = {
            'info': logging.info,
            'warning': logging.warning,
            'error': logging.error
        }

        if last_msg == '':
            msg = '### Bot is alive ###'
        elif current_msg != last_msg:
            msg = current_msg
        else:
            return

        send_message(bot, msg)
        log_type[bot_instructions['type']](
            bot_instructions['current_message']
        )
        bot_instructions['last_message'] = current_msg
    else:
        logging.error(bot_instructions['current_message'])


def say_hi(update, context):
    chat = update.effective_chat
    context.bot.send_message(chat_id=chat.id, text='RRrrrrrrrrr')


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical('Отсутствуют обязательные переменные окружения!')
        exit()

    bot = Bot(token=TELEGRAM_TOKEN)
    updater = Updater(token=TELEGRAM_TOKEN)

    text = 'Test'
    bot.send_message(TELEGRAM_CHAT_ID, text)

    updater.dispatcher.add_handler(MessageHandler(Filters.text, say_hi))
    updater.start_polling()
    updater.idle()

    exit()
    # telegram.error.Unauthorized: Forbidden: bot was blocked by the user
    # telegram.error.BadRequest: Chat not found

    current_timestamp = START_TIME

    # instructions for the bot to send specific messages
    # types are: 'info', 'error', 'warning'
    bot_instructions: dict = {
        'send_to_telegram': True,
        'last_message': '',
        'current_message': '',
        'type': ''
    }

    while True:
        try:
            response = get_api_answer(current_timestamp)
            if len(response.get('smth')) == 0:
                msg = 'Статус не изменился'
            else:
                result = check_response(response)[0]
                msg = parse_status(result)
            current_timestamp = response.get('current_date')
            bot_instructions['send_to_telegram'] = True
            bot_instructions['current_message'] = msg
            bot_instructions['type'] = 'info'
        except TelegramSendError as error:
            bot_instructions['send_to_telegram'] = False
            bot_instructions['current_message'] = error.args[0]
            bot_instructions['type'] = 'error'
        except Exception as error:
            bot_instructions['send_to_telegram'] = True
            bot_instructions['current_message'] = error.args[0]
            bot_instructions['type'] = 'error'

        inform_user(bot, bot_instructions)

        time.sleep(RETRY_TIME)


