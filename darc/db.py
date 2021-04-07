# -*- coding: utf-8 -*-
# pylint: disable=ungrouped-imports
"""Link Database
===================

The :mod:`darc` project utilises `Redis`_ based database
to provide tele-process communication.

.. note::

   In its first implementation, the :mod:`darc` project used
   :class:`~multiprocessing.Queue` to support such communication.
   However, as noticed when runtime, the :class:`~multiprocessing.Queue`
   object will be much affected by the lack of memory.

There will be three databases, all following the save naming
convension with ``queue_`` prefix:

* the hostname database -- ``queue_hostname`` (:class:`~darc.model.tasks.hostname.HostnameQueueModel`)
* the :mod:`requests` database -- ``queue_requests`` (:class:`~darc.model.tasks.requests.RequestsQueueModel`)
* the :mod:`selenium` database -- ``queue_selenium`` (:class:`~darc.model.tasks.selenium.SeleniumQueueModel`)

For ``queue_hostname``, ``queue_requests`` and ``queue_selenium``,
they are all `Redis`_ **sorted set** data type.

If :data:`~darc.const.FLAG_DB` is :data:`True`, then the
module uses the RDS storage described by the :mod:`peewee`
models as backend.

.. _Redis: https://redis.io/

"""

import contextlib
import math
import os
import pickle  # nosec: B403
import pprint
import shutil
import sys
import textwrap
import time
import warnings
from datetime import timedelta
from typing import TYPE_CHECKING, TypeVar, cast

import peewee
import pottery.exceptions as pottery_exceptions
import pottery.redlock as pottery_redlock
import redis as redis_lib
import stem.util.term as stem_term

from darc._compat import datetime, nullcontext
from darc.const import CHECK
from darc.const import DB as database
from darc.const import FLAG_DB
from darc.const import REDIS as redis
from darc.const import TIME_CACHE, VERBOSE
from darc.error import DatabaseOperaionFailed, LockWarning, RedisCommandFailed, render_error
from darc.link import Link
from darc.model.tasks import HostnameQueueModel, RequestsQueueModel, SeleniumQueueModel
from darc.parse import _check

_T = TypeVar('_T')

if TYPE_CHECKING:
    from types import MethodType
    from typing import Any, Callable, ContextManager, List, Optional, Tuple, Union

    from peewee import TextField
    from pottery.redlock import Redlock
    from typing_extensions import Literal

# Redis retry interval
RETRY_INTERVAL = float(os.getenv('DARC_RETRY', '10'))
if not math.isfinite(RETRY_INTERVAL):
    RETRY_INTERVAL = None  # type: ignore[assignment]

# lock blocking timeout
_LOCK_TIMEOUT = float(os.getenv('DARC_LOCK_TIMEOUT', '10'))
if math.isfinite(_LOCK_TIMEOUT):
    LOCK_TIMEOUT = int(_LOCK_TIMEOUT * 1_000)
else:
    LOCK_TIMEOUT = pottery_redlock.Redlock.AUTO_RELEASE_TIME  # type: ignore[attr-defined] # pylint: disable=no-member
del _LOCK_TIMEOUT

# use lock?
REDIS_LOCK = bool(int(os.getenv('DARC_REDIS_LOCK', '0')))
if redis is not None and REDIS_LOCK:
    REDIS_LOCK_POOL = {
        'queue_hostname': pottery_redlock.Redlock(key='queue_hostname', masters={redis}, auto_release_time=LOCK_TIMEOUT),  # pylint: disable=line-too-long
        'queue_requests': pottery_redlock.Redlock(key='queue_requests', masters={redis}, auto_release_time=LOCK_TIMEOUT),  # pylint: disable=line-too-long
        'queue_selenium': pottery_redlock.Redlock(key='queue_selenium', masters={redis}, auto_release_time=LOCK_TIMEOUT),  # pylint: disable=line-too-long
    }

# bulk size
BULK_SIZE = int(os.getenv('DARC_BULK_SIZE', '100'))

# max pool
MAX_POOL = float(os.getenv('DARC_MAX_POOL', '100'))
if math.isfinite(MAX_POOL):
    MAX_POOL = math.floor(MAX_POOL)


def _gen_arg_msg(*args: 'Any', **kwargs: 'Any') -> str:
    """Sanitise arguments representation string.

    Args:
        *args: Arbitrary arguments.

    Keyword Args:
        **kwargs: Arbitrary keyword arguments.

    Returns:
        Sanitised arguments representation string.

    """
    _args = ', '.join(map(repr, args))
    _kwargs = ', '.join(f'{k}={v!r}' for k, v in kwargs.items())
    if _kwargs:
        if _args:
            _args += ', '
        _args += _kwargs
    return textwrap.shorten(_args, shutil.get_terminal_size().columns)


