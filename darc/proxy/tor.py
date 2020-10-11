# -*- coding: utf-8 -*-
"""Tor Proxy
===============

The :mod:`darc.proxy.tor` module contains the auxiliary functions
around managing and processing the Tor proxy.

"""

import getpass
import json
import os
import pprint
import shutil
import sys
import traceback
import warnings

import selenium.webdriver
import selenium.webdriver.common.proxy
import stem.control
import stem.process
import stem.util.term

from darc.const import DEBUG
from darc.error import TorBootstrapFailed, TorRenewFailed, render_error

# Tor configs
TOR_CFG = json.loads(os.getenv('TOR_CFG', '{}'))

# bootstrap wait
BS_WAIT = float(os.getenv('TOR_WAIT', '90'))

# Tor Socks5 proxy & control port
TOR_PORT = os.getenv('TOR_PORT', '9050')
TOR_CTRL = os.getenv('TOR_CTRL', '9051')

# Tor authentication
TOR_PASS = os.getenv('TOR_PASS')
if TOR_PASS is None:
    TOR_PASS = getpass.getpass('Tor authentication: ')

# Tor bootstrap retry
TOR_RETRY = int(os.getenv('TOR_RETRY', '3'))

# proxy
TOR_REQUESTS_PROXY = {
    # c.f. https://stackoverflow.com/a/42972942
    'http':  f'socks5h://localhost:{TOR_PORT}',
    'https': f'socks5h://localhost:{TOR_PORT}',
}
TOR_SELENIUM_PROXY = selenium.webdriver.Proxy()
TOR_SELENIUM_PROXY.proxyType = selenium.webdriver.common.proxy.ProxyType.MANUAL
TOR_SELENIUM_PROXY.http_proxy = f'socks5://localhost:{TOR_PORT}'
TOR_SELENIUM_PROXY.ssl_proxy = f'socks5://localhost:{TOR_PORT}'

# use stem to manage Tor?
_MNG_TOR = bool(int(os.getenv('DARC_TOR', '1')))

# Tor bootstrapped flag
_TOR_BS_FLAG = not _MNG_TOR  # only if Tor managed through stem
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

if DEBUG:
    print(stem.util.term.format('-*- TOR PROXY -*-',
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    print(render_error(pprint.pformat(_TOR_CONFIG), stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    print(stem.util.term.format('-' * shutil.get_terminal_size().columns,
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member


def renew_tor_session() -> None:
    """Renew Tor session."""
    global _TOR_CTRL  # pylint: disable=global-statement

    try:
        # Tor controller process
        if _TOR_CTRL is None:
            _TOR_CTRL = stem.control.Controller.from_port(port=int(TOR_CTRL))
            _TOR_CTRL.authenticate(TOR_PASS)
        _TOR_CTRL.signal(stem.Signal.NEWNYM)  # pylint: disable=no-member
    except Exception as error:
        warning = warnings.formatwarning(str(error), TorRenewFailed, __file__, 88,
                                         '_TOR_CTRL = stem.control.Controller.from_port(port=int(TOR_CTRL))')
        print(render_error(warning, stem.util.term.Color.YELLOW), end='', file=sys.stderr)  # pylint: disable=no-member


def print_bootstrap_lines(line: str) -> None:
    """Print Tor bootstrap lines.

    Args:
        line: Tor bootstrap line.

    """
    if DEBUG:
        print(stem.util.term.format(line, stem.util.term.Color.BLUE))  # pylint: disable=no-member
        return

    if 'Bootstrapped ' in line:
        print(stem.util.term.format(line, stem.util.term.Color.BLUE))  # pylint: disable=no-member


def _tor_bootstrap() -> None:
    """Tor bootstrap.

    The bootstrap configuration is defined as
    :data:`~darc.proxy.tor._TOR_CONFIG`.

    If :data:`~darc.proxy.tor.TOR_PASS` not provided,
    the function will request for it.

    See Also:
        * :func:`darc.proxy.tor.tor_bootstrap`
        * :data:`darc.proxy.tor.BS_WAIT`
        * :data:`darc.proxy.tor.TOR_PASS`
        * :data:`darc.proxy.tor._TOR_BS_FLAG`
        * :data:`darc.proxy.tor._TOR_PROC`
        * :data:`darc.proxy.tor._TOR_CTRL`

    """
    global _TOR_BS_FLAG, _TOR_PROC  # pylint: disable=global-statement

    # launch Tor process
    _TOR_PROC = stem.process.launch_tor_with_config(
        config=_TOR_CONFIG,
        init_msg_handler=print_bootstrap_lines,
        timeout=BS_WAIT,
        take_ownership=True,
    )

    # update flag
    _TOR_BS_FLAG = True


def tor_bootstrap() -> None:
    """Bootstrap wrapper for Tor.

    The function will bootstrap the Tor proxy. It will retry for
    :data:`~darc.proxy.tor.TOR_RETRY` times in case of failure.

    Also, it will **NOT** re-bootstrap the proxy as is guaranteed by
    :data:`~darc.proxy.tor._TOR_BS_FLAG`.

    Warns:
        TorBootstrapFailed: If failed to bootstrap Tor proxy.

    See Also:
        * :func:`darc.proxy.tor._tor_bootstrap`
        * :data:`darc.proxy.tor.TOR_RETRY`
        * :data:`darc.proxy.tor._TOR_BS_FLAG`

    """
    # don't re-bootstrap
    if _TOR_BS_FLAG:
        return

    print(stem.util.term.format('-*- Tor Bootstrap -*-',
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    for _ in range(TOR_RETRY+1):
        try:
            _tor_bootstrap()
            break
        except Exception as error:
            if DEBUG:
                message = '[Error bootstraping Tor proxy]' + os.linesep + traceback.format_exc()
                print(render_error(message, stem.util.term.Color.RED), end='', file=sys.stderr)  # pylint: disable=no-member

            warning = warnings.formatwarning(str(error), TorBootstrapFailed, __file__, 170, 'tor_bootstrap()')
            print(render_error(warning, stem.util.term.Color.YELLOW), end='', file=sys.stderr)  # pylint: disable=no-member
    print(stem.util.term.format('-' * shutil.get_terminal_size().columns,
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
