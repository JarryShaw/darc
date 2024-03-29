# -*- coding: utf-8 -*-
# pylint: disable=ungrouped-imports
"""Main Processing
=====================

The :mod:`darc.process` module contains the main processing
logic of the :mod:`darc` module.

"""

import multiprocessing
import signal
import threading
import time
from typing import TYPE_CHECKING

from darc.const import DARC_CPU, DARC_WAIT, FLAG_MP, FLAG_TH, REBOOT
from darc.crawl import crawler, loader
from darc.db import load_requests, load_selenium
from darc.error import HookExecutionFailed, WorkerBreak
from darc.link import Link
from darc.logging import WARNING as LOG_WARNING
from darc.logging import logger
from darc.proxy.freenet import _FREENET_BS_FLAG, freenet_bootstrap
from darc.proxy.i2p import _I2P_BS_FLAG, i2p_bootstrap
from darc.proxy.tor import _TOR_BS_FLAG, renew_tor_session, tor_bootstrap
from darc.proxy.zeronet import _ZERONET_BS_FLAG, zeronet_bootstrap
from darc.signal import exit_signal
from darc.signal import register as register_signal

if TYPE_CHECKING:
    from multiprocessing import Process
    from threading import Thread
    from typing import Callable, List, Literal, Optional, Union

#: List[Union[Process, Thread]]: List of
#: active child processes and/or threads.
_WORKER_POOL = []  # type: List[Union[Process, Thread]]

#: List[Callable[[Literal['crawler', 'loader'], List[Link]]]: List of hook functions to
#: be called between each *round*.
_HOOK_REGISTRY = []  # type: List[Callable[[Literal["crawler", "loader"], List[Link]], None]]


def register(hook: 'Callable[[Literal["crawler", "loader"], List[Link]], None]', *,
             _index: 'Optional[int]' = None) -> None:
    """Register hook function.

    Args:
        hook: Hook function to be registered.

    Keyword Args:
        _index: Position index for the hook function.

    The hook function takes two parameters:

    1. a :obj:`str` object indicating the type of worker,
       i.e. ``'crawler'`` or ``'loader'``;
    2. a :obj:`list` object containing :class:`~darc.link.Link`
       objects, as the current processed link pool.

    The hook function may raises :exc:`~darc.error.WorkerBreak`
    so that the worker shall break from its indefinite loop upon
    finishing of current *round*. Any value returned from the
    hook function will be ignored by the workers.

    See Also:
        The hook functions will be saved into
        :data:`~darc.process._HOOK_REGISTRY`.

    """
    if _index is None:
        _HOOK_REGISTRY.append(hook)
    else:
        _HOOK_REGISTRY.insert(_index, hook)


def process_crawler() -> None:
    """A worker to run the :func:`~darc.crawl.crawler` process.

    Warns:
        HookExecutionFailed: When hook function raises an error.

    """
    logger.info('[CRAWLER] Starting mainloop...')
    logger.debug('[CRAWLER] Starting first round...')

    # start mainloop
    while True:
        # requests crawler
        link_pool = load_requests()
        if not link_pool:
            if DARC_WAIT is not None:
                time.sleep(DARC_WAIT)
            continue

        for link in link_pool:
            crawler(link)

        time2break = False
        for hook in _HOOK_REGISTRY:
            try:
                hook('crawler', link_pool)
            except WorkerBreak:
                time2break = True
            except Exception:
                logger.pexc(LOG_WARNING, '[CRAWLER] hook execution failed', HookExecutionFailed)

        # marked to break by hook function
        if time2break:
            break

        # quit in reboot mode
        if REBOOT:
            break

        # renew Tor session
        renew_tor_session()
        logger.debug('[CRAWLER] Starting next round...')

    logger.info('[CRAWLER] Stopping mainloop...')


