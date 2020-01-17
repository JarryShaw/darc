# -*- coding: utf-8 -*-
"""The darc project."""

import signal

import stem.util.term

import darc.typing as typing
from darc.process import _dump_last_word


def signal_handler(signum: typing.Union[int, signal.Signals],  # pylint: disable=unused-argument,no-member
                   frame: typing.Optional[typing.FrameType] = None):  # pylint: disable=unused-argument
    """Signal handler."""
    print(stem.util.term.format('Keeping last words...',
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member

    # keep records
    _dump_last_word()

    print(stem.util.term.format(f'Exit with signal: {signal.strsignal(signal)} <{frame}>',
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member


signal.signal(signal.SIGINT, _dump_last_word)
signal.signal(signal.SIGTERM, _dump_last_word)
#signal.signal(signal.SIGKILL, _dump_last_word)
