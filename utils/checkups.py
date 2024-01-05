from loguru import logger  # todo DEL

import os
import re
import json
import datetime as dt

from config import MEXC_HOST, TOKENS_ON_HOLD

from utils.exceptions import DateTimeParseException

async def get_environments() -> dict:
    envs = {
        'token': ['TELEGRAM_TOKEN', str],
        'admin_id': ['ADMIN_ID', int],
        'mexc_api': ['MEXC_API', str],
        'mexc_secret_key': ['MEXC_SECRET_KEY', str],
    }
    environ = {}
    result = (False, environ)
    for var_name, (env_name, _) in envs.items():
        environ[var_name] = os.getenv(env_name)
        # if _ is list:
        #     try:
        #         environ[var_name] = json.loads(environ[var_name].replace("'", '"'))
        #     except (json.JSONDecodeError, TypeError):
        #         result = (True, f"Env variable {environ[var_name]} should be a list!")
        # if _ is str and not environ[var_name]:
        #     result = (True, f"Environment variable {environ[var_name]} should be a string!")
        if _ is int:
            try:
                environ[var_name] = int(environ[var_name])
            except (ValueError, TypeError):
                result = (True, f"Environment variable {environ[var_name]} should be an integer!")
    try:
        environ['tokens_on_hold'] = json.loads(str(TOKENS_ON_HOLD).replace("'", '"'))
    except (json.JSONDecodeError, TypeError):
        result = (True, f"Variable (config.py) TOKENS_ON_HOLD should be a list!")
    environ['MEXC_HOST'] = MEXC_HOST
    return result

def check_token(token_name):
    pattern = r'^[A-Z]{1,30}$'
    return bool(re.match(pattern, token_name))

def check_listing_time(listing_time):
    pattern = r'^(?:(?:\d{2}\.\d{2}(?:\.\d{4})?)\s)?\d{2}:\d{2}(?::\d{2})?$'
    return bool(re.match(pattern, listing_time))

def check_date_with_year(datestr):
    date_with_year = r'\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}'
    date_without_year = r'\d{2}\.\d{2} \d{2}:\d{2}'
    if re.match(date_with_year, datestr):
        return True
    elif re.match(date_without_year, datestr):
        return False
    raise DateTimeParseException

def convert_listing_time(listing_time: str):
    parse_str = '%d.%m.%Y %H:%M'
    if not check_date_with_year(listing_time):
        parse_str = '%Y %d.%m %H:%M'
        listing_time = f'{dt.datetime.now().year} {listing_time}'
    return dt.datetime.strptime(listing_time, parse_str)
