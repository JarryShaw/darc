# -*- coding: utf-8 -*-
"""ZeroNet proxy."""

import os
import subprocess
import sys
import urllib.parse
import warnings

import stem

import darc.typing as typing
from darc.error import ZeroNetBootstrapFailed, render_error
from darc.proxy.tor import tor_bootstrap

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
    """ZERONET bootstrap."""
    global _ZERONET_BS_FLAG, _ZERONET_PROC

    # launch Tor first
    tor_bootstrap()

    # launch ZeroNet process
    args = [os.path.join(ZERONET_PATH, 'ZeroNet.sh'), 'start']
    _ZERONET_PROC = subprocess.Popen(
        args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if _ZERONET_PROC.returncode != 0:
        raise subprocess.CalledProcessError(_ZERONET_PROC.returncode, args,
                                            _ZERONET_PROC.stdout, _ZERONET_PROC.stderr)

    # update flag
    _ZERONET_BS_FLAG = True


def zeronet_bootstrap():
    """Bootstrap wrapper for ZERONET."""
    # don't re-bootstrap
    if _ZERONET_BS_FLAG:
        return

    for _ in range(ZERONET_RETRY+1):
        try:
            _zeronet_bootstrap()
            break
        except Exception as error:
            warning = warnings.formatwarning(error, ZeroNetBootstrapFailed, __file__, 53, 'zeronet_bootstrap()')
            print(render_error(warning, stem.util.term.Color.YELLOW), end='', file=sys.stderr)  # pylint: disable=no-member


def has_zeronet(link_pool: typing.Set[str]) -> bool:
    """Check if contain ZERONET links."""
    for link in link_pool:
        # <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
        parse = urllib.parse.urlparse(link)

        if parse.netloc == f'127.0.0.1:{ZERONET_PORT}':
            return True
    return False
