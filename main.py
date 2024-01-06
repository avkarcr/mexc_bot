import asyncio
import os
import sys

from dotenv import load_dotenv
from loguru import logger

from bot.bot import TeleBot
from utils.checkups import get_environments
from modules.mexc.mexc_user import MexcAccount


async def start():
    load_dotenv()
    logger.remove()
    logger.add(sys.stderr, format="{time} {level} {message}", level="WARNING")
    logger.add("logs.txt", rotation="50 MB", retention="1 week", level="DEBUG")
    environ = await get_environments()
    if environ[0]:
        logger.critical(f'Failed to get ENV: {environ[1]}')
        exit()
    logger.debug('ENVs has been successfully loaded')
    environ = environ[1]

    telebot = TeleBot(
        token=environ['token'],
        admin_id=environ['admin_id'],
    )
    telebot.dp.mexc = MexcAccount(
        mexc_host = environ['MEXC_HOST'],
        api_key = environ['mexc_api'],
        secret_key = environ['mexc_secret_key'],
        tokens_on_hold = environ['tokens_on_hold'],
    )
    await telebot.start()

if __name__ == '__main__':
    asyncio.run(start())
