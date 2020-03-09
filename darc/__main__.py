# -*- coding: utf-8 -*-
"""Module entrypoint."""

import argparse
import contextlib
import shutil
import sys
import traceback

import stem.util.term

import darc.typing as typing
from darc.const import DEBUG
from darc.db import save_requests
from darc.process import process
from darc.proxy.freenet import _FREENET_PROC
from darc.proxy.i2p import _I2P_PROC
from darc.proxy.tor import _TOR_CTRL, _TOR_PROC
from darc.proxy.zeronet import _ZERONET_PROC


def _exit():
    """Gracefully exit."""
    def caller(target: typing.Optional[typing.Union[typing.Queue, typing.Popen]], function: str):
        """Wrapper caller."""
        if target is None:
            return
        with contextlib.suppress(BaseException):
            getattr(target, function)()

    # close link queue
    #caller(MANAGER, 'shutdown')

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
    parser = argparse.ArgumentParser('darc',
                                     description='darkweb swiss knife crawler')

    parser.add_argument('-f', '--file', action='append', help='read links from file')
    parser.add_argument('link', nargs=argparse.REMAINDER, help='links to craw')

    return parser


def main():
    """Entrypoint."""
    parser = get_parser()
    args = parser.parse_args()

    if DEBUG:
        print(stem.util.term.format('-*- Initialisation -*-', stem.util.term.Color.MAGENTA))  # pylint: disable=no-member

    link_list = list()
    for link in filter(None, map(lambda s: s.strip(), args.link)):
        if DEBUG:
            print(stem.util.term.format(link, stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
        #QUEUE_REQUESTS.put(link)
        link_list.append(link)

    if args.file is not None:
        for path in args.file:
            with open(path) as file:
                for line in filter(None, map(lambda s: s.strip(), file)):
                    if line.startswith('#'):
                        continue
                    if DEBUG:
                        print(stem.util.term.format(line, stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
                    #QUEUE_REQUESTS.put(line)
                    link_list.append(line)

    # write to database
    save_requests(link_list)

    if DEBUG:
        print(stem.util.term.format('-' * shutil.get_terminal_size().columns, stem.util.term.Color.MAGENTA))  # pylint: disable=no-member

    try:
        process()
    except BaseException:
        traceback.print_exc()
    _exit()


if __name__ == "__main__":
    sys.exit(main())
