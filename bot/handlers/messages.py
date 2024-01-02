from aiogram import Router
from aiogram.types import Message

msg_router = Router()


@msg_router.message()
async def msg_handler(message: Message) -> None:
    await message.delete()
