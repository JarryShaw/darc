# -*- coding: utf-8 -*-
"""Freenet proxy."""

import getpass
import os
import platform
import pprint
import shlex
import shutil
import subprocess
import sys
import traceback
import urllib.parse
import warnings

import stem

import darc.typing as typing
from darc.const import DARC_USER, DEBUG, VERBOSE
from darc.error import FreenetBootstrapFailed, UnsupportedPlatform, render_error

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
if getpass.getuser() == 'root':
    _system = platform.system()
    if _system in ['Linux', 'Darwin']:
        _FREENET_ARGS = ['su', '-', DARC_USER, os.path.join(FREENET_PATH, 'run.sh'), 'start']
    else:
        raise UnsupportedPlatform(f'unsupported system: {_system}')
else:
    _FREENET_ARGS = [os.path.join(FREENET_PATH, 'run.sh'), 'start']
_FREENET_ARGS.extend(FREENET_ARGS)

if VERBOSE:
    print(stem.util.term.format('-*- FREENET PROXY -*-',
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    pprint.pprint(_FREENET_ARGS)
    print(stem.util.term.format('-' * shutil.get_terminal_size().columns,
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member


def _freenet_bootstrap():
    """Freenet bootstrap."""
    global _FREENET_BS_FLAG, _FREENET_PROC

    # launch Freenet process
    _FREENET_PROC = subprocess.Popen(
        _FREENET_ARGS, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
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
    """Bootstrap wrapper for Freenet."""
    # don't re-bootstrap
    if _FREENET_BS_FLAG:
        return

    print(stem.util.term.format('Bootstrapping Freenet proxy...',
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    for _ in range(FREENET_RETRY+1):
        try:
            _freenet_bootstrap()
            break
        except Exception as error:
            if DEBUG:
                error = f'[Error bootstraping Freenet proxy]' + os.linesep + traceback.format_exc() + '-' * shutil.get_terminal_size().columns  # pylint: disable=line-too-long
            print(render_error(error, stem.util.term.Color.CYAN), end='', file=sys.stderr)  # pylint: disable=no-member

            warning = warnings.formatwarning(error, FreenetBootstrapFailed, __file__, 64, 'freenet_bootstrap()')
            print(render_error(warning, stem.util.term.Color.YELLOW), end='', file=sys.stderr)  # pylint: disable=no-member


def has_freenet(link_pool: typing.Set[str]) -> bool:
    """Check if contain Freenet links."""
    for link in link_pool:
        # <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
        parse = urllib.parse.urlparse(link)

        if parse.netloc in (f'127.0.0.1:{FREENET_PORT}', f'localhost:{FREENET_PORT}'):
            return True
    return False
