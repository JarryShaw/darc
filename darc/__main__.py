# -*- coding: utf-8 -*-
"""Module entrypoint."""

import argparse
import contextlib
import os
import shutil
import sys
import traceback
import warnings

import stem.util.term

import darc.typing as typing
from darc.const import DB, DB_WEB, DEBUG, FLAG_DB, PATH_ID, PATH_LN
from darc.db import _db_operation, _redis_command, save_requests
from darc.error import DatabaseOperaionFailed, render_error
from darc.link import parse_link
from darc.model import (HostnameModel, HostnameQueueModel, HostsModel, RequestsHistoryModel,
                        RequestsModel, RequestsQueueModel, RobotsModel, SeleniumModel,
                        SeleniumQueueModel, SitemapModel, URLModel)
from darc.process import process
from darc.proxy.freenet import _FREENET_PROC
from darc.proxy.i2p import _I2P_PROC
from darc.proxy.tor import _TOR_CTRL, _TOR_PROC
from darc.proxy.zeronet import _ZERONET_PROC
from darc.submit import SAVE_DB

# wait for Redis connection?
_WAIT_REDIS = bool(int(os.getenv('DARC_REDIS', '1')))


def _exit() -> None:
    """Gracefully exit."""
    def caller(target: typing.Optional[typing.Union[typing.Queue, typing.Popen]], function: str) -> None:
        """Wrapper caller."""
        if target is None:
            return
        with contextlib.suppress(BaseException):
            getattr(target, function)()

    # close Tor processes
    caller(_TOR_CTRL, 'close')
    caller(_TOR_PROC, 'kill')
    caller(_TOR_PROC, 'wait')

    # close I2P process
    caller(_I2P_PROC, 'kill')
    caller(_I2P_PROC, 'wait')

    # close ZeroNet process
    caller(_ZERONET_PROC, 'kill')
    caller(_ZERONET_PROC, 'wait')

    # close Freenet process
    caller(_FREENET_PROC, 'kill')
    caller(_FREENET_PROC, 'wait')


def get_parser() -> typing.ArgumentParser:
    """Argument parser."""
    from darc import __version__  # pylint: disable=import-outside-toplevel

    parser = argparse.ArgumentParser('darc',
                                     description='the darkweb crawling swiss army knife')
    parser.add_argument('-v', '--version', action='version', version=__version__)

    parser.add_argument('-t', '--type', action='store', required=True,
                        choices=['crawler', 'loader'], help='type of worker process')

    parser.add_argument('-f', '--file', action='append', help='read links from file')
    parser.add_argument('link', nargs=argparse.REMAINDER, help='links to craw')

    return parser


def main(argv: typing.Optional[typing.List[str]] = None) -> int:
    """Entrypoint.

    Args:
        argv: Optional command line arguments.

    Returns:
        Exit code.

    """
    parser = get_parser()
    args = parser.parse_args(argv)

    pid = os.getpid()
    with open(PATH_ID, 'w') as file:
        print(pid, file=file)

    # wait for Redis
    if _WAIT_REDIS:
        if not FLAG_DB:
            _redis_command('set', 'darc', pid)

    if FLAG_DB:
        while True:
            try:
                with DB:
                    _db_operation(DB.create_tables, [
                        HostnameQueueModel, RequestsQueueModel, SeleniumQueueModel,
                    ])
            except Exception as error:
                warning = warnings.formatwarning(error, DatabaseOperaionFailed, __file__, 102,  # type: ignore[arg-type]
                                                 'DB.create_tables([HostnameQueueModel, ...])')
                print(render_error(warning, stem.util.term.Color.YELLOW), end='', file=sys.stderr)  # pylint: disable=no-member
                continue
            break

    if SAVE_DB:
        while True:
            try:
                with DB_WEB:
                    _db_operation(DB_WEB.create_tables, [
                        HostnameModel, URLModel,
                        RobotsModel, SitemapModel, HostsModel,
                        RequestsModel, RequestsHistoryModel, SeleniumModel,
                    ])
            except Exception as error:
                warning = warnings.formatwarning(error, DatabaseOperaionFailed, __file__, 117,  # type: ignore[arg-type]
                                                 'DB.create_tables([HostnameModel, ...])')
                print(render_error(warning, stem.util.term.Color.YELLOW), end='', file=sys.stderr)  # pylint: disable=no-member
                continue
            break

    if DEBUG:
        print(stem.util.term.format('-*- Initialisation -*-', stem.util.term.Color.MAGENTA))  # pylint: disable=no-member

        # nuke the db
        if not FLAG_DB:
            _redis_command('delete', 'queue_hostname')
            _redis_command('delete', 'queue_requests')
            _redis_command('delete', 'queue_selenium')

    link_list = list()
    for link in filter(None, map(lambda s: s.strip(), args.link)):  # type: ignore[name-defined,var-annotated]
        if DEBUG:
            print(stem.util.term.format(link, stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
        link_list.append(link)

    if args.file is not None:
        for path in args.file:
            with open(path) as file:
                for line in filter(None, map(lambda s: s.strip(), file)):
                    if line.startswith('#'):
                        continue
                    if DEBUG:
                        print(stem.util.term.format(line, stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
                    link_list.append(line)

    # write to database
    link_pool = [parse_link(link) for link in link_list]
    save_requests(link_pool, score=0, nx=True)

    if DEBUG:
        print(stem.util.term.format('-' * shutil.get_terminal_size().columns, stem.util.term.Color.MAGENTA))  # pylint: disable=no-member

    # init link file
    if not os.path.isfile(PATH_LN):
        with open(PATH_LN, 'w') as file:
            print('proxy,scheme,host,hash,link', file=file)

    try:
        process(args.type)
    except BaseException:
        traceback.print_exc()
    _exit()

    return 0


if __name__ == "__main__":
    sys.exit(main())
