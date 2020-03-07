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

import contextlib
import multiprocessing
import os
import pprint
import random
import shutil
import threading

import stem.util.term

import darc.typing as typing
from darc.const import FLAG_MP, FLAG_TH, PATH_QR, PATH_QS, VERBOSE
from darc.error import render_error
from darc.link import quote, unquote
from darc.parse import match_proxy
from darc.proxy.freenet import _FREENET_BS_FLAG, freenet_bootstrap, has_freenet
from darc.proxy.i2p import _I2P_BS_FLAG, has_i2p, i2p_bootstrap
from darc.proxy.tor import _TOR_BS_FLAG, has_tor, tor_bootstrap
from darc.proxy.zeronet import _ZERONET_BS_FLAG, has_zeronet, zeronet_bootstrap

# database I/O lock
QR_LOCK = multiprocessing.Lock()
if FLAG_MP:
    #QS_LOCK = MANAGER.Lock()  # pylint: disable=no-member
    QS_LOCK = multiprocessing.Lock()
elif FLAG_TH:
    QS_LOCK = threading.Lock()
else:
    QS_LOCK = contextlib.nullcontext()


def save_requests(entries: typing.Iterable[str], single: bool = False):
    """Save link to the |requests|_ database.

    Args:
        entries: Links to be added to the |requests|_ database.
            It can be either an *iterable* of links, or a single
            link string (if ``single`` set as ``True``).
        single: Indicate if ``entries`` is an *iterable* of links
            or a single link string.

    """
    with QR_LOCK:
        with open(PATH_QR, 'a') as file:
            if single:
                print(quote(entries), file=file)
            else:
                for link in entries:
                    print(quote(link), file=file)


def save_selenium(entries: typing.Iterable[str], single: bool = False):
    """Save link to the |selenium|_ database.

    Args:
        entries: Links to be added to the |selenium|_ database.
            It can be either an *iterable* of links, or a single
            link string (if ``single`` set as ``True``).
        single: Indicate if ``entries`` is an *iterable* of links
            or a single link string.

    """
    with QS_LOCK:
        with open(PATH_QS, 'a') as file:
            if single:
                print(quote(entries), file=file)
            else:
                for link in entries:
                    print(quote(link), file=file)


def load_requests() -> typing.List[str]:
    """Load link from the |requests|_ database.

    After loading, :mod:`darc` will backup the original database
    ``queue_requests.txt`` as ``queue_requests.txt.tmp`` and
    empty the loaded database.

    Returns:
        List of loaded links from the |requests|_ database.

    Note:
        Lines start with ``#`` will be considered as comments.
        Empty lines and comment lines will be ignored when loading.

    """
    link_pool = list()
    if os.path.isfile(PATH_QR):
        link_list = list()
        with open(PATH_QR) as file:
            for line in filter(None, map(lambda s: s.strip(), file)):
                if line.startswith('#'):
                    continue
                link_list.append(unquote(line.strip()))

        if link_list:
            random.shuffle(link_list)
        link_pool = sorted(set(link_list))

        if not _TOR_BS_FLAG and has_tor(link_pool) and not match_proxy('tor'):
            tor_bootstrap()
        if not _I2P_BS_FLAG and has_i2p(link_pool) and not match_proxy('i2p'):
            i2p_bootstrap()
        if not _ZERONET_BS_FLAG and has_zeronet(link_pool) and not match_proxy('zeronet'):
            zeronet_bootstrap()
        if not _FREENET_BS_FLAG and has_freenet(link_pool) and not match_proxy('freenet'):
            freenet_bootstrap()
        os.rename(PATH_QR, f'{PATH_QR}.tmp')

    if VERBOSE:
        print(stem.util.term.format('-*- [REQUESTS] LINK POOL -*-',
                                    stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
        print(render_error(pprint.pformat(sorted(link_pool)), stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
        print(stem.util.term.format('-' * shutil.get_terminal_size().columns,
                                    stem.util.term.Color.MAGENTA))  # pylint: disable=no-member

    return link_pool


def load_selenium() -> typing.List[str]:
    """Load link from the |selenium|_ database.

    After loading, :mod:`darc` will backup the original database
    ``queue_selenium.txt`` as ``queue_selenium.txt.tmp`` and
    empty the loaded database.

    Returns:
        List of loaded links from the |selenium|_ database.

    Note:
        Lines start with ``#`` will be considered as comments.
        Empty lines and comment lines will be ignored when loading.

    """
    link_pool = list()
    if os.path.isfile(PATH_QS):
        link_list = list()
        with open(PATH_QS) as file:
            for line in filter(None, map(lambda s: s.strip(), file)):
                if line.startswith('#'):
                    continue
                link_list.append(unquote(line.strip()))

        if link_list:
            random.shuffle(link_list)
        link_pool = sorted(set(link_list))
        os.rename(PATH_QS, f'{PATH_QS}.tmp')

    if VERBOSE:
        print(stem.util.term.format('-*- [SELENIUM] LINK POOL -*-',
                                    stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
        print(render_error(pprint.pformat(sorted(link_pool)), stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
        print(stem.util.term.format('-' * shutil.get_terminal_size().columns,
                                    stem.util.term.Color.MAGENTA))  # pylint: disable=no-member

    return link_pool
