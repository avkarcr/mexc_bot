import os
import re
import json
import datetime as dt
from loguru import logger
import config

from utils.exceptions import DateTimeParseException

async def get_environments() -> dict:
    # Variable name: [ENVIRONMENT/CONFIG NAME, type, True|False - is in .env]
    envs = {
        'token': ['TELEGRAM_TOKEN', str, True],
        'admin_id': ['ADMIN_ID', int, True],
        'mexc_api': ['MEXC_API', str, True],
        'mexc_secret_key': ['MEXC_SECRET_KEY', str, True],
        'user': ['USER', str, True],
        'mexc_host': ['MEXC_HOST', str, False],
        'db_url': ['DB_URL', str, False],
        'drop_db_on_start': ['DROP_DB_ON_START', bool, False],
        'timing': ['TIMING', dict, False],  # todo сделать проверку для словаря
        'tokens_on_hold': ['TOKENS_ON_HOLD', list, False],
    }
    environ = {}
    result = (False, environ)
    for var_name, (env_name, _type, _is_env) in envs.items():
        logger.debug(f'Getting var {var_name} named {env_name} with type {_type}. Env? - {_is_env}')
        if _is_env:
            logger.debug(f'{var_name} is in .env')
            environ[var_name] = os.getenv(env_name)
        else:
            logger.debug(f'{var_name} is in config.py')
            environ[var_name] = getattr(config, env_name)
        logger.debug(f'Variable {var_name} is set. Now checking type...')
        if _type is int:
            try:
                environ[var_name] = int(environ[var_name])
            except (ValueError, TypeError):
                result = (True, f"Environment variable {environ[var_name]} should be an integer!")
        else:
            if not isinstance(environ[var_name], _type):
                result = (True, f"Variable {environ[var_name]} should be a {_type} type.")
        # if _type is list:  # todo нужен тест
        #     try:
        #         environ[var_name] = json.loads(environ[var_name].replace("'", '"'))
        #     except (json.JSONDecodeError, TypeError):
        #         result = (True, f"Env variable {environ[var_name]} should be a list!")
        # if _type is str and not environ[var_name]:
        #     result = (True, f"Environment variable {environ[var_name]} should be a string!")
        # if _type is bool and not environ[var_name]:  # todo сделать проверку на булево значение
        #     is_non_empty = variable is not None and variable != ""
        #     is_boolean = isinstance(variable, bool)
        #     result = (True, f"Environment variable {environ[var_name]} should be a string!")
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
