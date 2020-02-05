# -*- coding: utf-8 -*-
"""I2P proxy."""

import os
import re
import subprocess
import sys
import urllib.parse
import warnings

import selenium
import stem

import darc.typing as typing
from darc.error import I2PBootstrapFailed, render_error

__all__ = ['I2P_REQUESTS_PROXY', 'I2P_SELENIUM_PROXY']

# I2P port
I2P_PORT = os.getenv('I2P_PORT', '4444')

# I2P bootstrap retry
I2P_RETRY = int(os.getenv('I2P_RETRY', '3'))

# proxy
I2P_REQUESTS_PROXY = {
    # c.f. https://stackoverflow.com/a/42972942
    'http':  f'http://localhost:{I2P_PORT}',
    'https': f'http://localhost:{I2P_PORT}'
}
I2P_SELENIUM_PROXY = selenium.webdriver.Proxy()
I2P_SELENIUM_PROXY.proxyType = selenium.webdriver.common.proxy.ProxyType.MANUAL
I2P_SELENIUM_PROXY.http_proxy = f'http://localhost:{I2P_PORT}'
I2P_SELENIUM_PROXY.ssl_proxy = f'http://localhost:{I2P_PORT}'


# I2P bootstrapped flag
_I2P_BS_FLAG = False
# I2P daemon process
_I2P_PROC = None


def _i2p_bootstrap():
    """I2P bootstrap."""
    global _I2P_BS_FLAG, _I2P_PROC

    # launch I2P process
    _I2P_PROC = subprocess.Popen(
        ['i2prouter', 'start'],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )

    # update flag
    _I2P_BS_FLAG = True


def i2p_bootstrap():
    """Bootstrap wrapper for I2P."""
    # don't re-bootstrap
    if _I2P_BS_FLAG:
        return

    for _ in range(I2P_RETRY+1):
        try:
            _i2p_bootstrap()
            break
        except Exception as error:
            warning = warnings.formatwarning(error, I2PBootstrapFailed, __file__, 65, 'i2p_bootstrap()')
            print(render_error(warning, stem.util.term.Color.YELLOW), end='', file=sys.stderr)  # pylint: disable=no-member


def has_i2p(link_pool: typing.Set[str]) -> bool:
    """Check if contain I2P links."""
    for link in link_pool:
        # <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
        parse = urllib.parse.urlparse(link)
        host = parse.hostname or parse.netloc

        if re.fullmatch(r'.*?\.i2p', host):
            return True
    return False
