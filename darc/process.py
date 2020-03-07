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

import stem
import stem.control
import stem.process
import stem.util.term

import darc.typing as typing
from darc.const import DARC_CPU, FLAG_MP, FLAG_TH, PATH_ID, PATH_QR, PATH_QS, REBOOT, getpid
from darc.crawl import crawler, loader
from darc.db import load_requests, load_selenium
from darc.proxy.tor import renew_tor_session


def _load_last_word():
    """Load data to queue.

    The function will copy the backup of the |requests|_ database
    ``_queue_requests.txt.tmp`` (if exists) and the backup of the
    |selenium|_ database ``_queue_selenium.txt.tmp`` (if exists)
    to the corresponding database.

    The function will also save the process ID to the ``darc.pid``
    PID file.

    See Also:
        * :func:`darc.const.getpid`
        * :func:`darc.db.load_requests`
        * :func:`darc.db.load_selenium`

    """
    with open(PATH_ID, 'w') as file:
        print(os.getpid(), file=file)

    # if os.path.isfile(PATH_QR):
    #     with open(PATH_QR) as file:
    #         for line in file:
    #             QUEUE_REQUESTS.put(line.strip())
    #     os.remove(PATH_QR)

    # if os.path.isfile(PATH_QS):
    #     with open(PATH_QS) as file:
    #         for line in file:
    #             QUEUE_SELENIUM.put(line.strip())
    #     os.remove(PATH_QS)

    if os.path.isfile(f'{PATH_QR}.tmp'):
        with open(f'{PATH_QR}.tmp') as file:
            link_list = file.read()
        with open(f'{PATH_QR}', 'a') as file:
            print(file=file)
            print('# last words', file=file)
            file.write(link_list)
        os.remove(f'{PATH_QR}.tmp')

    if os.path.isfile(f'{PATH_QS}.tmp'):
        with open(f'{PATH_QS}.tmp') as file:
            link_list = file.read()
        with open(f'{PATH_QS}', 'a') as file:
            print(file=file)
            print('# last words', file=file)
            file.write(link_list)
        os.remove(f'{PATH_QS}.tmp')


def _dump_last_word(errors: bool = True):
    """Dump data in queue.

    Args:
        errors: If the function is called upon error raised.

    The function will remove the backup of the |requests|_ database
    ``_queue_requests.txt.tmp`` (if exists) and the backup of the
    |selenium|_ database ``_queue_selenium.txt.tmp`` (if exists).

    If ``errors`` is ``True``, the function will copy the backup of
    the |requests|_ database ``_queue_requests.txt.tmp`` (if exists)
    and the backup of the |selenium|_ database ``_queue_selenium.txt.tmp``
    (if exists) to the corresponding database.

    The function will also remove the PID file ``darc.pid``

    See Also:
        * :func:`darc.const.getpid`
        * :func:`darc.db.save_requests`
        * :func:`darc.db.save_selenium`

    """
    # requests_links = _get_requests_links()
    # if requests_links:
    #     with open(PATH_QR, 'w') as file:
    #         for link in requests_links:
    #             print(link, file=file)

    # selenium_links = _get_selenium_links()
    # if selenium_links:
    #     with open(PATH_QS, 'w') as file:
    #         for link in selenium_links:
    #             print(link, file=file)

    if errors:
        if os.path.isfile(f'{PATH_QR}.tmp'):
            with open(f'{PATH_QR}.tmp') as file:
                link_list = file.read()
            with open(f'{PATH_QR}', 'a') as file:
                print('# last words', file=file)
                file.write(link_list)
            os.remove(f'{PATH_QR}.tmp')

        if os.path.isfile(f'{PATH_QS}.tmp'):
            with open(f'{PATH_QS}.tmp') as file:
                link_list = file.read()
            with open(f'{PATH_QS}', 'a') as file:
                print('# last words', file=file)
                file.write(link_list)
            os.remove(f'{PATH_QS}.tmp')
    else:
        if os.path.isfile(f'{PATH_QR}.tmp'):
            os.remove(f'{PATH_QR}.tmp')

        if os.path.isfile(f'{PATH_QS}.tmp'):
            os.remove(f'{PATH_QS}.tmp')

    if os.path.isfile(PATH_ID):
        os.remove(PATH_ID)


