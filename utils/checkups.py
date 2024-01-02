import os
import json

from config import MEXC_HOST, TOKENS_ON_HOLD


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
        if _ is str and not environ[var_name]:
            result = (True, f"Environment variable {environ[var_name]} should be a string!")
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
