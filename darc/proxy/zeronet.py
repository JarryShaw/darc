# -*- coding: utf-8 -*-
# pylint: disable=ungrouped-imports
"""ZeroNet Proxy
====================

The :mod:`darc.proxy.zeronet` module contains the auxiliary functions
around managing and processing the ZeroNet proxy.

"""

import os
import shlex
import subprocess  # nosec: B404
import traceback

from darc.error import ZeroNetBootstrapFailed
from darc.logging import DEBUG as LOG_DEBUG
from darc.logging import WARNING as LOG_WARNING
from darc.logging import logger
from darc.proxy.tor import tor_bootstrap

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


def _zeronet_bootstrap() -> None:
    """ZeroNet bootstrap.

    The bootstrap arguments are defined as :data:`~darc.proxy.zeronet._ZERONET_ARGS`.

    Raises:
        subprocess.CalledProcessError: If the return code of :data:`~darc.proxy.zeronet._ZERONET_PROC` is non-zero.

    See Also:
        * :func:`darc.proxy.zeronet.zeronet_bootstrap`
        * :data:`darc.proxy.zeronet.BS_WAIT`
        * :data:`darc.proxy.zeronet._ZERONET_BS_FLAG`
        * :data:`darc.proxy.zeronet._ZERONET_PROC`

    """
    global _ZERONET_BS_FLAG, _ZERONET_PROC  # pylint: disable=global-statement

    # launch Tor first
    tor_bootstrap()

    # launch ZeroNet process
    _ZERONET_PROC = subprocess.Popen(  # pylint: disable=consider-using-with # nosec
        _ZERONET_ARGS, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )

    try:
        stdout, stderr = _ZERONET_PROC.communicate(timeout=BS_WAIT)
    except subprocess.TimeoutExpired as error:
        stdout, stderr = error.stdout, error.stderr
    if stdout is not None:
        logger.verbose(stdout)
    if stderr is not None:
        logger.error(stderr)

    returncode = _ZERONET_PROC.returncode or -1
    if returncode != 0:
        raise subprocess.CalledProcessError(returncode, _ZERONET_ARGS, stdout, stderr)

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

    logger.debug('-*- ZeroNet Bootstrap -*-')
    for _ in range(ZERONET_RETRY+1):
        try:
            _zeronet_bootstrap()
            break
        except Exception:
            logger.debug('[Error bootstraping ZeroNet proxy]\n%s', traceback.format_exc().rstrip())
            logger.perror('zeronet_bootstrap()', ZeroNetBootstrapFailed, level=LOG_WARNING)
    logger.pline(LOG_DEBUG, logger.horizon)
