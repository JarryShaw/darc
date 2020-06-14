# -*- coding: utf-8 -*-
"""Link Database
===================

The :mod:`darc` project utilises file system based database
to provide tele-process communication.

.. note::

   In its first implementation, the :mod:`darc` project used
   |Queue|_ to support such communication. However, as noticed
   when runtime, the |Queue| object will be much affected by
   the lack of memory.

   .. |Queue| replace:: ``multiprocessing.Queue``
   .. _Queue: https://docs.python.org/3/library/multiprocessing.html#multiprocessing.Queue

There will be two databases, both locate at root of the
data storage path :data:`~darc.const.PATH_DB`:

* the |requests|_ database -- ``queue_requests.txt``
* the |selenium|_ database -- ``queue_selenium.txt``

At runtime, after reading such database, :mod:`darc`
will keep a backup of the database with ``.tmp`` suffix
to its file extension.

"""

import math
import os
import pickle
import pprint
import shutil
import sys
import time
import warnings

import redis.lock as redis_lock
import stem.util.term

import darc.typing as typing
from darc._compat import nullcontext
from darc.const import CHECK
from darc.const import REDIS as redis
from darc.const import TIME_CACHE, VERBOSE
from darc.error import LockWarning, RedisCommandFailed, render_error
from darc.link import Link
from darc.parse import _check

# use lock?
REDIS_LOCK = bool(int(os.getenv('DARC_REDIS_LOCK', '0')))

# lock blocking timeout
LOCK_TIMEOUT = float(os.getenv('DARC_LOCK_TIMEOUT', '10'))
if not math.isfinite(LOCK_TIMEOUT):
    LOCK_TIMEOUT = None

# bulk size
BULK_SIZE = int(os.getenv('DARC_BULK_SIZE', '100'))

# max pool
MAX_POOL = float(os.getenv('DARC_MAX_POOL', '100'))
if math.isfinite(MAX_POOL):
    MAX_POOL = math.floor(MAX_POOL)


def redis_command(command: str, *args, **kwargs) -> typing.Any:
    """Wrapper function for Redis command.

    Args:
        command: Command name.
        *args: Arbitrary arguments for the Redis command.

    Keyword Args:
        **kwargs: Arbitrary keyword arguments for the Redis command.

    Return:
        Values returned from the Redis command.

    """
    method = getattr(redis, command)
    while True:
        try:
            value = method(*args, **kwargs)
        except Exception as error:
            warning = warnings.formatwarning(error, RedisCommandFailed, __file__, 85, 'value = method(*args, **kwargs)')
            print(render_error(warning, stem.util.term.Color.YELLOW), end='', file=sys.stderr)  # pylint: disable=no-member
            continue
        break
    return value


def get_lock(name: str,
             timeout: typing.Optional[float] = None,
             sleep: float = 0.1,
             blocking_timeout: typing.Optional[float] = None,
             lock_class: typing.Optional[redis_lock.Lock] = None,
             thread_local: bool = True) -> typing.Union[redis_lock.Lock, nullcontext]:
    """Get a lock for Redis operations.

    Args:
        name: Lock name.
        timeout: Maximum life for the lock.
        sleep: Amount of time to sleep per loop iteration when the
            lock is in blocking mode and another client is currently
            holding the lock.
        blocking_timeout: Maximum amount of time in seconds to spend
            trying to acquire the lock.
        lock_class: Lock implementation.
        thread_local: Whether the lock token is placed in thread-local
            storage.

    Returns:
        Return a new :class:`redis.lock.Lock` object using key ``name``
        that mimics the behavior of :class:`threading.Lock`.

    Notes:
        If :data:`~darc.db.REDIS_LOCK` is :data:`False`, returns a
        :class:`contextlib.nullcontext` instead.

    """
    if REDIS_LOCK:
        return redis_command('lock', name, timeout, sleep, blocking_timeout, lock_class, thread_local)
    return nullcontext()


def have_hostname(link: Link) -> bool:
    """Check if current link is a new host.

    Args:
        link: Link to check against.

    Returns:
        If such link is a new host.

    """
    with get_lock('lock_queue_hostname'):
        code = redis_command('sadd', 'queue_hostname', link.host)
    flag = not bool(code)  # 1 - success; 0 - failed
    return flag


def drop_hostname(link: Link):
    """Remove link from the hostname database.

    Args:
        link: Link to be removed.

    """
    with get_lock('lock_queue_hostname'):
        redis_command('zrem', 'queue_hostname', link.host)


def drop_requests(link: Link):
    """Remove link from the |requests|_ database.

    Args:
        link: Link to be removed.

    """
    with get_lock('lock_queue_requests'):
        redis_command('zrem', 'queue_requests', pickle.dumps(link))


def drop_selenium(link: Link):
    """Remove link from the |selenium|_ database.

    Args:
        link: Link to be removed.

    """
    with get_lock('lock_queue_selenium'):
        redis_command('zrem', 'queue_selenium', pickle.dumps(link))