def _redis_command(command: str, *args: 'Any', **kwargs: 'Any') -> 'Any':
    """Wrapper function for Redis command.

    Args:
        command: Command name.
        *args: Arbitrary arguments for the Redis command.

    Keyword Args:
        **kwargs: Arbitrary keyword arguments for the Redis command.

    Return:
        Values returned from the Redis command.

    Warns:
        RedisCommandFailed: Warns at each round when the command failed.

    See Also:
        Between each retry, the function sleeps for :data:`~darc.db.RETRY_INTERVAL`
        second(s) if such value is **NOT** :data:`None`.

    """
    _arg_msg = None

    method = getattr(redis, command)
    while True:
        try:
            value = method(*args, **kwargs)
        except (redis_lib.exceptions.ConnectionError, pottery_exceptions.PotteryError) as error:
            if _arg_msg is None:
                _arg_msg = _gen_arg_msg(*args, **kwargs)

            warning = warnings.formatwarning(f'{type(error).__name__}: {error}', RedisCommandFailed, __file__, 153,
                                             f'value = redis.{command}({_arg_msg})')
            print(render_error(warning, stem_term.Color.YELLOW), end='', file=sys.stderr)  # pylint: disable=no-member

            if RETRY_INTERVAL is not None:
                time.sleep(RETRY_INTERVAL)
            continue
        break
    return value


def _db_operation(operation: 'Callable[..., _T]', *args: 'Any', **kwargs: 'Any') -> _T:
    """Retry operation on database.

    Args:
        operation: Callable / method to perform.
        *args: Arbitrary positional arguments.

    Keyword Args:
        **kwargs: Arbitrary keyword arguments.

    Returns:
        Any return value from a successful
        ``operation`` call.

    """
    _arg_msg = None

    while True:
        try:
            value = operation(*args, **kwargs)
        except (peewee.OperationalError, peewee.InterfaceError) as error:
            if _arg_msg is None:
                _arg_msg = _gen_arg_msg(*args, **kwargs)

            model = cast('MethodType', operation).__self__.__class__.__name__
            warning = warnings.formatwarning(f'{type(error).__name__}: {error}', DatabaseOperaionFailed, __file__, 188,
                                             f'{model}.{operation.__name__}({_arg_msg})')
            print(render_error(warning, stem_term.Color.YELLOW), end='', file=sys.stderr)  # pylint: disable=no-member

            if RETRY_INTERVAL is not None:
                time.sleep(RETRY_INTERVAL)
            continue
        break
    return value


def _redis_get_lock(key: 'Literal["queue_hostname", "queue_requests", "queue_selenium"]') -> 'Union[Redlock, ContextManager]':  # pylint: disable=line-too-long
    """Get a lock for Redis operations.

    Args:
        key: Lock target key.

    Returns:
        Return a new :class:`pottery.redlock.Redlock` object using key ``key``
        that mimics the behavior of :class:`threading.Lock`.

    Seel Also:
        If :data:`~darc.db.REDIS_LOCK` is :data:`False`, returns a
        :class:`contextlib.nullcontext` instead.

    """
    if REDIS_LOCK:
        return REDIS_LOCK_POOL.get(key) or nullcontext()
    return nullcontext()


def have_hostname(link: 'Link') -> 'Tuple[bool, bool]':
    """Check if current link is a new host.

    Args:
        link: Link to check against.

    Returns:
        A tuple of two :obj:`bool` values representing
        if such link is a known host and needs force
        refetch respectively.

    See Also:
        * :func:`darc.db._have_hostname_db`
        * :func:`darc.db._have_hostname_redis`

    """
    if FLAG_DB:
        with database.connection_context():
            try:
                return _have_hostname_db(link)
            except Exception as error:
                warning = warnings.formatwarning(str(error), DatabaseOperaionFailed, __file__, 244,
                                                 f'_have_hostname_db({link})')
                print(render_error(warning, stem_term.Color.YELLOW), end='', file=sys.stderr)  # pylint: disable=no-member
                return False, False
    return _have_hostname_redis(link)


