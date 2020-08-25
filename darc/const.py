# -*- coding: utf-8 -*-
"""Defined constants."""

import datetime
import getpass
import json
import math
import multiprocessing
import os
import pprint
import re
import shutil
import sys
import threading

import peewee
import playhouse.db_url
import redis
import stem.util.term

import darc.typing as typing
from darc._compat import nullcontext
from darc.error import render_error

# reboot mode?
REBOOT = bool(int(os.getenv('DARC_REBOOT', '0')))

# debug mode?
DEBUG = bool(int(os.getenv('DARC_DEBUG', '0')))

# verbose mode?
VERBOSE = bool(int(os.getenv('DARC_VERBOSE', '0'))) or DEBUG

# force mode?
FORCE = bool(int(os.getenv('DARC_FORCE', '0')))

# check mode?
CHECK_NG = bool(int(os.getenv('DARC_CHECK_CONTENT_TYPE', '0')))
CHECK = bool(int(os.getenv('DARC_CHECK', '0'))) or CHECK_NG

# root path
ROOT = os.path.dirname(os.path.abspath(__file__))
CWD = os.path.realpath(os.curdir)

# process number
DARC_CPU = os.getenv('DARC_CPU')
if DARC_CPU is not None:
    DARC_CPU = int(DARC_CPU)  # type: ignore

# use multiprocessing?
FLAG_MP = bool(int(os.getenv('DARC_MULTIPROCESSING', '1')))
FLAG_TH = bool(int(os.getenv('DARC_MULTITHREADING', '0')))
if FLAG_MP and FLAG_TH:
    sys.exit('cannot enable multiprocessing and multithreading at the same time')

# non-root user
DARC_USER = os.getenv('DARC_USER', getpass.getuser())
if DARC_USER == 'root':
    sys.exit('please specify a non-root user as DARC_USER')

# data storage
PATH_DB = os.path.abspath(os.getenv('PATH_DATA', 'data'))
PATH_MISC = os.path.join(PATH_DB, 'misc')
os.makedirs(PATH_MISC, exist_ok=True)

# link file mapping
PATH_LN = os.path.join(PATH_DB, 'link.csv')

# PID file
PATH_ID = os.path.join(PATH_DB, 'darc.pid')

