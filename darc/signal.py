# -*- coding: utf-8 -*-
# pylint: disable=ungrouped-imports
"""Signal Handling
=====================

The :mod:`darc.signal` module contains the handlers for OS-level
signals, c.f. :mod:`signal`, for the :mod:`darc` module.

"""

import collections
import enum
import os
import signal
from typing import TYPE_CHECKING, cast

from darc._compat import strsignal
from darc.const import FLAG_MP, FLAG_TH, PATH_ID, getpid
from darc.logging import logger

__all__ = ['register']

if TYPE_CHECKING:
    from multiprocessing import Process
    from signal import Handlers, Signals  # pylint: disable=no-name-in-module
    from threading import Thread
    from types import FrameType
    from typing import Any, Callable, Dict, List, Optional, Union

#: Dict[int, List[Callable[[Optional[Union[int, Signals]], Optional[FrameType]], Any]]]:
#: List of registered custom signal handlers.
_HANDLER_REGISTRY = collections.defaultdict(list)  # type: Dict[int, List[Callable[[Optional[Union[int, Signals]], Optional[FrameType]], Any]]] # pylint: disable=line-too-long


def register(
        signum: 'Union[int, Signals]',
        handler: 'Callable[[Optional[Union[int, Signals]], Optional[FrameType]], Any]', *,
        _index: 'Optional[int]' = None
    ) -> 'Union[Callable[[Signals, FrameType], Any], int, Handlers, None]':
    """Register signal handler.

    Args:
        signum: The signal to register.
        handler: The signal handler function to be registered with :func:`signal.signal`.

    Keyword Args:
        _index: Position index for the signal handler function.

    See Also:
        The signal handler functions will be saved into
        :data:`~darc.signal._HANDLER_REGISTRY`.

    """
    if isinstance(signum, enum.Enum):
        sigint = signum.value
    else:
        sigint = signum

    if _index is None:
        _HANDLER_REGISTRY[sigint].append(handler)
    else:
        _HANDLER_REGISTRY[sigint].insert(_index, handler)
    return signal.signal(signum, generic_handler)


def generic_handler(signum: 'Optional[Union[int, Signals]]' = None,
                    frame: 'Optional[FrameType]' = None) -> None:
    """Generic signal handler.

    If the current process is not the main process, the function
    shall transfer the signal to the main process.

    The function is to be registered through :func:`signal.signal`
    and calls all registered signal handlers from the
    :data:`~darc.signal._HANDLER_REGISTRY` mapping.

    Args:
        signum: The signal to handle.
        frame (types.FrameType): The traceback frame from the signal.

    See Also:
        * :func:`darc.const.getpid`

    """
    if signum is None:
        return

    if os.getpid() != (pid := getpid()):
        os.kill(pid, signum)
        return

    if isinstance(signum, enum.Enum):
        sigint = signum.value
    else:
        sigint = signum

    for func in _HANDLER_REGISTRY[sigint]:
        func(signum, frame)

    try:
        sig = strsignal(signum) if signum else signum
    except Exception:
        sig = f'Signal: {signum}'
    logger.info('[DARC] Handled signal: %s <%s>', sig, frame)


def exit_signal(signum: 'Optional[Union[int, Signals]]' = None,
                 frame: 'Optional[FrameType]' = None) -> None:
    """Handler for exiting signals.

    If the current process is not the main process, the function
    shall transfer the signal to the main process.

    Args:
        signum: The signal to handle.
        frame (types.FrameType): The traceback frame from the signal.

    See Also:
        * :func:`darc.const.getpid`

    """
    from darc.process import _WORKER_POOL  # pylint: disable=import-outside-toplevel
    if FLAG_MP and _WORKER_POOL:
        for proc in cast('List[Process]', _WORKER_POOL):
            proc.kill()
            proc.join()

    if FLAG_TH and _WORKER_POOL:
        for thrd in cast('List[Thread]', _WORKER_POOL):
            thrd._stop()  # type: ignore[attr-defined] # pylint: disable=protected-access
            thrd.join()

    if os.path.isfile(PATH_ID):
        os.remove(PATH_ID)

    try:
        sig = strsignal(signum) if signum else signum
    except Exception:
        sig = signum
    logger.info('[DARC] Exit with signal: %s <%s>', sig, frame)
