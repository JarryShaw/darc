# -*- coding: utf-8 -*-
"""ZeroNet proxy."""

import os
import pprint
import shlex
import shutil
import subprocess
import sys
import time
import traceback
import urllib.parse
import warnings

import stem

import darc.typing as typing
from darc.const import DEBUG
from darc.error import ZeroNetBootstrapFailed, render_error
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
    print(stem.util.term.format('ZERONET_ARGS',
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    pprint.pprint(_ZERONET_ARGS)
    print(stem.util.term.format('-' * shutil.get_terminal_size().columns,
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member


def _zeronet_bootstrap():
    """ZeroNet bootstrap."""
    global _ZERONET_BS_FLAG, _ZERONET_PROC

    # launch Tor first
    tor_bootstrap()

    # launch ZeroNet process
    _ZERONET_PROC = subprocess.Popen(_ZERONET_ARGS)
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
        raise subprocess.CalledProcessError(returncode, _ZERONET_ARGS,
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
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    for _ in range(ZERONET_RETRY+1):
        try:
            _zeronet_bootstrap()
            break
        except Exception as error:
            if DEBUG:
                error = f'[Error bootstraping ZeroNet proxy]' + os.linesep + traceback.format_exc() + '-' * shutil.get_terminal_size().columns  # pylint: disable=line-too-long
            print(render_error(error, stem.util.term.Color.CYAN), end='', file=sys.stderr)  # pylint: disable=no-member

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