def _have_hostname_db(link: 'Link') -> 'Tuple[bool, bool]':
    """Check if current link is a new host.

    The function checks the :class:`~darc.models.tasks.hostname.HostnameQueueModel` table.

    Args:
        link: Link to check against.

    Returns:
        A tuple of two :obj:`bool` values representing
        if such link is a known host and needs force
        refetch respectively.

    """
    timestamp = datetime.now()
    if TIME_CACHE is None:
        threshold = math.inf
    else:
        threshold = (timestamp - TIME_CACHE).timestamp()

    model, created = cast(
        'Tuple[HostnameQueueModel, bool]',
        _db_operation(HostnameQueueModel.get_or_create, hostname=link.host, defaults={
            'timestamp': timestamp,
        })
    )
    if created:
        return False, False
    return True, model.timestamp.timestamp() < threshold


def _have_hostname_redis(link: 'Link') -> 'Tuple[bool, bool]':
    """Check if current link is a new host.

    The function checks the ``queue_hostname`` database.

    Args:
        link: Link to check against.

    Returns:
        A tuple of two :obj:`bool` values representing
        if such link is a known host and needs force
        refetch respectively.

    """
    new_score = time.time()
    if TIME_CACHE is None:
        threshold = math.inf
    else:
        threshold = new_score - TIME_CACHE.total_seconds()

    with _redis_get_lock('queue_hostname'):
        score = _redis_command('zscore', 'queue_hostname', link.host)  # type: Optional[int]
        if score is None:
            have_flag = False
            force_fetch = False

            # update Redis record
            redis_update = True
        else:
            have_flag = True
            force_fetch = score < threshold

            # update Redis record (only if re-fetch)
            redis_update = force_fetch

    if redis_update:
        _redis_command('zadd', 'queue_hostname', {
            link.host: new_score,
        })
    return have_flag, force_fetch


def drop_hostname(link: 'Link') -> None:
    """Remove link from the hostname database.

    Args:
        link: Link to be removed.

    See Also:
        * :func:`darc.db._drop_hostname_db`
        * :func:`darc.db._drop_hostname_redis`

    """
    if FLAG_DB:
        with database.connection_context():
            try:
                return _drop_hostname_db(link)
            except Exception as error:
                warning = warnings.formatwarning(str(error), DatabaseOperaionFailed, __file__, 340,
                                                 f'_drop_hostname_db({link})')
                print(render_error(warning, stem_term.Color.YELLOW), end='', file=sys.stderr)  # pylint: disable=no-member
                return None
    return _drop_hostname_redis(link)


def _drop_hostname_db(link: 'Link') -> None:
    """Remove link from the hostname database.

    The function updates the :class:`~darc.models.tasks.hostname.HostnameQueueModel` table.

    Args:
        link: Link to be removed.

    """
    model = _db_operation(HostnameQueueModel.get_or_none,
                          HostnameQueueModel.hostname == link.host)  # type: HostnameQueueModel
    if model is not None:
        model.delete_instance()


def _drop_hostname_redis(link: 'Link') -> None:
    """Remove link from the hostname database.

    The function updates the ``queue_hostname`` database.

    Args:
        link: Link to be removed.

    """
    with _redis_get_lock('queue_hostname'):
        _redis_command('zrem', 'queue_hostname', link.host)


def drop_requests(link: 'Link') -> None:  # pylint: disable=inconsistent-return-statements
    """Remove link from the :mod:`requests` database.

    Args:
        link: Link to be removed.

    See Also:
        * :func:`darc.db._drop_requests_db`
        * :func:`darc.db._drop_requests_redis`

    """
    if FLAG_DB:
        with database.connection_context():
            try:
                return _drop_requests_db(link)
            except Exception as error:
                warning = warnings.formatwarning(str(error), DatabaseOperaionFailed, __file__, 391,
                                                 f'_drop_requests_db({link})')
                print(render_error(warning, stem_term.Color.YELLOW), end='', file=sys.stderr)  # pylint: disable=no-member
                return None
    return _drop_requests_redis(link)


def _drop_requests_db(link: 'Link') -> None:
    """Remove link from the :mod:`requests` database.

    The function updates the :class:`~darc.model.tasks.requests.RequestsQueueModel` table.

    Args:
        link: Link to be removed.

    """
    model = _db_operation(RequestsQueueModel.get_or_none,
                          RequestsQueueModel.text == link.url)  # type: RequestsQueueModel
    if model is not None:
        model.delete_instance()


def _drop_requests_redis(link: 'Link') -> None:
    """Remove link from the :mod:`requests` database.

    The function updates the ``queue_requests`` database.

    Args:
        link: Link to be removed.

    """
    with _redis_get_lock('queue_requests'):
        _redis_command('zrem', 'queue_requests', link.name)
    _redis_command('delete', link.name)


