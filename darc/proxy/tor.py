# -*- coding: utf-8 -*-
# pylint: disable=ungrouped-imports
"""Tor Proxy
===============

The :mod:`darc.proxy.tor` module contains the auxiliary functions
around managing and processing the Tor proxy.

"""

import getpass
import json
import os
from typing import TYPE_CHECKING

import selenium.webdriver
import selenium.webdriver.common.proxy
import stem.control
import stem.process

from darc.const import DEBUG
from darc.error import TorBootstrapFailed, TorRenewFailed
from darc.logging import DEBUG as LOG_DEBUG
from darc.logging import INFO as LOG_INFO
from darc.logging import VERBOSE as LOG_VERBOSE
from darc.logging import WARNING as LOG_WARNING
from darc.logging import logger

if TYPE_CHECKING:
    from subprocess import Popen  # nosec: B404
    from typing import Optional

    from stem.control import Controller

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
_TOR_CTRL = None  # type: Optional[Controller]
# Tor daemon process
_TOR_PROC = None  # type: Optional[Popen[bytes]]
# Tor bootstrap config
_TOR_CONFIG = {
    'SocksPort': TOR_PORT,
    'ControlPort': TOR_CTRL,
}
_TOR_CONFIG.update(TOR_CFG)
logger.plog(LOG_DEBUG, '-*- TOR PROXY -*-', object=_TOR_CONFIG)


def renew_tor_session() -> None:
    """Renew Tor session."""
    global _TOR_CTRL  # pylint: disable=global-statement

    try:
        # Tor controller process
        if _TOR_CTRL is None:
            _TOR_CTRL = stem.control.Controller.from_port(port=int(TOR_CTRL))
            _TOR_CTRL.authenticate(TOR_PASS)
        _TOR_CTRL.signal(stem.Signal.NEWNYM)  # pylint: disable=no-member
    except Exception:
        logger.pexc(LOG_WARNING, category=TorRenewFailed,
                    line='_TOR_CTRL = stem.control.Controller.from_port(port=int(TOR_CTRL))')


def print_bootstrap_lines(line: str) -> None:
    """Print Tor bootstrap lines.

    Args:
        line: Tor bootstrap line.

    """
    if 'Bootstrapped ' in line:
        level = LOG_DEBUG
    else:
        level = LOG_VERBOSE
    logger.log(level, line)


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

    logger.info('-*- Tor Bootstrap -*-')
    for _ in range(TOR_RETRY+1):
        try:
            _tor_bootstrap()
            break
        except Exception:
            if DEBUG:
                logger.ptb('[Error bootstraping Tor proxy]')
            logger.pexc(LOG_WARNING, category=TorBootstrapFailed, line='tor_bootstrap()')
    logger.pline(LOG_INFO, logger.horizon)
