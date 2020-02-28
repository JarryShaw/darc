# -*- coding: utf-8 -*-
"""Main processing."""

import multiprocessing
import os
import pprint
import queue
import random
import shutil
import signal
import threading

import stem
import stem.control
import stem.process
import stem.util.term

import darc.typing as typing
from darc.const import (DARC_CPU, DEBUG, FLAG_MP, FLAG_TH, PATH_ID, PATH_QR, PATH_QS,
                        QUEUE_REQUESTS, QUEUE_SELENIUM, REBOOT, getpid)
from darc.crawl import crawler, loader
from darc.proxy.freenet import _FREENET_BS_FLAG, freenet_bootstrap, has_freenet
from darc.proxy.i2p import _I2P_BS_FLAG, has_i2p, i2p_bootstrap
from darc.proxy.tor import _TOR_BS_FLAG, has_tor, renew_tor_session, tor_bootstrap
from darc.proxy.zeronet import _ZERONET_BS_FLAG, has_zeronet, zeronet_bootstrap


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
                QUEUE_SELENIUM.put(line.strip())
        os.remove(PATH_QS)


def _dump_last_word():
    """Dump data in queue."""
    requests_links = _get_requests_links()
    if requests_links:
        with open(PATH_QR, 'w') as file:
            for link in requests_links:
                print(link, file=file)

    selenium_links = _get_selenium_links()
    if selenium_links:
        with open(PATH_QS, 'w') as file:
            for link in selenium_links:
                print(link, file=file)

    if os.path.isfile(PATH_ID):
        os.remove(PATH_ID)


def _get_requests_links() -> typing.Set[str]:
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
    if DEBUG:
        print(stem.util.term.format('LINK POOL',
                                    stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
        pprint.pprint(sorted(link_pool))
        print(stem.util.term.format('-' * shutil.get_terminal_size().columns,
                                    stem.util.term.Color.MAGENTA))  # pylint: disable=no-member

    if not _TOR_BS_FLAG and has_tor(link_pool):
        tor_bootstrap()
    if not _I2P_BS_FLAG and has_i2p(link_pool):
        i2p_bootstrap()
    if not _ZERONET_BS_FLAG and has_zeronet(link_pool):
        zeronet_bootstrap()
    if not _FREENET_BS_FLAG and has_freenet(link_pool):
        freenet_bootstrap()
    return link_pool


def _get_selenium_links() -> typing.Set[typing.Tuple[typing.Datetime, str]]:
    """Fetch links from queue."""
    link_list = list()
    while True:
        try:
            link = QUEUE_SELENIUM.get_nowait()
        except queue.Empty:
            break
        link_list.append(link)

    if link_list:
        random.shuffle(link_list)
    return set(link_list)


def _signal_handler(signum: typing.Optional[typing.Union[int, signal.Signals]] = None,  # pylint: disable=unused-argument,no-member
                    frame: typing.Optional[typing.FrameType] = None):  # pylint: disable=unused-argument
    """Signal handler."""
    if os.getpid() != getpid():
        return

    print(stem.util.term.format('Keeping last words...',
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member

    # keep records
    _dump_last_word()

    try:
        strsignal = signal.strsignal(signum)
    except Exception:
        strsignal = signum
    print(stem.util.term.format(f'Exit with signal: {strsignal} <{frame}>',
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member


def process():
    """Main process."""
    #signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)
    #signal.signal(signal.SIGKILL, _signal_handler)

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