def drop_selenium(link: 'Link') -> None:  # pylint: disable=inconsistent-return-statements
    """Remove link from the :mod:`selenium` database.

    Args:
        link: Link to be removed.

    See Also:
        * :func:`darc.db._drop_selenium_db`
        * :func:`darc.db._drop_selenium_redis`

    """
    if FLAG_DB:
        with database.connection_context():
            try:
                return _drop_selenium_db(link)
            except Exception as error:
                warning = warnings.formatwarning(str(error), DatabaseOperaionFailed, __file__, 443,
                                                 f'_drop_selenium_db({link})')
                print(render_error(warning, stem_term.Color.YELLOW), end='', file=sys.stderr)  # pylint: disable=no-member
                return None
    return _drop_selenium_redis(link)


def _drop_selenium_db(link: 'Link') -> None:
    """Remove link from the :mod:`selenium` database.

    The function updates the :class:`~darc.model.tasks.selenium.SeleniumQueueModel` table.

    Args:
        link: Link to be removed.

    """
    model = _db_operation(SeleniumQueueModel.get_or_none,
                          SeleniumQueueModel.text == link.url)  # type: SeleniumQueueModel
    if model is not None:
        model.delete_instance()


def _drop_selenium_redis(link: 'Link') -> None:
    """Remove link from the :mod:`selenium` database.

    The function updates the ``queue_selenium`` database.

    Args:
        link: Link to be removed.

    """
    with _redis_get_lock('queue_selenium'):
        _redis_command('zrem', 'queue_selenium', link.name)
    _redis_command('delete', link.name)


def save_requests(entries: 'Union[Link, List[Link]]', single: bool = False,
                  score: 'Optional[float]' = None, nx: bool = False, xx: bool = False) -> None:
    """Save link to the :mod:`requests` database.

    The function updates the ``queue_requests`` database.

    Args:
        entries: Links to be added to the :mod:`requests` database.
            It can be either a :obj:`list` of links, or a single
            link string (if ``single`` set as :data:`True`).
        single: Indicate if ``entries`` is a :obj:`list` of links
            or a single link string.
        score: Score to for the Redis sorted set.
        nx: Only create new elements and not to
            update scores for elements that already exist.
        xx: Only update scores of elements that
            already exist. New elements will not be added.

    Notes:
        The ``entries`` will be dumped through :mod:`pickle` so that
        :mod:`darc` do not need to parse them again.

    When ``entries`` is a list of :class:`~darc.link.Link` instances,
    we tries to perform *bulk* update to easy the memory consumption.
    The *bulk* size is defined by :data:`~darc.db.BULK_SIZE`.

    See Also:
        * :func:`darc.db._save_requests_db`
        * :func:`darc.db._save_requests_redis`

    """
    if FLAG_DB:
        with database.connection_context():
            try:
                return _save_requests_db(entries, single, score, nx, xx)
            except Exception as error:
                warning = warnings.formatwarning(str(error), DatabaseOperaionFailed, __file__, 515,
                                                 '_save_requests_db(...)')
                print(render_error(warning, stem_term.Color.YELLOW), end='', file=sys.stderr)  # pylint: disable=no-member
                return None
    return _save_requests_redis(entries, single, score, nx, xx)


