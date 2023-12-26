import asyncio
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError, TelegramNetworkError
from aiogram.filters import CommandStart
from aiogram.types import Message
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

logger.remove()
logger.add(sys.stderr, format="{time} {level} {message}", level="WARNING")
logger.add("logs.txt", rotation="100 MB", level="DEBUG")
logger.info("Информационное сообщение")

token = os.getenv('TELEGRAM_TOKEN')
admin_id = os.getenv('ADMIN_ID')
mexc_api = os.getenv('MEXC_API')
mexc_secret_key = os.getenv('MEXC_SECRET_KEY')

bot = Bot(token=token, parse_mode=ParseMode.HTML)
dp = Dispatcher()

@dp.message(CommandStart())
async def start_handler(message: Message, bot: bot) -> None:
    user = message.from_user
    await message.answer(f'Добро пожаловать, {user.first_name}')
    # await bot.send_message(admin_id, text=f'Bot is running by {user.full_name}')

async def start():
    try:
        await dp.start_polling(bot, skip_updates=True)
    except TelegramNetworkError:
        print('Нет соединения с Интернет')
        exit()
    except TelegramAPIError:
        print('Ошибка подключения к API сервера Telegramm')
        exit()
    finally:
        await bot.send_message(admin_id, text='Бот прекращает работу...')
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(start())