def process_loader() -> None:
    """A worker to run the :func:`~darc.crawl.loader` process.

    Warns:
        HookExecutionFailed: When hook function raises an error.

    """
    logger.info('[CRAWLER] Starting mainloop...')
    logger.debug('[LOADER] Starting first round...')

    # start mainloop
    while True:
        # selenium loader
        link_pool = load_selenium()
        if not link_pool:
            if DARC_WAIT is not None:
                time.sleep(DARC_WAIT)
            continue

        for link in link_pool:
            loader(link)

        time2break = False
        for hook in _HOOK_REGISTRY:
            try:
                hook('loader', link_pool)
            except WorkerBreak:
                time2break = True
            except Exception:
                logger.pexc(LOG_WARNING, '[LOADER] hook execution failed', HookExecutionFailed)

        # marked to break by hook function
        if time2break:
            break

        # quit in reboot mode
        if REBOOT:
            break

        # renew Tor session
        renew_tor_session()
        logger.debug('[LOADER] Starting next round...')

    logger.info('[LOADER] Stopping mainloop...')


def _process(worker: 'Union[process_crawler, process_loader]') -> None:  # type: ignore[valid-type]
    """Wrapper function to start the worker process."""
    global _WORKER_POOL  # pylint: disable=global-statement

    if FLAG_MP:
        _WORKER_POOL = [multiprocessing.Process(target=worker) for _ in range(DARC_CPU)]
        for proc in _WORKER_POOL:
            proc.start()
        for proc in _WORKER_POOL:
            proc.join()

    elif FLAG_TH:
        _WORKER_POOL = [threading.Thread(target=worker) for _ in range(DARC_CPU)]
        for proc in _WORKER_POOL:
            proc.start()
        for proc in _WORKER_POOL:
            proc.join()

    else:
        worker()  # type: ignore[misc]


