# -*- coding: utf-8 -*-
"""Main Processing
=====================

The :mod:`darc.process` module contains the main processing
logic of the :mod:`darc` module.

"""

import multiprocessing
import os
import signal
import threading
import time

import stem
import stem.control
import stem.process
import stem.util.term

import darc.typing as typing
from darc._compat import nullcontext, strsignal
from darc.const import DARC_CPU, DARC_WAIT, FLAG_MP, FLAG_TH, PATH_ID, REBOOT, getpid
from darc.crawl import crawler, loader
from darc.db import load_requests, load_selenium
from darc.proxy.tor import renew_tor_session


def _signal_handler(signum: typing.Optional[typing.Union[int, signal.Signals]] = None,  # pylint: disable=unused-argument,no-member
                    frame: typing.Optional[typing.FrameType] = None):  # pylint: disable=unused-argument
    """Signal handler.

    If the current process is not the main process, the function
    shall do nothing.

    Args:
        signum: The signal to handle.
        frame (types.FrameType): The traceback frame from the signal.

    See Also:
        * :func:`darc.const.getpid`

    """
    if os.getpid() != getpid():
        return

    if os.path.isfile(PATH_ID):
        os.remove(PATH_ID)

    try:
        sig = strsignal(signum) or signum
    except Exception:
        sig = signum
    print(stem.util.term.format(f'[DARC] Exit with signal: {sig} <{frame}>',
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member


def process_crawler():
    """A worker to run the :func:`~darc.crawl.crawler` process."""
    print('[CRAWLER] Starting first round...')

    # start mainloop
    with multiprocessing.Pool(processes=DARC_CPU) as pool:
        while True:
            # requests crawler
            link_pool = load_requests()
            if not link_pool:
                if DARC_WAIT is not None:
                    time.sleep(DARC_WAIT)
                continue
            pool.map(crawler, link_pool)

            # quit in reboot mode
            if REBOOT:
                break

            # renew Tor session
            renew_tor_session()
            print('[CRAWLER] Starting next round...')


def process_loader():
    """A worker to run the :func:`~darc.crawl.loader` process."""
    if FLAG_MP:
        pool = multiprocessing.Pool(processes=DARC_CPU)
    else:
        pool = nullcontext()

    print('[LOADER] Starting first round...')
    with pool:
        while True:
            # selenium loader
            link_pool = load_selenium()
            if not link_pool:
                if DARC_WAIT is not None:
                    time.sleep(DARC_WAIT)
                continue

            if FLAG_MP:
                pool.map(loader, link_pool)
            elif FLAG_TH and DARC_CPU:
                while link_pool:
                    thread_list = list()
                    for _ in range(DARC_CPU):
                        try:
                            item = link_pool.pop()
                        except IndexError:
                            break
                        thread = threading.Thread(target=loader, args=(item,))
                        thread_list.append(thread)
                        thread.start()
                    for thread in thread_list:
                        thread.join()
            else:
                [loader(item) for item in link_pool]  # pylint: disable=expression-not-assigned

            # quit in reboot mode
            if REBOOT:
                break

            # renew Tor session
            renew_tor_session()
            print('[LOADER] Starting next round...')


def process(worker: typing.Literal['crawler', 'loader']):
    """Main process.

    The function will register :func:`~darc.process._signal_handler` for ``SIGTERM``,
    and start the main process of the :mod:`darc` darkweb crawlers.

    Args:
        worker: Worker process type.

    Raises:
        ValueError: If ``worker`` is not a valid value.

    The general process can be described as following:

    0. :func:`~darc.process.process`: obtain URLs from the |requests|_
       link database (c.f. :func:`~darc.db.load_requests`), and feed
       such URLs to :func:`~darc.crawl.crawler` with *multiprocessing*
       support.

    1. :func:`~darc.crawl.crawler`: parse the URL using
       :func:`~darc.link.parse_link`, and check if need to crawl the
       URL (c.f. :data:`~darc.const.PROXY_WHITE_LIST`, :data:`~darc.const.PROXY_BLACK_LIST`
       , :data:`~darc.const.LINK_WHITE_LIST` and :data:`~darc.const.LINK_BLACK_LIST`);
       if true, then crawl the URL with |requests|_.

       If the URL is from a brand new host, :mod:`darc` will first try
       to fetch and save ``robots.txt`` and sitemaps of the host
       (c.f. :func:`~darc.save.save_robots` and :func:`~darc.save.save_sitemap`),
       and extract then save the links from sitemaps (c.f. :func:`~darc.parse.read_sitemap`)
       into link database for future crawling (c.f. :func:`~darc.db.save_requests`).
       Also, if the submission API is provided, :func:`~darc.submit.submit_new_host`
       will be called and submit the documents just fetched.

       If ``robots.txt`` presented, and :data:`~darc.const.FORCE` is
       ``False``, :mod:`darc` will check if allowed to crawl the URL.

       .. note::

          The root path (e.g. ``/`` in https://www.example.com/) will always
          be crawled ignoring ``robots.txt``.

       At this point, :mod:`darc` will call the customised hook function
       from :mod:`darc.sites` to crawl and get the final response object.
       :mod:`darc` will save the session cookies and header information,
       using :func:`~darc.save.save_headers`.

       .. note::

          If :exc:`requests.exceptions.InvalidSchema` is raised, the link
          will be saved by :func:`~darc.save.save_invalid`. Further
          processing is dropped.

       If the content type of response document is not ignored (c.f.
       :data:`~darc.const.MIME_WHITE_LIST` and :data:`~darc.const.MIME_BLACK_LIST`),
       :mod:`darc` will save the document using :func:`~darc.save.save_html` or
       :func:`~darc.save.save_file` accordingly. And if the submission API
       is provided, :func:`~darc.submit.submit_requests` will be called and
       submit the document just fetched.

       If the response document is HTML (``text/html`` and ``application/xhtml+xml``),
       :func:`~darc.parse.extract_links` will be called then to extract all possible
       links from the HTML document and save such links into the database
       (c.f. :func:`~darc.db.save_requests`).

       And if the response status code is between ``400`` and ``600``,
       the URL will be saved back to the link database
       (c.f. :func:`~darc.db.save_requests`). If **NOT**, the URL will
       be saved into |selenium|_ link database to proceed next steps
       (c.f. :func:`~darc.db.save_selenium`).

    2. :func:`~darc.process.process`: in the meanwhile, :mod:`darc` will
       obtain URLs from the |selenium|_ link database (c.f. :func:`~darc.db.load_selenium`),
       and feed such URLs to :func:`~darc.crawl.loader`.

       .. note::

          If :data:`~darc.const.FLAG_MP` is ``True``, the function will be
          called with *multiprocessing* support; if :data:`~darc.const.FLAG_TH`
          if ``True``, the function will be called with *multithreading*
          support; if none, the function will be called in single-threading.

    3. :func:`~darc.crawl.loader`: parse the URL using
       :func:`~darc.link.parse_link` and start loading the URL using
       |selenium|_ with Google Chrome.

       At this point, :mod:`darc` will call the customised hook function
       from :mod:`darc.sites` to load and return the original
       |Chrome|_ object.

       If successful, the rendered source HTML document will be saved
       using :func:`~darc.save.save_html`, and a full-page screenshot
       will be taken and saved.

       If the submission API is provided, :func:`~darc.submit.submit_selenium`
       will be called and submit the document just loaded.

       Later, :func:`~darc.parse.extract_links` will be called then to
       extract all possible links from the HTML document and save such
       links into the |requests|_ database (c.f. :func:`~darc.db.save_requests`).

    If in reboot mode, i.e. :data:`~darc.const.REBOOT` is ``True``, the function
    will exit after first round. If not, it will renew the Tor connections (if
    bootstrapped), c.f. :func:`~darc.proxy.tor.renew_tor_session`, and start
    another round.

    """
    #signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)
    #signal.signal(signal.SIGKILL, _signal_handler)

    print(f'[DARC] Starting {worker}...')

    if worker == 'crawler':
        process_crawler()
    elif worker == 'loader':
        process_loader()
    else:
        raise ValueError(f'invalid worker type: {worker!r}')

    print(f'[DARC] Gracefully existing {worker}...')
