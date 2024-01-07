from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

start_router = Router()


@start_router.message(Command("start"))
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    # await message.answer('⏳')
    mexc = start_router.megabot.mexc
    await mexc.update_balance()
    balance = next((item['free'] for item in mexc.current_balance if item['asset'] == 'USDT'), None)
    tokens_to_sell = '\n'.join(_ for _ in mexc.tokens_to_sell)
    # await message.edit_text('')  # todo сделать исчезновение часов
    await message.answer(f'Баланс USDT: {balance}')
    await message.answer(tokens_to_sell)