def _save_requests_db(entries: 'Union[Link, List[Link]]', single: bool = False,
                      score: 'Optional[float]' = None, nx: bool = False, xx: bool = False) -> None:
    """Save link to the :mod:`requests` database.

    The function updates the :class:`~darc.model.tasks.requests.RequestsQueueModel` table.

    Args:
        entries: Links to be added to the :mod:`requests` database.
            It can be either a :obj:`list` of links, or a single
            link string (if ``single`` set as :data:`True`).
        single: Indicate if ``entries`` is a :obj:`list` of links
            or a single link string.
        score: Score to for the Redis sorted set.
        nx: Only create new elements and not to
            update scores for elements that already exist.
        xx: Only update scores of elements that
            already exist. New elements will not be added.

    """
    if not entries:
        return None
    if score is None:
        timestamp = datetime.now()
    else:
        timestamp = datetime.fromtimestamp(score)

    if not single:
        if TYPE_CHECKING:
            entries = cast('List[Link]', entries)

        if nx:
            with database.atomic():
                insert_many = [{
                    'text': link.url,
                    'hash': link.name,
                    'link': link,
                    'timestamp': timestamp,
                } for link in entries]
                for batch in peewee.chunked(insert_many, BULK_SIZE):
                    _db_operation(RequestsQueueModel
                                  .insert_many(insert_many)
                                  .on_conflict_ignore()
                                  .execute)
            return None

        if xx:
            entries_text = [link.url for link in entries]
            _db_operation(RequestsQueueModel
                          .update(timestamp=timestamp)
                          .where(cast('TextField', RequestsQueueModel.text).in_(entries_text))
                          .execute)
            return None

        with database.atomic():
            replace_many = [{
                'text': link.url,
                'hash': link.name,
                'link': link,
                'timestamp': timestamp,
            } for link in entries]
            for batch in peewee.chunked(replace_many, BULK_SIZE):
                _db_operation(RequestsQueueModel.replace_many(batch).execute)
        return None

    if TYPE_CHECKING:
        entries = cast('Link', entries)

    if nx:
        _db_operation(RequestsQueueModel.get_or_create,
                      text=entries.url,
                      defaults={
                          'hash': entries.name,
                          'link': entries,
                          'timestamp': timestamp,
                      })
        return None

    if xx:
        with contextlib.suppress(peewee.DoesNotExist):
            model = _db_operation(RequestsQueueModel.get, RequestsQueueModel.text == entries.url)  # type: RequestsQueueModel # pylint: disable=line-too-long
            model.timestamp = timestamp
            _db_operation(model.save)
        return None

    _db_operation(RequestsQueueModel.replace(
        text=entries.url,
        hash=entries.name,
        link=entries,
        timestamp=timestamp,
    ).execute)
    return None


def _save_requests_redis(entries: 'Union[Link, List[Link]]', single: bool = False,
                         score: 'Optional[float]' = None, nx: bool = False, xx: bool = False) -> None:
    """Save link to the :mod:`requests` database.

    The function updates the ``queue_requests`` database.

    Args:
        entries: Links to be added to the :mod:`requests` database.
            It can be either a :obj:`list` of links, or a single
            link string (if ``single`` set as :data:`True`).
        single: Indicate if ``entries`` is a :obj:`list` of links
            or a single link string.
        score: Score to for the Redis sorted set.
        nx: Forces ``ZADD`` to only create new elements and not to
            update scores for elements that already exist.
        xx: Forces ``ZADD`` to only update scores of elements that
            already exist. New elements will not be added.

    """
    if score is None:
        score = time.time()

    if not single:
        if TYPE_CHECKING:
            entries = cast('List[Link]', entries)

        for chunk in peewee.chunked(entries, BULK_SIZE):
            pool = list(filter(lambda link: isinstance(link, Link), chunk))  # type: List[Link]
            for link in pool:
                _redis_command('set', link.name, pickle.dumps(link), nx=True)
            with _redis_get_lock('queue_requests'):
                _redis_command('zadd', 'queue_requests', {
                    link.name: score for link in pool
                }, nx=nx, xx=xx)
        return None

    if TYPE_CHECKING:
        entries = cast('Link', entries)

    _redis_command('set', entries.name, pickle.dumps(entries), nx=True)
    with _redis_get_lock('queue_requests'):
        _redis_command('zadd', 'queue_requests', {
            entries.name: score,
        }, nx=nx, xx=xx)
    return None


def save_selenium(entries: 'Union[Link, List[Link]]', single: bool = False,  # pylint: disable=inconsistent-return-statements
                  score: 'Optional[float]' = None, nx: bool = False, xx: bool = False) -> None:
    """Save link to the :mod:`selenium` database.

    Args:
        entries: Links to be added to the :mod:`selenium` database.
            It can be either a :obj:`list` of links, or a single
            link string (if ``single`` set as :data:`True`).
        single: Indicate if ``entries`` is a :obj:`list` of links
            or a single link string.
        score: Score to for the Redis sorted set.
        nx: Only create new elements and not to
            update scores for elements that already exist.
        xx: Only update scores of elements that
            already exist. New elements will not be added.

    Notes:
        The ``entries`` will be dumped through :mod:`pickle` so that
        :mod:`darc` do not need to parse them again.

    When ``entries`` is a list of :class:`~darc.link.Link` instances,
    we tries to perform *bulk* update to easy the memory consumption.
    The *bulk* size is defined by :data:`~darc.db.BULK_SIZE`.

    See Also:
        * :func:`darc.db._save_selenium_db`
        * :func:`darc.db._save_selenium_redis`

    """
    if FLAG_DB:
        with database.connection_context():
            try:
                return _save_selenium_db(entries, single, score, nx, xx)
            except Exception as error:
                warning = warnings.formatwarning(str(error), DatabaseOperaionFailed, __file__, 696,
                                                 '_save_selenium_db(...)')
                print(render_error(warning, stem_term.Color.YELLOW), end='', file=sys.stderr)  # pylint: disable=no-member
                return None
    return _save_selenium_redis(entries, single, score, nx, xx)


