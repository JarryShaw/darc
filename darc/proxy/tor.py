# -*- coding: utf-8 -*-
"""Tor proxy."""

import getpass
import json
import os
import pprint
import re
import shutil
import sys
import traceback
import urllib
import warnings

import selenium
import stem.control
import stem.process
import stem.util.term

import darc.typing as typing
from darc.const import DEBUG, VERBOSE
from darc.error import TorBootstrapFailed, render_error

__all__ = ['TOR_REQUESTS_PROXY', 'TOR_SELENIUM_PROXY']

# Tor configs
TOR_CFG = json.loads(os.getenv('TOR_CFG', '{}'))

# bootstrap wait
BS_WAIT = float(os.getenv('TOR_WAIT', '90'))

# Tor Socks5 proxy & control port
TOR_PORT = os.getenv('TOR_PORT', '9050')
TOR_CTRL = os.getenv('TOR_CTRL', '9051')

# Tor authentication
TOR_PASS = os.getenv('TOR_PASS')

# use stem to manage Tor?
TOR_STEM = bool(int(os.getenv('TOR_STEM', '1')))

# Tor bootstrap retry
TOR_RETRY = int(os.getenv('TOR_RETRY', '3'))

# proxy
TOR_REQUESTS_PROXY = {
    # c.f. https://stackoverflow.com/a/42972942
    'http':  f'socks5h://localhost:{TOR_PORT}',
    'https': f'socks5h://localhost:{TOR_PORT}'
}
TOR_SELENIUM_PROXY = selenium.webdriver.Proxy()
TOR_SELENIUM_PROXY.proxyType = selenium.webdriver.common.proxy.ProxyType.MANUAL
TOR_SELENIUM_PROXY.http_proxy = f'socks5://localhost:{TOR_PORT}'
TOR_SELENIUM_PROXY.ssl_proxy = f'socks5://localhost:{TOR_PORT}'

# Tor bootstrapped flag
_TOR_BS_FLAG = not TOR_STEM  # only if Tor managed through stem
# Tor controller
_TOR_CTRL = None
# Tor daemon process
_TOR_PROC = None
# Tor bootstrap config
_TOR_CONFIG = {
    'SocksPort': TOR_PORT,
    'ControlPort': TOR_CTRL,
}
_TOR_CONFIG.update(TOR_CFG)

if VERBOSE:
    print(stem.util.term.format('-*- TOR PROXY -*-',
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    pprint.pprint(_TOR_CONFIG)
    print(stem.util.term.format('-' * shutil.get_terminal_size().columns,
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member


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
        config=_TOR_CONFIG,
        init_msg_handler=print_bootstrap_lines,
        timeout=BS_WAIT,
        take_ownership=True,
    )

    if TOR_PASS is None:
        TOR_PASS = getpass.getpass('Tor authentication: ')

    # Tor controller process
    _TOR_CTRL = stem.control.Controller.from_port(port=int(TOR_CTRL))
    _TOR_CTRL.authenticate(TOR_PASS)

    # update flag
    _TOR_BS_FLAG = True


def tor_bootstrap():
    """Bootstrap wrapper for Tor."""
    # don't re-bootstrap
    if _TOR_BS_FLAG:
        return

    print(stem.util.term.format('Bootstrapping Tor proxy...',
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    for _ in range(TOR_RETRY+1):
        try:
            _tor_bootstrap()
            break
        except Exception as error:
            if DEBUG:
                error = f'[Error bootstraping Tor proxy]' + os.linesep + traceback.format_exc() + '-' * shutil.get_terminal_size().columns  # pylint: disable=line-too-long
            print(render_error(error, stem.util.term.Color.CYAN), end='', file=sys.stderr)  # pylint: disable=no-member

            warning = warnings.formatwarning(error, TorBootstrapFailed, __file__, 91, 'tor_bootstrap()')
            print(render_error(warning, stem.util.term.Color.YELLOW), end='', file=sys.stderr)  # pylint: disable=no-member
    print(stem.util.term.format('-' * shutil.get_terminal_size().columns,
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member


def has_tor(link_pool: typing.Set[str]) -> bool:
    """Check if contain Tor links."""
    for link in link_pool:
        # <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
        parse = urllib.parse.urlparse(link)
        host = parse.netloc or parse.hostname

        if re.fullmatch(r'.*?\.onion', host):
            return True
    return False
