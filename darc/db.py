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

import pickle
import pprint
import shutil
import time

import stem.util.term

import darc.typing as typing
from darc.const import CHECK
from darc.const import REDIS as redis
from darc.const import TIME_CACHE, VERBOSE
from darc.error import render_error
from darc.link import Link
from darc.parse import _check, match_proxy
from darc.proxy.freenet import _FREENET_BS_FLAG, freenet_bootstrap, has_freenet
from darc.proxy.i2p import _I2P_BS_FLAG, has_i2p, i2p_bootstrap
from darc.proxy.tor import _TOR_BS_FLAG, has_tor, tor_bootstrap
from darc.proxy.zeronet import _ZERONET_BS_FLAG, has_zeronet, zeronet_bootstrap


def save_requests(entries: typing.Iterable[Link], single: bool = False,
                  score=None, nx=False, xx=False):
    """Save link to the |requests|_ database.

    Args:
        entries: Links to be added to the |requests|_ database.
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
    if score is None:
        score = time.time()

    if single:
        mapping = {
            pickle.dumps(entries): score,
        }
    else:
        mapping = {
            pickle.dumps(link): score for link in entries
        }

    if not mapping:
        return
    redis.zadd('queue_requests', mapping, nx=nx, xx=xx)


def save_selenium(entries: typing.Iterable[Link], single: bool = False,
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
    if score is None:
        score = time.time()

    if single:
        mapping = {
            pickle.dumps(entries): score,
        }
    else:
        mapping = {
            pickle.dumps(link): score for link in entries
        }

    if not mapping:
        return
    redis.zadd('queue_selenium', mapping, nx=nx, xx=xx)


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
    if TIME_CACHE is None:
        max_score = time.time()
    else:
        max_score = time.time() - TIME_CACHE.total_seconds()

    link_pool = [
        pickle.loads(link) for link in redis.zrangebyscore('queue_requests', min=0, max=max_score)
    ]
    if check:
        link_pool = _check(link_pool)

    if not match_proxy('tor') and not _TOR_BS_FLAG and has_tor(link_pool):
        tor_bootstrap()
    if not match_proxy('i2p') and not _I2P_BS_FLAG and has_i2p(link_pool):
        i2p_bootstrap()
    if not match_proxy('zeronet') and not _ZERONET_BS_FLAG and has_zeronet(link_pool):
        zeronet_bootstrap()
    if not match_proxy('freenet') and not _FREENET_BS_FLAG and has_freenet(link_pool):
        freenet_bootstrap()

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
    if TIME_CACHE is None:
        max_score = time.time()
    else:
        max_score = time.time() - TIME_CACHE.total_seconds()

    link_pool = [
        pickle.loads(link) for link in redis.zrangebyscore('queue_selenium', min=0, max=max_score)
    ]
    if check:
        link_pool = _check(link_pool)

    if not match_proxy('tor') and not _TOR_BS_FLAG and has_tor(link_pool):
        tor_bootstrap()
    if not match_proxy('i2p') and not _I2P_BS_FLAG and has_i2p(link_pool):
        i2p_bootstrap()
    if not match_proxy('zeronet') and not _ZERONET_BS_FLAG and has_zeronet(link_pool):
        zeronet_bootstrap()
    if not match_proxy('freenet') and not _FREENET_BS_FLAG and has_freenet(link_pool):
        freenet_bootstrap()

    if VERBOSE:
        print(stem.util.term.format('-*- [SELENIUM] LINK POOL -*-',
                                    stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
        print(render_error(pprint.pformat(sorted(link.url for link in link_pool)),
                           stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
        print(stem.util.term.format('-' * shutil.get_terminal_size().columns,
                                    stem.util.term.Color.MAGENTA))  # pylint: disable=no-member

    return link_pool