def process(worker: 'Literal["crawler", "loader"]') -> None:
    """Main process.

    The function will register :func:`~darc.process._signal_handler` for ``SIGTERM``,
    and start the main process of the :mod:`darc` darkweb crawlers.

    Args:
        worker: Worker process type.

    Raises:
        ValueError: If ``worker`` is not a valid value.

    Before starting the workers, the function will start proxies through

    * :func:`darc.proxy.tor.tor_proxy`
    * :func:`darc.proxy.i2p.i2p_proxy`
    * :func:`darc.proxy.zeronet.zeronet_proxy`
    * :func:`darc.proxy.freenet.freenet_proxy`

    The general process can be described as following for *workers* of ``crawler`` type:

    1. :func:`~darc.process.process_crawler`: obtain URLs from the :mod:`requests`
       link database (c.f. :func:`~darc.db.load_requests`), and feed such URLs to
       :func:`~darc.crawl.crawler`.

       .. note::

          If :data:`~darc.const.FLAG_MP` is :data:`True`, the function will be
          called with *multiprocessing* support; if :data:`~darc.const.FLAG_TH`
          if :data:`True`, the function will be called with *multithreading*
          support; if none, the function will be called in single-threading.

    2. :func:`~darc.crawl.crawler`: parse the URL using
       :func:`~darc.link.parse_link`, and check if need to crawl the
       URL (c.f. :data:`~darc.const.PROXY_WHITE_LIST`, :data:`~darc.const.PROXY_BLACK_LIST`
       , :data:`~darc.const.LINK_WHITE_LIST` and :data:`~darc.const.LINK_BLACK_LIST`);
       if true, then crawl the URL with :mod:`requests`.

       If the URL is from a brand new host, :mod:`darc` will first try
       to fetch and save ``robots.txt`` and sitemaps of the host
       (c.f. :func:`~darc.proxy.null.save_robots` and :func:`~darc.proxy.null.save_sitemap`),
       and extract then save the links from sitemaps (c.f. :func:`~darc.proxy.null.read_sitemap`)
       into link database for future crawling (c.f. :func:`~darc.db.save_requests`).
       Also, if the submission API is provided, :func:`~darc.submit.submit_new_host`
       will be called and submit the documents just fetched.

       If ``robots.txt`` presented, and :data:`~darc.const.FORCE` is
       :data:`False`, :mod:`darc` will check if allowed to crawl the URL.

       .. note::

          The root path (e.g. ``/`` in https://www.example.com/) will always
          be crawled ignoring ``robots.txt``.

       At this point, :mod:`darc` will call the customised hook function
       from :mod:`darc.sites` to crawl and get the final response object.
       :mod:`darc` will save the session cookies and header information,
       using :func:`~darc.save.save_headers`.

       .. note::

          If :exc:`requests.exceptions.InvalidSchema` is raised, the link
          will be saved by :func:`~darc.proxy.null.save_invalid`. Further
          processing is dropped.

       If the content type of response document is not ignored (c.f.
       :data:`~darc.const.MIME_WHITE_LIST` and :data:`~darc.const.MIME_BLACK_LIST`),
       :func:`~darc.submit.submit_requests` will be called and submit the document
       just fetched.

       If the response document is HTML (``text/html`` and ``application/xhtml+xml``),
       :func:`~darc.parse.extract_links` will be called then to extract all possible
       links from the HTML document and save such links into the database
       (c.f. :func:`~darc.db.save_requests`).

       And if the response status code is between ``400`` and ``600``,
       the URL will be saved back to the link database
       (c.f. :func:`~darc.db.save_requests`). If **NOT**, the URL will
       be saved into :mod:`selenium` link database to proceed next steps
       (c.f. :func:`~darc.db.save_selenium`).

    The general process can be described as following for *workers* of ``loader`` type:

    1. :func:`~darc.process.process_loader`: in the meanwhile, :mod:`darc` will
       obtain URLs from the :mod:`selenium` link database (c.f. :func:`~darc.db.load_selenium`),
       and feed such URLs to :func:`~darc.crawl.loader`.

       .. note::

          If :data:`~darc.const.FLAG_MP` is :data:`True`, the function will be
          called with *multiprocessing* support; if :data:`~darc.const.FLAG_TH`
          if :data:`True`, the function will be called with *multithreading*
          support; if none, the function will be called in single-threading.

    2. :func:`~darc.crawl.loader`: parse the URL using
       :func:`~darc.link.parse_link` and start loading the URL using
       :mod:`selenium` with Google Chrome.

       At this point, :mod:`darc` will call the customised hook function
       from :mod:`darc.sites` to load and return the original
       :class:`~selenium.webdriver.Chrome` object.

       If successful, the rendered source HTML document will be saved, and a
       full-page screenshot will be taken and saved.

       If the submission API is provided, :func:`~darc.submit.submit_selenium`
       will be called and submit the document just loaded.

       Later, :func:`~darc.parse.extract_links` will be called then to
       extract all possible links from the HTML document and save such
       links into the :mod:`requests` database (c.f. :func:`~darc.db.save_requests`).

    After each *round*, :mod:`darc` will call registered hook functions in
    sequential order, with the type of worker (``'crawler'`` or ``'loader'``)
    and the current link pool as its parameters, see :func:`~darc.process.register`
    for more information.

    If in reboot mode, i.e. :data:`~darc.const.REBOOT` is :data:`True`, the function
    will exit after first round. If not, it will renew the Tor connections (if
    bootstrapped), c.f. :func:`~darc.proxy.tor.renew_tor_session`, and start
    another round.

    """
    register_signal(signal.SIGINT, exit_signal)
    register_signal(signal.SIGTERM, exit_signal)
    #register_signal(signal.SIGKILL, exit_signal)

    logger.info('[DARC] Starting %s...', worker)

    if not _TOR_BS_FLAG:
        tor_bootstrap()
    if not _I2P_BS_FLAG:
        i2p_bootstrap()
    if not _ZERONET_BS_FLAG:
        zeronet_bootstrap()
    if not _FREENET_BS_FLAG:
        freenet_bootstrap()

    if worker == 'crawler':
        _process(process_crawler)
    elif worker == 'loader':
        _process(process_loader)
    else:
        raise ValueError(f'invalid worker type: {worker!r}')

    logger.info('[DARC] Gracefully existing %s...', worker)
