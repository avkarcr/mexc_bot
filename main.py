import asyncio
import sys

from dotenv import load_dotenv
from loguru import logger

from bot.bot import MegaBot
from utils.checkups import get_environments


async def start():
    load_dotenv()
    logger.remove()
    logger.add(sys.stderr, format="{time} {level} {message}", level="DEBUG")
    logger.add("DB/logs.txt", rotation="50 MB", retention="1 week", level="DEBUG")
    environ = await get_environments()
    if environ[0]:
        logger.critical(f'Failed to get ENV: {environ[1]}')
        exit()
    logger.debug('ENVs has been successfully loaded')
    environ = environ[1]
    megabot = MegaBot(
        token=environ['token'],
        admin_id=environ['admin_id'],
        timing=environ['timing'],
        steps=environ['steps'],
        db_set={
            'db_url': environ['db_url'],
            'drop_db_on_start': environ['drop_db_on_start'],
            'user_id': environ['admin_id'],
            'tokens_on_hold': environ['tokens_on_hold'],
        },
        mexc_set={
            'mexc_host': environ['mexc_host'],
            'api_key': environ['mexc_api'],
            'secret_key': environ['mexc_secret_key'],
            'tokens_on_hold': environ['tokens_on_hold'],
        },
    )
    await megabot.start()

if __name__ == '__main__':
    asyncio.run(start())