# extract link pattern
_LINK_WHITE_LIST = json.loads(os.getenv('LINK_WHITE_LIST', '[]'))
if DEBUG:
    print(stem.util.term.format('-*- LINK WHITE LIST -*-',
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    print(render_error(pprint.pformat(_LINK_WHITE_LIST), stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    print(stem.util.term.format('-' * shutil.get_terminal_size().columns,
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
LINK_WHITE_LIST = [re.compile(link, re.IGNORECASE) for link in _LINK_WHITE_LIST]

# link black list
_LINK_BLACK_LIST = json.loads(os.getenv('LINK_BLACK_LIST', '[]'))
if DEBUG:
    print(stem.util.term.format('-*- LINK BLACK LIST -*-',
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    print(render_error(pprint.pformat(_LINK_BLACK_LIST), stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    print(stem.util.term.format('-' * shutil.get_terminal_size().columns,
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
LINK_BLACK_LIST = [re.compile(link, re.IGNORECASE) for link in _LINK_BLACK_LIST]

# link fallback value
LINK_FALLBACK = bool(int(os.getenv('LINK_FALLBACK', '0')))

# content type white list
_MIME_WHITE_LIST = json.loads(os.getenv('MIME_WHITE_LIST', '[]'))
if DEBUG:
    print(stem.util.term.format('-*- MIME WHITE LIST -*-',
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    print(render_error(pprint.pformat(_MIME_WHITE_LIST), stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    print(stem.util.term.format('-' * shutil.get_terminal_size().columns,
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
MIME_WHITE_LIST = [re.compile(mime, re.IGNORECASE) for mime in _MIME_WHITE_LIST]

# content type black list
_MIME_BLACK_LIST = json.loads(os.getenv('MIME_BLACK_LIST', '[]'))
if DEBUG:
    print(stem.util.term.format('-*- MIME BLACK LIST -*-',
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    print(render_error(pprint.pformat(_MIME_BLACK_LIST), stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    print(stem.util.term.format('-' * shutil.get_terminal_size().columns,
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
MIME_BLACK_LIST = [re.compile(mime, re.IGNORECASE) for mime in _MIME_BLACK_LIST]

# content type fallback value
MIME_FALLBACK = bool(int(os.getenv('MIME_FALLBACK', '0')))

# proxy type black list
_PROXY_BLACK_LIST = json.loads(os.getenv('PROXY_BLACK_LIST', '[]').casefold())
if DEBUG:
    print(stem.util.term.format('-*- PROXY BLACK LIST -*-',
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    print(render_error(pprint.pformat(_PROXY_BLACK_LIST), stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    print(stem.util.term.format('-' * shutil.get_terminal_size().columns,
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
PROXY_BLACK_LIST = [proxy.casefold() for proxy in _PROXY_BLACK_LIST]

# proxy type white list
_PROXY_WHITE_LIST = json.loads(os.getenv('PROXY_WHITE_LIST', '[]').casefold())
if DEBUG:
    print(stem.util.term.format('-*- PROXY WHITE LIST -*-',
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    print(render_error(pprint.pformat(_PROXY_WHITE_LIST), stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    print(stem.util.term.format('-' * shutil.get_terminal_size().columns,
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
PROXY_WHITE_LIST = [proxy.casefold() for proxy in _PROXY_WHITE_LIST]

# proxy type fallback value
PROXY_FALLBACK = bool(int(os.getenv('PROXY_FALLBACK', '0')))

# time delta for caches in seconds
_TIME_CACHE = float(os.getenv('TIME_CACHE', '60'))
if math.isfinite(_TIME_CACHE):
    TIME_CACHE = datetime.timedelta(seconds=_TIME_CACHE)
else:
    TIME_CACHE = None  # type: ignore
del _TIME_CACHE

# selenium wait time
_SE_WAIT = float(os.getenv('SE_WAIT', '60'))
if math.isfinite(_SE_WAIT):
    SE_WAIT = _SE_WAIT
else:
    SE_WAIT = None  # type: ignore
del _SE_WAIT

# selenium empty page
SE_EMPTY = '<html><head></head><body></body></html>'

# selenium wait time
_DARC_WAIT = float(os.getenv('DARC_WAIT', '60'))
if math.isfinite(_DARC_WAIT):
    DARC_WAIT = _DARC_WAIT
else:
    DARC_WAIT = None  # type: ignore
del _DARC_WAIT

# Redis client
_REDIS_URL = os.getenv('REDIS_URL')
if _REDIS_URL is None:
    REDIS = NotImplemented
    FLAG_DB = True
else:
    REDIS = redis.Redis.from_url(_REDIS_URL, decode_components=True)
    FLAG_DB = False

# database instance
_DB_URL = os.getenv('DB_URL')
if _DB_URL is None:
    DB = peewee.SqliteDatabase(f'sqlite://{PATH_DB}/sqlite/darc.db')
    DB_WEB = peewee.SqliteDatabase(f'sqlite://{PATH_DB}/sqlite/darcweb.db')
else:
    DB: typing.Database = playhouse.db_url.connect(f'{_DB_URL}/darc', unquote_password=True)  # type: ignore
    DB_WEB: typing.Database = playhouse.db_url.connect(f'{_DB_URL}/darcweb', unquote_password=True)  # type: ignore
del _DB_URL


def getpid() -> int:
    """Get process ID.

    The process ID will be saved under the :data:`~darc.const.PATH_DB`
    folder, in a file named ``darc.pid``. If no such file exists,
    ``-1`` will be returned.

    Returns:
        The process ID.

    See Also:
        * :data:`darc.const.PATH_ID`

    """
    if os.path.isfile(PATH_ID):
        with open(PATH_ID) as file:
            return int(file.read().strip())
    return -1


def get_lock() -> typing.Union[multiprocessing.Lock, threading.Lock, nullcontext]:  # type: ignore
    """Get a lock.

    Returns:
        Lock context based on :data:`~darc.const.FLAG_MP`
        and :data:`~darc.const.FLAG_TH`.

    """
    if FLAG_MP:
        return multiprocessing.Lock()
    if FLAG_TH:
        return threading.Lock()
    return nullcontext()
