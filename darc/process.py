# -*- coding: utf-8 -*-
"""Main processing."""

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
    """Load data to queue."""
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
    """Dump data in queue."""
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
    """Fetch links from queue."""
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
    """Fetch links from queue."""
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
    """Signal handler."""
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
    """Main process."""
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
