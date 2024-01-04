from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

listing_router = Router()


@listing_router.message(Command("listing"))
async def command_listing_handler(message: Message) -> None:
    """
    This handler receives messages with `/listing` command
    """
    # await message.answer('⏳')
    mexc = listing_router.parent_router.mexc
    await mexc.update_balance()
    balance = next((item['free'] for item in mexc.current_balance if item['asset'] == 'USDT'), None)
    tokens_to_sell = '\n'.join(_ for _ in mexc.tokens_to_sell)
    # await message.edit_text('wwwwwwwwww')  # todo сделать исчезновение часов
    await message.answer(f'Баланс USDT: {balance}')
    await message.answer(tokens_to_sell)
