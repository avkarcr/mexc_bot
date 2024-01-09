import datetime as dt
from loguru import logger

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from utils.checkups import (
    check_token,
    check_listing_time,
    convert_listing_time,
)

listing_router = Router()


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
    megabot = listing_router.megabot
    db = megabot.db
    args = message.text.split(maxsplit=1)
    if not check_args(args)[0]:
        await message.answer(check_args(args)[1])
        return
    token = args[1].split(maxsplit=1)[0]
    listing_time = convert_listing_time(args[1].split(maxsplit=1)[1])
    await db.set_listing_time(token, listing_time)
    start_time = listing_time
    if megabot.steps['spot']:
        megabot.scheduler.add_job(megabot.step_1_spot_trade, 'date', run_date=start_time, args=[token])
        logger.debug(f'Scheduled SPOT for {token}')
        start_time += dt.timedelta(seconds=megabot.timing['spot'] + 1)
    if megabot.steps['convert']:
        megabot.scheduler.add_job(megabot.step_2_convert_to_mx, 'date', run_date=start_time, args=[token])
        logger.debug(f'Scheduled CONVERT for {token}')
        start_time += dt.timedelta(seconds=megabot.timing['convert'] + 1)
    if megabot.steps['spot']:
        megabot.scheduler.add_job(megabot.step_3_threshold_meeting, 'date', run_date=listing_time, args=[token])
        logger.debug(f'Scheduled THRESHOLD for {token}')
    logger.debug(f'Trading cycle for {token} has been scheduled at {listing_time}')
    await message.answer(f'Set time for <b>{token}</b>\nListing time: {listing_time}.')