def _save_selenium_db(entries: 'Union[Link, List[Link]]', single: bool = False,
                      score: 'Optional[float]' = None, nx: bool = False, xx: bool = False) -> None:
    """Save link to the :mod:`selenium` database.

    The function updates the :class:`~darc.model.tasks.selenium.SeleniumQueueModel` table.

    Args:
        entries: Links to be added to the :mod:`selenium` database.
            It can be either a :obj:`list` of links, or a single
            link string (if ``single`` set as :data:`True`).
        single: Indicate if ``entries`` is a :obj:`list` of links
            or a single link string.
        score: Score to for the Redis sorted set.
        nx: Only create new elements and not to
            update scores for elements that already exist.
        xx: Only update scores of elements that
            already exist. New elements will not be added.

    """
    if not entries:
        return None
    if score is None:
        timestamp = datetime.now()
    else:
        timestamp = datetime.fromtimestamp(score)

    if not single:
        if TYPE_CHECKING:
            entries = cast('List[Link]', entries)

        if nx:
            with database.atomic():
                insert_many = [{
                    'text': link.url,
                    'hash': link.name,
                    'link': link,
                    'timestamp': timestamp,
                } for link in entries]
                for batch in peewee.chunked(insert_many, BULK_SIZE):
                    _db_operation(SeleniumQueueModel
                                  .insert_many(insert_many)
                                  .on_conflict_ignore()
                                  .execute)
            return None

        if xx:
            entries_text = [link.url for link in entries]
            _db_operation(SeleniumQueueModel
                          .update(timestamp=timestamp)
                          .where(cast('TextField', SeleniumQueueModel.text).in_(entries_text))
                          .execute)
            return None

        with database.atomic():
            replace_many = [{
                'text': link.url,
                'hash': link.name,
                'link': link,
                'timestamp': timestamp,
            } for link in entries]
            for batch in peewee.chunked(replace_many, BULK_SIZE):
                _db_operation(SeleniumQueueModel.replace_many(batch).execute)
        return None

    if TYPE_CHECKING:
        entries = cast('Link', entries)

    if nx:
        _db_operation(SeleniumQueueModel.get_or_create,
                      text=entries.url,
                      defaults={
                          'hash': entries.name,
                          'link': entries,
                          'timestamp': timestamp,
                      })
        return None

    if xx:
        with contextlib.suppress(peewee.DoesNotExist):
            model = _db_operation(SeleniumQueueModel.get, SeleniumQueueModel.text == entries.url)  # type: SeleniumQueueModel # pylint: disable=line-too-long
            model.timestamp = timestamp
            _db_operation(model.save)
        return None

    _db_operation(SeleniumQueueModel.replace(
        text=entries.url,
        hash=entries.name,
        link=entries,
        timestamp=timestamp,
    ).execute)
    return None


def _save_selenium_redis(entries: 'Union[Link, List[Link]]', single: bool = False,
                         score: 'Optional[float]' = None, nx: bool = False, xx: bool = False) -> None:
    """Save link to the :mod:`selenium` database.

    The function updates the ``queue_selenium`` database.

    Args:
        entries: Links to be added to the :mod:`selenium` database.
            It can be either an *iterable* of links, or a single
            link string (if ``single`` set as :data:`True`).
        single: Indicate if ``entries`` is an *iterable* of links
            or a single link string.
        score: Score to for the Redis sorted set.
        nx: Forces ``ZADD`` to only create new elements and not to
            update scores for elements that already exist.
        xx: Forces ``ZADD`` to only update scores of elements that
            already exist. New elements will not be added.

    When ``entries`` is a list of :class:`~darc.link.Link` instances,
    we tries to perform *bulk* update to easy the memory consumption.
    The *bulk* size is defined by :data:`~darc.db.BULK_SIZE`.

    Notes:
        The ``entries`` will be dumped through :mod:`pickle` so that
        :mod:`darc` do not need to parse them again.

    """
    if not entries:
        return None
    if score is None:
        score = time.time()

    if not single:
        if TYPE_CHECKING:
            entries = cast('List[Link]', entries)

        for chunk in peewee.chunked(entries, BULK_SIZE):
            pool = list(filter(lambda link: isinstance(link, Link), chunk))  # type: List[Link]
            for link in pool:
                _redis_command('set', link.name, pickle.dumps(link), nx=True)
            with _redis_get_lock('queue_selenium'):
                _redis_command('zadd', 'queue_selenium', {
                    link.name: score for link in pool
                }, nx=nx, xx=xx)
        return None

    if TYPE_CHECKING:
        entries = cast('Link', entries)

    _redis_command('set', entries.name, pickle.dumps(entries), nx=True)
    with _redis_get_lock('queue_selenium'):
        _redis_command('zadd', 'queue_selenium', {
            entries.name: score,
        }, nx=nx, xx=xx)
    return None


