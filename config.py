# Environment loading borrowed from
# https://github.com/marchibbins/teela/blob/9d65abaff804f9a79483529ed194581feafdd745/teela/config.py

import os

from dotenv import load_dotenv
from pathlib import Path

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)


def env_var(key, default=None):
    """ Parse environment variable """

    val = os.getenv(key, default)

    if val == 'True':
        val = True
    elif val == 'False':
        val = False

    return val


class Config(object):
    """
    Configure the application with environment variables
    """

    DEBUG = env_var('DEBUG', default=False)
    APPEND_FROM = env_var('APPEND_FROM', default=False)

    REDIRECT_RULES = [
        ('mofo-redirector.herokuapp.com', 'https://foundation.mozilla.org/', 307)
    ]
