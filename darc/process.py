# -*- coding: utf-8 -*-
"""Main processing."""

import datetime
import multiprocessing
import os
import queue
import random
import threading

import stem
import stem.control
import stem.process
import stem.util.term

import darc.typing as typing
from darc.const import (DARC_CPU, FLAG_MP, FLAG_TH, PATH_ID, PATH_QR, PATH_QS, QUEUE_REQUESTS,
                        QUEUE_SELENIUM, REBOOT)
from darc.crawl import crawler, loader
from darc.proxy.tor import _TOR_BS_FLAG, has_tor, renew_tor_session, tor_bootstrap


def _load_last_word():
    """Load data to queue."""
    with open(PATH_ID, 'w') as file:
        print(os.getpid(), file=file)

    if os.path.isfile(PATH_QR):
        with open(PATH_QR) as file:
            for line in file:
                QUEUE_REQUESTS.put(line.strip())
        os.remove(PATH_QR)

    if os.path.isfile(PATH_QS):
        with open(PATH_QS) as file:
            for line in file:
                timestamp, link = line.strip().split(maxsplit=1)
                QUEUE_SELENIUM.put((datetime.datetime.fromisoformat(timestamp), link))
        os.remove(PATH_QS)


def _dump_last_word():
    """Dump data in queue."""
    with open(PATH_QR, 'w') as file:
        for link in _get_requests_links():
            print(link, file=file)

    with open(PATH_QS, 'w') as file:
        for (timestamp, link) in _get_selenium_links():
            print(f'{timestamp.isoformat()} {link}', file=file)

    if os.path.isfile(PATH_ID):
        os.remove(PATH_ID)


def _get_selenium_links() -> typing.Optional[typing.Set[typing.Tuple[typing.Datetime, str]]]:
    """Fetch links from queue."""
    entry_list = list()
    while True:
        try:
            entry = QUEUE_SELENIUM.get_nowait()
        except queue.Empty:
            break
        entry_list.append(entry)

    if entry_list:
        random.shuffle(entry_list)
    return set(entry_list)


def _get_requests_links() -> typing.Optional[typing.Set[str]]:
    """Fetch links from queue."""
    link_list = list()
    while True:
        try:
            link = QUEUE_REQUESTS.get_nowait()
        except queue.Empty:
            break
        link_list.append(link)

    if link_list:
        random.shuffle(link_list)

    link_pool = set(link_list)
    if not _TOR_BS_FLAG and has_tor(link_pool):
        tor_bootstrap()
    return link_pool


def process():
    """Main process."""
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
                item_pool = _get_selenium_links()
                if item_pool:
                    if FLAG_MP:
                        pool.map(loader, item_pool)
                    elif FLAG_TH and DARC_CPU:
                        thread_list = list()
                        for _ in range(DARC_CPU):
                            try:
                                item = item_pool.pop()
                            except KeyError:
                                break
                            thread = threading.Thread(target=loader, args=(item,))
                            thread_list.append(thread)
                            thread.start()
                        for thread in thread_list:
                            thread.join()
                    else:
                        [loader(item) for item in item_pool]  # pylint: disable=expression-not-assigned
                else:
                    break

                # quit in reboot mode
                if REBOOT:
                    _dump_last_word()
                    break

                # renew Tor session
                renew_tor_session()
                print(stem.util.term.format('Starting next round...', stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    except BaseException:
        print(stem.util.term.format('Keeping last words...', stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
        _dump_last_word()
        raise
    print(stem.util.term.format('Gracefully existing...', stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