def load_requests(check: bool = CHECK) -> 'List[Link]':
    """Load link from the :mod:`requests` database.

    Args:
        check: If perform checks on loaded links,
            default to :data:`~darc.const.CHECK`.

    Returns:
        List of loaded links from the :mod:`requests` database.

    Note:
        At runtime, the function will load links with maximum number
        at :data:`~darc.db.MAX_POOL` to limit the memory usage.

    See Also:
        * :func:`darc.db._load_requests_db`
        * :func:`darc.db._load_requests_redis`

    """
    if FLAG_DB:
        with database.connection_context():
            try:
                link_pool = _load_requests_db()
            except Exception as error:
                warning = warnings.formatwarning(str(error), DatabaseOperaionFailed, __file__, 877,
                                                 '_load_requests_db()')
                print(render_error(warning, stem_term.Color.YELLOW), end='', file=sys.stderr)  # pylint: disable=no-member
                link_pool = []
    else:
        link_pool = _load_requests_redis()

    if check:
        link_pool = _check(link_pool)

    if VERBOSE:
        print(stem_term.format('-*- [REQUESTS] LINK POOL -*-', stem_term.Color.MAGENTA))  # pylint: disable=no-member
        print(render_error(pprint.pformat(sorted(link.url for link in link_pool)), stem_term.Color.MAGENTA))  # pylint: disable=no-member
        print(stem_term.format('-' * shutil.get_terminal_size().columns, stem_term.Color.MAGENTA))  # pylint: disable=no-member
    return link_pool


def _load_requests_db() -> 'List[Link]':
    """Load link from the :mod:`requests` database.

    The function reads the :class:`~darc.model.tasks.requests.RequestsQueueModel` table.

    Returns:
        List of loaded links from the :mod:`requests` database.

    Note:
        At runtime, the function will load links with maximum number
        at :data:`~darc.db.MAX_POOL` to limit the memory usage.

    """
    now = datetime.now()
    if TIME_CACHE is None:
        sec_delta = timedelta(seconds=0)
        max_score = now
    else:
        sec_delta = TIME_CACHE
        max_score = now - sec_delta

    with database.atomic():
        query = _db_operation(
            RequestsQueueModel
            .select(RequestsQueueModel.link)
            .where(RequestsQueueModel.timestamp <= max_score)
            .order_by(RequestsQueueModel.timestamp)
            .limit(MAX_POOL)
            .execute
        )  # type: List[RequestsQueueModel]
        link_pool = [model.link for model in query]

        # force update records
        if TIME_CACHE is not None:
            new_score = (now + sec_delta).timestamp()
            _save_requests_db(link_pool, score=new_score)
    return link_pool


def _load_requests_redis() -> 'List[Link]':
    """Load link from the :mod:`requests` database.

    The function reads the ``queue_requests`` database.

    Returns:
        List of loaded links from the :mod:`requests` database.

    Note:
        At runtime, the function will load links with maximum number
        at :data:`~darc.db.MAX_POOL` to limit the memory usage.

    """
    now = time.time()
    if TIME_CACHE is None:
        sec_delta = 0  # type: float
        max_score = now
    else:
        sec_delta = TIME_CACHE.total_seconds()
        max_score = now - sec_delta

    try:
        with _redis_get_lock('queue_requests'):
            temp_pool = [_redis_command('get', name) for name in _redis_command('zrangebyscore', 'queue_requests',
                                                                                min=0, max=max_score, start=0, num=MAX_POOL)]  # type: List[bytes] # pylint: disable=line-too-long
            link_pool = [pickle.loads(link) for link in filter(None, temp_pool)]  # nosec: B301
            if TIME_CACHE is not None:
                new_score = now + sec_delta
                _save_requests_redis(link_pool, score=new_score)  # force update records
    except pottery_exceptions.PotteryError:
        warning = warnings.formatwarning(f'[REQUESTS] Failed to acquire Redis lock after {LOCK_TIMEOUT} second(s)',
                                         LockWarning, __file__, 957, "_redis_get_lock('queue_requests')")
        print(render_error(warning, stem_term.Color.YELLOW), end='', file=sys.stderr)  # pylint: disable=no-member
        link_pool = []
    return link_pool


