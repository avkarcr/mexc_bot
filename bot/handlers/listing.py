import re

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

listing_router = Router()


def check_token(token_name):
    pattern = r'^[A-Z]{1,30}$'
    return bool(re.match(pattern, token_name))

def check_listing_time(listing_time):
    pattern = r'^(?:\d{2}\.\d{2}\.(?:\d{4})?\s)?\d{2}:\d{2}(?::\d{2})?$'
    return bool(re.match(pattern, listing_time))  # todo не проходит дата 04.01 12:00

def check_args(args):
    if len(args) == 1:
        return (False, 'Формат команды: listing TOKEN ДД.ММ ЧЧ:ММ (или просто ЧЧ:ММ, если дата - сегодня).')
    args = args[1].split(maxsplit=1)
    if not check_token(args[0]):
        return (False, 'Неправильный формат названия токена.')
    try:
        if not check_listing_time(args[1]):
            return (False, 'Неправильный формат времени.')
    except IndexError:
        return (False, 'Задайте время листинга для токена.')
    return (True, '')

@listing_router.message(Command("listing"))
async def command_listing_handler(message: Message) -> None:
    """
    This handler receives messages with `/listing` command
    """
    args = message.text.split(maxsplit=1)
    if not check_args(args)[0]:
        await message.answer(check_args(args)[1])
        return
    await message.answer('Зашибись!!')

    # mexc = listing_router.parent_router.mexc
    # await mexc.update_balance()
    # balance = next((item['free'] for item in mexc.current_balance if item['asset'] == 'USDT'), None)
    # tokens_to_sell = '\n'.join(_ for _ in mexc.tokens_to_sell)
    # # await message.edit_text('wwwwwwwwww')  # todo сделать исчезновение часов
    # await message.answer(f'Баланс USDT: {balance}')
    # await message.answer(tokens_to_sell)
