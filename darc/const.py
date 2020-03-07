# -*- coding: utf-8 -*-
"""Defined constants."""

import datetime
import getpass
import json
import math
import os
import pprint
import shutil
import sys

import stem.util.term

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
    DARC_CPU = int(DARC_CPU)

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
PATH_QR = os.path.join(PATH_DB, '_queue_requests.txt')
PATH_QS = os.path.join(PATH_DB, '_queue_selenium.txt')

# PID file
PATH_ID = os.path.join(PATH_DB, 'darc.pid')

# extract link pattern
LINK_WHITE_LIST = json.loads(os.getenv('LINK_WHITE_LIST', '[]'))
if DEBUG:
    print(stem.util.term.format('-*- LINK WHITE LIST -*-',
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    print(render_error(pprint.pformat(LINK_WHITE_LIST), stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    print(stem.util.term.format('-' * shutil.get_terminal_size().columns,
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member

# link black list
LINK_BLACK_LIST = json.loads(os.getenv('LINK_BLACK_LIST', '[]'))
if DEBUG:
    print(stem.util.term.format('-*- LINK BLACK LIST -*-',
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    print(render_error(pprint.pformat(LINK_BLACK_LIST), stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    print(stem.util.term.format('-' * shutil.get_terminal_size().columns,
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member

# content type white list
MIME_WHITE_LIST = json.loads(os.getenv('MIME_WHITE_LIST', '[]'))
if DEBUG:
    print(stem.util.term.format('-*- MIME WHITE LIST -*-',
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    print(render_error(pprint.pformat(MIME_WHITE_LIST), stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    print(stem.util.term.format('-' * shutil.get_terminal_size().columns,
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member

# content type black list
MIME_BLACK_LIST = json.loads(os.getenv('MIME_BLACK_LIST', '[]'))
if DEBUG:
    print(stem.util.term.format('-*- MIME BLACK LIST -*-',
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    print(render_error(pprint.pformat(MIME_BLACK_LIST), stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    print(stem.util.term.format('-' * shutil.get_terminal_size().columns,
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member

# proxy type black list
PROXY_BLACK_LIST = json.loads(os.getenv('PROXY_BLACK_LIST', '[]').casefold())
if DEBUG:
    print(stem.util.term.format('-*- PROXY BLACK LIST -*-',
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    print(render_error(pprint.pformat(PROXY_BLACK_LIST), stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    print(stem.util.term.format('-' * shutil.get_terminal_size().columns,
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member

# proxy type white list
PROXY_WHITE_LIST = json.loads(os.getenv('PROXY_WHITE_LIST', '[]').casefold())
if DEBUG:
    print(stem.util.term.format('-*- PROXY WHITE LIST -*-',
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    print(render_error(pprint.pformat(PROXY_WHITE_LIST), stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    print(stem.util.term.format('-' * shutil.get_terminal_size().columns,
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member

# time delta for caches in seconds
_TIME_CACHE = float(os.getenv('TIME_CACHE', '60'))
if math.isfinite(_TIME_CACHE):
    TIME_CACHE = datetime.timedelta(seconds=_TIME_CACHE)
else:
    TIME_CACHE = None
del _TIME_CACHE

# selenium wait time
_SE_WAIT = float(os.getenv('SE_WAIT', '60'))
if math.isfinite(_SE_WAIT):
    SE_WAIT = _SE_WAIT
else:
    SE_WAIT = None
del _SE_WAIT

# selenium empty page
SE_EMPTY = '<html><head></head><body></body></html>'

# link queue
#MANAGER = multiprocessing.Manager()
#QUEUE_REQUESTS = MANAGER.Queue()  # url
#QUEUE_SELENIUM = MANAGER.Queue()  # url


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
