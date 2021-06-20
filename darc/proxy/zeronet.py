# -*- coding: utf-8 -*-
# pylint: disable=ungrouped-imports
"""ZeroNet Proxy
====================

The :mod:`darc.proxy.zeronet` module contains the auxiliary functions
around managing and processing the ZeroNet proxy.

"""

import os
import shlex
import signal
import subprocess  # nosec: B404
from typing import TYPE_CHECKING, cast

from darc.const import DEBUG
from darc.error import ZeroNetBootstrapFailed
from darc.logging import DEBUG as LOG_DEBUG
from darc.logging import INFO as LOG_INFO
from darc.logging import VERBOSE as LOG_VERBOSE
from darc.logging import WARNING as LOG_WARNING
from darc.logging import logger
from darc.proxy.tor import tor_bootstrap

if TYPE_CHECKING:
    from io import IO  # type: ignore[attr-defined] # pylint: disable=no-name-in-module
    from signal import Signals  # pylint: disable=no-name-in-module
    from subprocess import Popen  # nosec: B404
    from types import FrameType
    from typing import NoReturn, Optional, Union

# ZeroNet args
ZERONET_ARGS = shlex.split(os.getenv('ZERONET_ARGS', ''))

# bootstrap wait
BS_WAIT = float(os.getenv('ZERONET_WAIT', '90'))

# ZeroNet port
ZERONET_PORT = os.getenv('ZERONET_PORT', '43110')

# ZeroNet bootstrap retry
ZERONET_RETRY = int(os.getenv('ZERONET_RETRY', '3'))

# ZeroNet project path
ZERONET_PATH = os.getenv('ZERONET_PATH', '/usr/local/src/zeronet')

# manage ZeroNet through darc?
_MNG_ZERONET = bool(int(os.getenv('DARC_ZERONET', '1')))

# ZeroNet bootstrapped flag
_ZERONET_BS_FLAG = not _MNG_ZERONET
# ZeroNet daemon process
_ZERONET_PROC = None
# ZeroNet bootstrap args
_ZERONET_ARGS = [os.path.join(ZERONET_PATH, 'ZeroNet.sh'), 'main']
_ZERONET_ARGS.extend(ZERONET_ARGS)
logger.plog(LOG_DEBUG, '-*- ZERONET PROXY -*-', object=_ZERONET_ARGS)


def launch_zeronet() -> 'Popen[bytes]':
    """Launch ZeroNet process.

    See Also:
        This function mocks the behaviour of :func:`stem.process.launch_tor`.

    """
    zeronet_process = None
    try:
        zeronet_process = subprocess.Popen(  # pylint: disable=consider-using-with # nosec
            _ZERONET_ARGS, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
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
                raise OSError('Process terminated: Timed out')

            if 'ConnServer Server port opened' in init_line:
                return zeronet_process
    except BaseException:
        if zeronet_process is not None:
            zeronet_process.kill()  # don't leave a lingering process
            zeronet_process.wait()
        raise
    finally:
        signal.alarm(0)  # stop alarm


def _zeronet_bootstrap() -> None:
    """ZeroNet bootstrap.

    The bootstrap arguments are defined as :data:`~darc.proxy.zeronet._ZERONET_ARGS`.

    Raises:
        subprocess.CalledProcessError: If the return code of :data:`~darc.proxy.zeronet._ZERONET_PROC` is non-zero.

    See Also:
        * :func:`darc.proxy.zeronet.zeronet_bootstrap`
        * :func:`darc.proxy.zeronet.launch_zeronet`
        * :data:`darc.proxy.zeronet.BS_WAIT`
        * :data:`darc.proxy.zeronet._ZERONET_BS_FLAG`
        * :data:`darc.proxy.zeronet._ZERONET_PROC`

    """
    global _ZERONET_BS_FLAG, _ZERONET_PROC  # pylint: disable=global-statement

    # launch Tor first
    tor_bootstrap()

    # launch ZeroNet process
    _ZERONET_PROC = launch_zeronet()

    # update flag
    _ZERONET_BS_FLAG = True


def zeronet_bootstrap() -> None:
    """Bootstrap wrapper for ZeroNet.

    The function will bootstrap the ZeroNet proxy. It will retry for
    :data:`~darc.proxy.zeronet.ZERONET_RETRY` times in case of failure.

    Also, it will **NOT** re-bootstrap the proxy as is guaranteed by
    :data:`~darc.proxy.zeronet._ZERONET_BS_FLAG`.

    Warns:
        ZeroNetBootstrapFailed: If failed to bootstrap ZeroNet proxy.

    Raises:
        :exc:`UnsupportedPlatform`: If the system is not supported, i.e. not macOS or Linux.

    See Also:
        * :func:`darc.proxy.zeronet._zeronet_bootstrap`
        * :data:`darc.proxy.zeronet.ZERONET_RETRY`
        * :data:`darc.proxy.zeronet._ZERONET_BS_FLAG`

    """
    # don't re-bootstrap
    if _ZERONET_BS_FLAG:
        return

    logger.info('-*- ZeroNet Bootstrap -*-')
    for _ in range(ZERONET_RETRY+1):
        try:
            _zeronet_bootstrap()
            break
        except Exception:
            if DEBUG:
                logger.ptb('[Error bootstraping ZeroNet proxy]')
            logger.pexc(LOG_WARNING, category=ZeroNetBootstrapFailed, line='zeronet_bootstrap()')
    logger.pline(LOG_INFO, logger.horizon)
