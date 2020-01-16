# -*- coding: utf-8 -*-
"""Tor proxy."""

import getpass
import re
import sys
import urllib
import warnings

import stem

import darc.typing as typing
from darc.const import DEBUG, TOR_CTRL, TOR_PASS, TOR_PORT, TOR_RETRY, TOR_STEM
from darc.error import TorBootstrapFailed, render_error

# Tor bootstrapped flag
_TOR_BS_FLAG = not TOR_STEM  # only if Tor managed through stem
# Tor controller
_TOR_CTRL = None
# Tor daemon process
_TOR_PROC = None


def renew_tor_session():
    """Renew Tor session."""
    if _TOR_CTRL is None:
        return
    _TOR_CTRL.signal(stem.Signal.NEWNYM)  # pylint: disable=no-member


def print_bootstrap_lines(line: str):
    """Print Tor bootstrap lines."""
    if DEBUG:
        print(stem.util.term.format(line, stem.util.term.Color.BLUE))  # pylint: disable=no-member
        return

    if 'Bootstrapped ' in line:
        print(stem.util.term.format(line, stem.util.term.Color.BLUE))  # pylint: disable=no-member


def _tor_bootstrap():
    """Tor bootstrap."""
    global _TOR_BS_FLAG, _TOR_CTRL, _TOR_PROC, TOR_PASS

    # launch Tor process
    _TOR_PROC = stem.process.launch_tor_with_config(
        config={
            'SocksPort': TOR_PORT,
            'ControlPort': TOR_CTRL,
        },
        take_ownership=True,
        init_msg_handler=print_bootstrap_lines,
    )

    if TOR_PASS is None:
        TOR_PASS = getpass.getpass('Tor authentication: ')

    # Tor controller process
    _TOR_CTRL = stem.control.Controller.from_port(port=int(TOR_CTRL))
    _TOR_CTRL.authenticate(TOR_PASS)

    # update flag
    #_TOR_BS_FLAG.value = True
    _TOR_BS_FLAG = True


def tor_bootstrap():
    """Bootstrap wrapper for Tor."""
    # don't re-bootstrap
    #if _TOR_BS_FLAG.value:
    if _TOR_BS_FLAG:
        return

    # with _TOR_BS_LOCK:
    for _ in range(TOR_RETRY+1):
        try:
            _tor_bootstrap()
            break
        except Exception as error:
            warning = warnings.formatwarning(error, TorBootstrapFailed, __file__, 514, 'tor_bootstrap()')
            print(render_error(warning, stem.util.term.Color.YELLOW), end='', file=sys.stderr)  # pylint: disable=no-member


def has_tor(link_pool: typing.Set[str]) -> bool:
    """Check if contain Tor links."""
    for link in link_pool:
        # <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
        parse = urllib.parse.urlparse(link)
        host = parse.hostname or parse.netloc

        if re.match(r'.*?\.onion', host):
            return True
    return False
