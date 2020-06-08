# -*- coding: utf-8 -*-
"""ZeroNet Proxy
====================

The :mod:`darc.proxy.zeronet` module contains the auxiliary functions
around managing and processing the ZeroNet proxy.

"""

import os
import pprint
import shlex
import shutil
import subprocess
import sys
import traceback
import warnings

import stem.util.term

import darc.typing as typing
from darc.const import DEBUG, VERBOSE
from darc.error import ZeroNetBootstrapFailed, render_error
from darc.link import Link
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

# ZeroNet bootstrapped flag
_ZERONET_BS_FLAG = False
# ZeroNet daemon process
_ZERONET_PROC = None
# ZeroNet bootstrap args
_ZERONET_ARGS = [os.path.join(ZERONET_PATH, 'ZeroNet.sh'), 'main']
_ZERONET_ARGS.extend(ZERONET_ARGS)

if DEBUG:
    print(stem.util.term.format('-*- ZERONET PROXY -*-',
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    print(render_error(pprint.pformat(_ZERONET_ARGS), stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    print(stem.util.term.format('-' * shutil.get_terminal_size().columns,
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member


def _zeronet_bootstrap():
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
    global _ZERONET_BS_FLAG, _ZERONET_PROC

    # launch Tor first
    tor_bootstrap()

    # launch ZeroNet process
    _ZERONET_PROC = subprocess.Popen(
        _ZERONET_ARGS, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )

    try:
        stdout, stderr = _ZERONET_PROC.communicate(timeout=BS_WAIT)
    except subprocess.TimeoutExpired as error:
        stdout, stderr = error.stdout, error.stderr
    if VERBOSE:
        if stdout is not None:
            print(render_error(stdout, stem.util.term.Color.BLUE))  # pylint: disable=no-member
    if stderr is not None:
        print(render_error(stderr, stem.util.term.Color.RED))  # pylint: disable=no-member

    returncode = _ZERONET_PROC.returncode
    if returncode is not None and returncode != 0:
        raise subprocess.CalledProcessError(returncode, _ZERONET_ARGS,
                                            _ZERONET_PROC.stdout,
                                            _ZERONET_PROC.stderr)

    # update flag
    _ZERONET_BS_FLAG = True


def zeronet_bootstrap():
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

    print(stem.util.term.format('-*- ZeroNet Bootstrap -*-',
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    for _ in range(ZERONET_RETRY+1):
        try:
            _zeronet_bootstrap()
            break
        except Exception as error:
            if DEBUG:
                message = '[Error bootstraping ZeroNet proxy]' + os.linesep + traceback.format_exc()
                print(render_error(message, stem.util.term.Color.RED), end='', file=sys.stderr)  # pylint: disable=no-member

            warning = warnings.formatwarning(error, ZeroNetBootstrapFailed, __file__, 94, 'zeronet_bootstrap()')
            print(render_error(warning, stem.util.term.Color.YELLOW), end='', file=sys.stderr)  # pylint: disable=no-member
    print(stem.util.term.format('-' * shutil.get_terminal_size().columns,
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member


def has_zeronet(link_pool: typing.Set[Link]) -> bool:
    """Check if contain ZeroNet links.

    Args:
        link_pool: Link pool to check.

    Returns:
        If the link pool contains ZeroNet links.

    See Also:
        * :func:`darc.link.parse_link`
        * :func:`darc.link.urlparse`
        * :data:`darc.proxy.zeronet.ZERONET_PORT`

    """
    for link in link_pool:
        # <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
        parse = link.url_parse

        if parse.netloc in (f'127.0.0.1:{ZERONET_PORT}', f'localhost:{ZERONET_PORT}'):
            return True
    return False
