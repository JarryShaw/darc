# -*- coding: utf-8 -*-
# pylint: disable=ungrouped-imports
"""Freenet Proxy
===================

The :mod:`darc.proxy.freenet` module contains the auxiliary functions
around managing and processing the Freenet proxy.

"""

import contextlib
import getpass
import os
import platform
import shlex
import signal
import subprocess  # nosec: B404
import time
from typing import TYPE_CHECKING, cast

import psutil

from darc.const import DARC_USER, DEBUG, getpid
from darc.error import FreenetBootstrapFailed, UnsupportedPlatform
from darc.logging import DEBUG as LOG_DEBUG
from darc.logging import ERROR as LOG_ERROR
from darc.logging import INFO as LOG_INFO
from darc.logging import VERBOSE as LOG_VERBOSE
from darc.logging import WARNING as LOG_WARNING
from darc.logging import logger

if TYPE_CHECKING:
    from io import IO  # type: ignore[attr-defined] # pylint: disable=no-name-in-module
    from signal import Signals  # pylint: disable=no-name-in-module
    from subprocess import Popen  # nosec: B404
    from types import FrameType
    from typing import NoReturn, Optional, Union

# ZeroNet args
FREENET_ARGS = shlex.split(os.getenv('FREENET_ARGS', ''))

# bootstrap wait
BS_WAIT = float(os.getenv('FREENET_WAIT', '90'))

# Freenet port
FREENET_PORT = os.getenv('FREENET_PORT', '8888')

# Freenet bootstrap retry
FREENET_RETRY = int(os.getenv('FREENET_RETRY', '3'))

# Freenet project path
FREENET_PATH = os.getenv('FREENET_PATH', '/usr/local/src/freenet')

# manage Freenet through darc?
_MNG_FREENET = bool(int(os.getenv('DARC_FREENET', '1')))

# Freenet bootstrapped flag
_FREENET_BS_FLAG = not _MNG_FREENET
# Freenet daemon process
_FREENET_PROC = None
# Freenet bootstrap args
_unsupported = False
if getpass.getuser() == 'root':
    _system = platform.system()
    if _system in ['Linux', 'Darwin']:
        _FREENET_ARGS = ['su', '-', DARC_USER, os.path.join(FREENET_PATH, 'run.sh'), 'start']
    else:
        _unsupported = True
        _FREENET_ARGS = []
else:
    _FREENET_ARGS = [os.path.join(FREENET_PATH, 'run.sh'), 'start']
_FREENET_ARGS.extend(FREENET_ARGS)

if _unsupported:
    if DEBUG:
        logger.debug('-*- FREENET PROXY -*-')
        logger.pline(LOG_ERROR, 'unsupported system: %s', platform.system())
        logger.pline(LOG_DEBUG, logger.horizon)
else:
    logger.plog(LOG_DEBUG, '-*- FREENET PROXY -*-', object=_FREENET_ARGS)


def launch_freenet() -> 'Popen[bytes]':
    """Launch Freenet process.

    See Also:
        This function mocks the behaviour of :func:`stem.process.launch_tor`.

    """
    pidfile = os.path.join(FREENET_PATH, 'Freenet.pid')
    with contextlib.suppress(OSError):
        os.remove(pidfile)

    zeronet_process = None
    try:
        zeronet_process = subprocess.Popen(  # pylint: disable=consider-using-with # nosec
            _FREENET_ARGS, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )

        def timeout_handlet(signum: 'Optional[Union[int, Signals]]' = None,
                            frame: 'Optional[FrameType]' = None) -> 'NoReturn':
            raise OSError('reached a %i second timeout without success' % BS_WAIT)

        signal.signal(signal.SIGALRM, timeout_handlet)
        signal.setitimer(signal.ITIMER_REAL, BS_WAIT)

        while True:
            init_line = cast(
                'IO[bytes]', zeronet_process.stdout
            ).readline().decode('utf-8', 'replace').strip()
            logger.pline(LOG_VERBOSE, init_line)

            if not init_line:
                if (code := zeronet_process.returncode) is not None and code == 0:
                    return zeronet_process
                raise OSError(f'Process terminated: Timed out [{code}]')

            if os.path.exists(pidfile):
                pid = getpid(pidfile)

                time.sleep(1)  # wait a little bit
                if psutil.pid_exists(pid):
                    return zeronet_process
    except BaseException:
        if zeronet_process is not None:
            zeronet_process.kill()  # don't leave a lingering process
            zeronet_process.wait()
        raise
    finally:
        signal.alarm(0)  # stop alarm


def _freenet_bootstrap() -> None:
    """Freenet bootstrap.

    The bootstrap arguments are defined as :data:`~darc.proxy.freenet._FREENET_ARGS`.

    Raises:
        subprocess.CalledProcessError: If the return code of :data:`~darc.proxy.freenet._FREENET_PROC` is non-zero.

    See Also:
        * :func:`darc.proxy.freenet.freenet_bootstrap`
        * :func:`darc.proxy.freenet.launch_freenet`
        * :data:`darc.proxy.freenet.BS_WAIT`
        * :data:`darc.proxy.freenet._FREENET_BS_FLAG`
        * :data:`darc.proxy.freenet._FREENET_PROC`

    """
    global _FREENET_BS_FLAG, _FREENET_PROC  # pylint: disable=global-statement

    # launch Freenet process
    _FREENET_PROC = launch_freenet()

    # update flag
    _FREENET_BS_FLAG = True


def freenet_bootstrap() -> None:
    """Bootstrap wrapper for Freenet.

    The function will bootstrap the Freenet proxy. It will retry for
    :data:`~darc.proxy.freenet.FREENET_RETRY` times in case of failure.

    Also, it will **NOT** re-bootstrap the proxy as is guaranteed by
    :data:`~darc.proxy.freenet._FREENET_BS_FLAG`.

    Warns:
        FreenetBootstrapFailed: If failed to bootstrap Freenet proxy.

    Raises:
        :exc:`UnsupportedPlatform`: If the system is not supported, i.e. not macOS or Linux.

    See Also:
        * :func:`darc.proxy.freenet._freenet_bootstrap`
        * :data:`darc.proxy.freenet.FREENET_RETRY`
        * :data:`darc.proxy.freenet._FREENET_BS_FLAG`

    """
    if _unsupported:
        raise UnsupportedPlatform(f'unsupported system: {platform.system()}')

    # don't re-bootstrap
    if _FREENET_BS_FLAG:
        return

    logger.info('-*- Freenet Bootstrap -*-')
    for _ in range(FREENET_RETRY+1):
        try:
            _freenet_bootstrap()
            break
        except Exception:
            if DEBUG:
                logger.ptb('[Error bootstraping Freenet proxy]')
            logger.pexc(LOG_WARNING, category=FreenetBootstrapFailed, line='freenet_bootstrap()')
    logger.pline(LOG_INFO, logger.horizon)
