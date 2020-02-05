# -*- coding: utf-8 -*-
"""Module entrypoint."""

import argparse
import contextlib
import sys
import traceback

import darc.typing as typing
from darc.const import MANAGER, QUEUE_REQUESTS
from darc.process import process
from darc.proxy.i2p import _I2P_PROC
from darc.proxy.tor import _TOR_CTRL, _TOR_PROC
from darc.proxy.zeronet import _ZERONET_PROC


def _exit():
    """Gracefully exit."""
    def caller(target: typing.Optional[typing.Union[typing.Queue, typing.Popen]], function: str):
        """Wrapper caller."""
        if target is None:
            return
        with contextlib.suppress():
            getattr(target, function)()

    # close link queue
    caller(MANAGER, 'shutdown')

    # close Tor processes
    caller(_TOR_CTRL, 'close')
    caller(_TOR_PROC, 'kill')
    caller(_TOR_PROC, 'wait')

    # close I2P process
    caller(_I2P_PROC, 'kill')
    caller(_I2P_PROC, 'wait')
    caller(_ZERONET_PROC, 'kill')
    caller(_ZERONET_PROC, 'wait')


def get_parser() -> typing.ArgumentParser:
    """Argument parser."""
    parser = argparse.ArgumentParser('darc')

    parser.add_argument('-f', '--file', help='read links from file')
    parser.add_argument('link', nargs=argparse.REMAINDER, help='links to craw')

    return parser


def main():
    """Entrypoint."""
    parser = get_parser()
    args = parser.parse_args()

    for link in args.link:
        QUEUE_REQUESTS.put(link)

    if args.file is not None:
        with open(args.file) as file:
            for line in file:
                QUEUE_REQUESTS.put(line.strip())

    try:
        process()
    except BaseException:
        traceback.print_exc()
    _exit()


if __name__ == "__main__":
    sys.exit(main())