def load_selenium(check: bool = CHECK) -> 'List[Link]':
    """Load link from the :mod:`selenium` database.

    Args:
        check: If perform checks on loaded links,
            default to :data:`~darc.const.CHECK`.

    Returns:
        List of loaded links from the :mod:`selenium` database.

    Note:
        At runtime, the function will load links with maximum number
        at :data:`~darc.db.MAX_POOL` to limit the memory usage.

    See Also:
        * :func:`darc.db._load_selenium_db`
        * :func:`darc.db._load_selenium_redis`

    """
    if FLAG_DB:
        with database.connection_context():
            try:
                link_pool = _load_selenium_db()
            except Exception as error:
                warning = warnings.formatwarning(str(error), DatabaseOperaionFailed, __file__, 994,
                                                 '_load_selenium_db()')
                print(render_error(warning, stem_term.Color.YELLOW), end='', file=sys.stderr)  # pylint: disable=no-member
                link_pool = []
    else:
        link_pool = _load_selenium_redis()

    if check:
        link_pool = _check(link_pool)

    if VERBOSE:
        print(stem_term.format('-*- [SELENIUM] LINK POOL -*-', stem_term.Color.MAGENTA))  # pylint: disable=no-member
        print(render_error(pprint.pformat(sorted(link.url for link in link_pool)), stem_term.Color.MAGENTA))  # pylint: disable=no-member
        print(stem_term.format('-' * shutil.get_terminal_size().columns, stem_term.Color.MAGENTA))  # pylint: disable=no-member
    return link_pool


def _load_selenium_db() -> 'List[Link]':
    """Load link from the :mod:`selenium` database.

    The function reads the :class:`~darc.model.tasks.selenium.SeleniumQueueModel` table.

    Returns:
        List of loaded links from the :mod:`selenium` database.

    Note:
        At runtime, the function will load links with maximum number
        at :data:`~darc.db.MAX_POOL` to limit the memory usage.

    """
    now = datetime.now()
    if TIME_CACHE is None:
        sec_delta = timedelta(seconds=0)
        max_score = now
    else:
        sec_delta = TIME_CACHE
        max_score = now - sec_delta

    with database.atomic():
        query = _db_operation(
            SeleniumQueueModel
            .select(SeleniumQueueModel.link)
            .where(SeleniumQueueModel.timestamp <= max_score)
            .order_by(SeleniumQueueModel.timestamp)
            .limit(MAX_POOL)
            .query
        )  # type: List[SeleniumQueueModel]
        link_pool = [model.link for model in query]

        # force update records
        if TIME_CACHE is not None:
            new_score = (now + sec_delta).timestamp()
            _save_selenium_db(link_pool, score=new_score)
    return link_pool


def _load_selenium_redis() -> 'List[Link]':
    """Load link from the :mod:`selenium` database.

    The function reads the ``queue_selenium`` database.

    Args:
        check: If perform checks on loaded links,
            default to :data:`~darc.const.CHECK`.

    Returns:
        List of loaded links from the :mod:`selenium` database.

    Note:
        At runtime, the function will load links with maximum number
        at :data:`~darc.db.MAX_POOL` to limit the memory usage.

    """
    now = time.time()
    if TIME_CACHE is None:
        sec_delta = 0  # type: float
        max_score = now
    else:
        sec_delta = TIME_CACHE.total_seconds()
        max_score = now - sec_delta

    try:
        with _redis_get_lock('queue_selenium'):
            temp_pool = [_redis_command('get', name) for name in _redis_command('zrangebyscore', 'queue_selenium',
                                                                                min=0, max=max_score, start=0, num=MAX_POOL)]  # type: List[bytes] # pylint: disable=line-too-long
            link_pool = [pickle.loads(link) for link in filter(None, temp_pool)]  # nosec: B301
            if TIME_CACHE is not None:
                new_score = now + sec_delta
                _save_selenium_redis(link_pool, score=new_score)  # force update records
    except pottery_exceptions.PotteryError:
        warning = warnings.formatwarning(f'[SELENIUM] Failed to acquire Redis lock after {LOCK_TIMEOUT} second(s)',
                                         LockWarning, __file__, 1078, "_redis_get_lock('queue_selenium')")
        print(render_error(warning, stem_term.Color.YELLOW), end='', file=sys.stderr)  # pylint: disable=no-member
        link_pool = []
    return link_pool