def _get_requests_links() -> typing.List[str]:
    """Fetch links from queue.

    Returns:
        List of links from the |requests|_ database.

    .. deprecated:: 0.1.0
       Use :func:`darc.db.load_requests` instead.

    """
    # link_list = list()
    # while True:
    #     try:
    #         link = QUEUE_REQUESTS.get_nowait()
    #     except queue.Empty:
    #         break
    #     link_list.append(link)

    # if link_list:
    #     random.shuffle(link_list)
    # link_pool = sorted(set(link_list))

    # if not _TOR_BS_FLAG and has_tor(link_pool) and not match_proxy('tor'):
    #     tor_bootstrap()
    # if not _I2P_BS_FLAG and has_i2p(link_pool) and not match_proxy('i2p'):
    #     i2p_bootstrap()
    # if not _ZERONET_BS_FLAG and has_zeronet(link_pool) and not match_proxy('zeronet'):
    #     zeronet_bootstrap()
    # if not _FREENET_BS_FLAG and has_freenet(link_pool) and not match_proxy('freenet'):
    #     freenet_bootstrap()

    # if VERBOSE:
    #     print(stem.util.term.format('-*- [REQUESTS] LINK POOL -*-',
    #                                 stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    #     print(render_error(pprint.pformat(sorted(link_pool)), stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    #     print(stem.util.term.format('-' * shutil.get_terminal_size().columns,
    #                                 stem.util.term.Color.MAGENTA))  # pylint: disable=no-member

    # return link_pool

    return load_requests()


def _get_selenium_links() -> typing.List[str]:
    """Fetch links from queue.

    Returns:
        List of links from the |selenium|_ database.

    .. deprecated:: 0.1.0
       Use :func:`darc.db.load_selenium` instead.

    """
    # link_list = list()
    # while True:
    #     try:
    #         link = QUEUE_SELENIUM.get_nowait()
    #     except queue.Empty:
    #         break
    #     link_list.append(link)

    # if link_list:
    #     random.shuffle(link_list)

    # link_pool = sorted(set(link_list))
    # if VERBOSE:
    #     print(stem.util.term.format('-*- [SELENIUM] LINK POOL -*-',
    #                                 stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    #     print(render_error(pprint.pformat(sorted(link_pool)), stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    #     print(stem.util.term.format('-' * shutil.get_terminal_size().columns,
    #                                 stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    # return link_pool

    return load_selenium()


def _signal_handler(signum: typing.Optional[typing.Union[int, signal.Signals]] = None,  # pylint: disable=unused-argument,no-member
                    frame: typing.Optional[typing.FrameType] = None):  # pylint: disable=unused-argument
    """Signal handler.

    The function will call :func:`~darc.process._dump_last_word`
    to keep a decent death.

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

    print(stem.util.term.format('Keeping last words...',
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member

    # keep records
    _dump_last_word(errors=True)

    try:
        strsignal = signal.strsignal(signum)
    except Exception:
        strsignal = signum
    print(stem.util.term.format(f'Exit with signal: {strsignal} <{frame}>',
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member


def process():
    """Main process.

    The function will register :func:`~darc.process._signal_handler` for ``SIGTERM``,
    and start the main process of the :mod:`darc` darkweb crawlers.

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

    2. :func:`~darc.process.process`: after the obtained URLs have all been
       crawled, :mod:`darc` will obtain URLs from the |selenium|_ link database
       (c.f. :func:`~darc.db.load_selenium`), and feed such URLs to
       :func:`~darc.crawl.loader`.

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

    print('Starting application...')
    try:
        # load remaining links
        _load_last_word()

        # start mainloop
        with multiprocessing.Pool(processes=DARC_CPU) as pool:
            while True:
                # requests crawler
                link_pool = _get_requests_links()
                if link_pool:
                    pool.map(crawler, link_pool)
                else:
                    break

                # selenium loader
                link_pool = _get_selenium_links()
                if link_pool:
                    if FLAG_MP:
                        pool.map(loader, link_pool)
                    elif FLAG_TH and DARC_CPU:
                        thread_list = list()
                        for _ in range(DARC_CPU):
                            try:
                                item = link_pool.pop()
                            except KeyError:
                                break
                            thread = threading.Thread(target=loader, args=(item,))
                            thread_list.append(thread)
                            thread.start()
                        for thread in thread_list:
                            thread.join()
                    else:
                        [loader(item) for item in link_pool]  # pylint: disable=expression-not-assigned
                else:
                    break

                # quit in reboot mode
                if REBOOT:
                    _dump_last_word(errors=False)
                    break

                # renew Tor session
                renew_tor_session()
                print('Starting next round...')
    except BaseException:
        print('Keeping last words...')
        _dump_last_word()
        raise
    print('Gracefully existing...')