def save_requests(entries: typing.List[Link], single: bool = False,
                  score=None, nx=False, xx=False):
    """Save link to the |requests|_ database.

    Args:
        entries: Links to be added to the |requests|_ database.
            It can be either a :obj:`list` of links, or a single
            link string (if ``single`` set as ``True``).
        single: Indicate if ``entries`` is a :obj:`list` of links
            or a single link string.
        score: Score to for the Redis sorted set.
        nx: Forces ``ZADD`` to only create new elements and not to
            update scores for elements that already exist.
        xx: Forces ``ZADD`` to only update scores of elements that
            already exist. New elements will not be added.

    """
    if not entries:
        return
    if score is None:
        score = time.time()

    if not single:
        for i in range(0, len(entries), BULK_SIZE):
            mapping = {
                pickle.dumps(link): score for link in entries[i:i + BULK_SIZE]
            }
            with get_lock('lock_queue_requests'):
                redis_command('zadd', 'queue_requests', mapping, nx=nx, xx=xx)
        return

    mapping = {
        pickle.dumps(entries): score,
    }
    with get_lock('lock_queue_requests'):
        redis_command('zadd', 'queue_requests', mapping, nx=nx, xx=xx)


def save_selenium(entries: typing.List[Link], single: bool = False,
                  score=None, nx=False, xx=False):
    """Save link to the |selenium|_ database.

    Args:
        entries: Links to be added to the |selenium|_ database.
            It can be either an *iterable* of links, or a single
            link string (if ``single`` set as ``True``).
        single: Indicate if ``entries`` is an *iterable* of links
            or a single link string.
        score: Score to for the Redis sorted set.
        nx: Forces ``ZADD`` to only create new elements and not to
            update scores for elements that already exist.
        xx: Forces ``ZADD`` to only update scores of elements that
            already exist. New elements will not be added.

    """
    if not entries:
        return
    if score is None:
        score = time.time()

    if not single:
        for i in range(0, len(entries), BULK_SIZE):
            mapping = {
                pickle.dumps(link): score for link in entries[i:i + BULK_SIZE]
            }
            with get_lock('lock_queue_selenium'):
                redis_command('zadd', 'queue_selenium', mapping, nx=nx, xx=xx)
        return

    mapping = {
        pickle.dumps(entries): score,
    }
    with get_lock('lock_queue_selenium'):
        redis_command('zadd', 'queue_selenium', mapping, nx=nx, xx=xx)


def load_requests(check: bool = CHECK) -> typing.List[Link]:
    """Load link from the |requests|_ database.

    Args:
        check: If perform checks on loaded links,
            default to :data:`~darc.const.CHECK`.

    Returns:
        List of loaded links from the |requests|_ database.

    Note:
        At runtime, the function will load links with maximum number
        at :data:`~darc.db.MAX_POOL` to limit the memory usage.

    """
    now = time.time()
    if TIME_CACHE is None:
        max_score = now
    else:
        sec_delta = TIME_CACHE.total_seconds()
        max_score = now - sec_delta

    try:
        with get_lock('lock_queue_requests', blocking_timeout=LOCK_TIMEOUT):
            link_pool = [pickle.loads(link) for link in redis_command('zrangebyscore', 'queue_requests',
                                                                      min=0, max=max_score, start=0, num=MAX_POOL)]
            if TIME_CACHE is not None:
                new_score = now + sec_delta
                save_requests(link_pool, score=new_score)  # force update records
    except redis_lock.LockError:
        warning = warnings.formatwarning(f'[REQUESTS] Failed to acquire Redis lock after {LOCK_TIMEOUT} second(s)',
                                         LockWarning, __file__, 250, "get_lock('lock_queue_requests')")
        print(render_error(warning, stem.util.term.Color.YELLOW), end='', file=sys.stderr)  # pylint: disable=no-member
        link_pool = list()

    if check:
        link_pool = _check(link_pool)

    if VERBOSE:
        print(stem.util.term.format('-*- [REQUESTS] LINK POOL -*-',
                                    stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
        print(render_error(pprint.pformat(sorted(link.url for link in link_pool)),
                           stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
        print(stem.util.term.format('-' * shutil.get_terminal_size().columns,
                                    stem.util.term.Color.MAGENTA))  # pylint: disable=no-member

    return link_pool


def load_selenium(check: bool = CHECK) -> typing.List[Link]:
    """Load link from the |selenium|_ database.

    Args:
        check: If perform checks on loaded links,
            default to :data:`~darc.const.CHECK`.

    Returns:
        List of loaded links from the |selenium|_ database.

    Note:
        At runtime, the function will load links with maximum number
        at :data:`~darc.db.MAX_POOL` to limit the memory usage.

    """
    now = time.time()
    if TIME_CACHE is None:
        max_score = now
    else:
        sec_delta = TIME_CACHE.total_seconds()
        max_score = now - sec_delta

    try:
        with get_lock('lock_queue_selenium', blocking_timeout=LOCK_TIMEOUT):
            link_pool = [pickle.loads(link) for link in redis_command('zrangebyscore', 'queue_selenium',
                                                                      min=0, max=max_score, start=0, num=MAX_POOL)]
            if TIME_CACHE is not None:
                new_score = now + sec_delta
                save_selenium(link_pool, score=new_score)  # force update records
    except redis_lock.LockError:
        warning = warnings.formatwarning(f'[SELENIUM] Failed to acquire Redis lock after {LOCK_TIMEOUT} second(s)',
                                         LockWarning, __file__, 299, "get_lock('lock_queue_selenium')")
        print(render_error(warning, stem.util.term.Color.YELLOW), end='', file=sys.stderr)  # pylint: disable=no-member
        link_pool = list()

    if check:
        link_pool = _check(link_pool)

    if VERBOSE:
        print(stem.util.term.format('-*- [SELENIUM] LINK POOL -*-',
                                    stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
        print(render_error(pprint.pformat(sorted(link.url for link in link_pool)),
                           stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
        print(stem.util.term.format('-' * shutil.get_terminal_size().columns,
                                    stem.util.term.Color.MAGENTA))  # pylint: disable=no-member

    return link_pool
