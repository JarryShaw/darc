# -*- coding: utf-8 -*-
"""ZeroNet proxy."""

import os
import subprocess
import sys
import time
import urllib.parse
import warnings

import stem

import darc.typing as typing
from darc.error import ZeroNetBootstrapFailed, render_error
from darc.proxy.tor import tor_bootstrap

# bootstrap wait
BS_WAIT = float(os.getenv('ZERONET_BS_WAIT', '10'))

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


def _zeronet_bootstrap():
    """ZeroNet bootstrap."""
    global _ZERONET_BS_FLAG, _ZERONET_PROC

    # launch Tor first
    tor_bootstrap()

    # launch ZeroNet process
    args = [os.path.join(ZERONET_PATH, 'ZeroNet.sh'), 'main']
    _ZERONET_PROC = subprocess.Popen(args)
    time.sleep(BS_WAIT)

    # _ZERONET_PROC = subprocess.Popen(
    #     args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    # )

    # stdout, stderr = _ZERONET_PROC.communicate()
    # if DEBUG:
    #     print(render_error(stdout, stem.util.term.Color.BLUE))  # pylint: disable=no-member
    # print(render_error(stderr, stem.util.term.Color.RED))  # pylint: disable=no-member

    returncode = _ZERONET_PROC.returncode
    if returncode is not None and returncode != 0:
        raise subprocess.CalledProcessError(returncode, args,
                                            _ZERONET_PROC.stdout,
                                            _ZERONET_PROC.stderr)

    # update flag
    _ZERONET_BS_FLAG = True


def zeronet_bootstrap():
    """Bootstrap wrapper for ZeroNet."""
    # don't re-bootstrap
    if _ZERONET_BS_FLAG:
        return

    print(stem.util.term.format('Bootstrapping ZeroNet proxy...',
                                stem.util.term.Color.BLUE))  # pylint: disable=no-member
    for _ in range(ZERONET_RETRY+1):
        try:
            _zeronet_bootstrap()
            break
        except Exception as error:
            warning = warnings.formatwarning(error, ZeroNetBootstrapFailed, __file__, 68, 'zeronet_bootstrap()')
            print(render_error(warning, stem.util.term.Color.YELLOW), end='', file=sys.stderr)  # pylint: disable=no-member


def has_zeronet(link_pool: typing.Set[str]) -> bool:
    """Check if contain ZeroNet links."""
    for link in link_pool:
        # <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
        parse = urllib.parse.urlparse(link)

        if parse.netloc in (f'127.0.0.1:{ZERONET_PORT}', f'localhost:{ZERONET_PORT}'):
            return True
    return False
