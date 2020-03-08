# -*- coding: utf-8 -*-
"""Freenet Proxy
===================

The :mod:`darc.proxy.freenet` module contains the auxiliary functions
around managing and processing the Freenet proxy.

"""

import getpass
import os
import platform
import pprint
import shlex
import shutil
import subprocess
import sys
import traceback
import warnings

import stem.util.term

import darc.typing as typing
from darc.const import DARC_USER, DEBUG, VERBOSE
from darc.error import FreenetBootstrapFailed, UnsupportedPlatform, render_error
from darc.link import urlparse

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

# Freenet bootstrapped flag
_FREENET_BS_FLAG = False
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
        _FREENET_ARGS = list()
else:
    _FREENET_ARGS = [os.path.join(FREENET_PATH, 'run.sh'), 'start']
_FREENET_ARGS.extend(FREENET_ARGS)

if DEBUG:
    print(stem.util.term.format('-*- FREENET PROXY -*-',
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    if _unsupported:
        print(stem.util.term.format(f'unsupported system: {platform.system()}',
                                    stem.util.term.Color.RED))  # pylint: disable=no-member
    else:
        print(render_error(pprint.pformat(_FREENET_ARGS), stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    print(stem.util.term.format('-' * shutil.get_terminal_size().columns,
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member


def _freenet_bootstrap():
    """Freenet bootstrap.

    The bootstrap arguments are defined as :data:`~darc.proxy.freenet._FREENET_ARGS`.

    Raises:
        subprocess.CalledProcessError: If the return code of :data:`~darc.proxy.freenet._FREENET_PROC` is non-zero.

    See Also:
        * :func:`darc.proxy.freenet.freenet_bootstrap`
        * :data:`darc.proxy.freenet.BS_WAIT`
        * :data:`darc.proxy.freenet._FREENET_BS_FLAG`
        * :data:`darc.proxy.freenet._FREENET_PROC`

    """
    global _FREENET_BS_FLAG, _FREENET_PROC

    # launch Freenet process
    _FREENET_PROC = subprocess.Popen(
        _FREENET_ARGS, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )

    try:
        stdout, stderr = _FREENET_PROC.communicate(timeout=BS_WAIT)
    except subprocess.TimeoutExpired as error:
        stdout, stderr = error.stdout, error.stderr
    if VERBOSE:
        if stdout is not None:
            print(render_error(stdout, stem.util.term.Color.BLUE))  # pylint: disable=no-member
    if stderr is not None:
        print(render_error(stderr, stem.util.term.Color.RED))  # pylint: disable=no-member

    returncode = _FREENET_PROC.returncode
    if returncode is not None and returncode != 0:
        raise subprocess.CalledProcessError(returncode, _FREENET_ARGS,
                                            _FREENET_PROC.stdout,
                                            _FREENET_PROC.stderr)

    # update flag
    _FREENET_BS_FLAG = True


def freenet_bootstrap():
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

    print(stem.util.term.format('-*- Freenet Bootstrap -*-',
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    for _ in range(FREENET_RETRY+1):
        try:
            _freenet_bootstrap()
            break
        except Exception as error:
            if DEBUG:
                message = f'[Error bootstraping Freenet proxy]' + os.linesep + traceback.format_exc()
                print(render_error(message, stem.util.term.Color.RED), end='', file=sys.stderr)  # pylint: disable=no-member

            warning = warnings.formatwarning(error, FreenetBootstrapFailed, __file__, 108, 'freenet_bootstrap()')
            print(render_error(warning, stem.util.term.Color.YELLOW), end='', file=sys.stderr)  # pylint: disable=no-member
    print(stem.util.term.format('-' * shutil.get_terminal_size().columns,
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member


def has_freenet(link_pool: typing.Iterable[str]) -> bool:
    """Check if contain Freenet links.

    Args:
        link_pool: Link pool to check.

    Returns:
        If the link pool contains Freenet links.

    See Also:
        * :func:`darc.link.parse_link`
        * :func:`darc.link.urlparse`
        * :data:`darc.proxy.freenet.FREENET_PORT`

    """
    for link in link_pool:
        # <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
        parse = urlparse(link)

        if parse.netloc in (f'127.0.0.1:{FREENET_PORT}', f'localhost:{FREENET_PORT}'):
            return True
    return False
