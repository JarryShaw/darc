# -*- coding: utf-8 -*-
"""Selenium Wrapper
======================

The :mod:`darc.selenium` module wraps around the |selenium|_
module, and provides some simple interface for the :mod:`darc`
project.

"""

import getpass
import platform
import shutil

import selenium

import darc.typing as typing
from darc.const import DEBUG
from darc.error import UnsupportedLink, UnsupportedPlatform, UnsupportedProxy
from darc.link import Link
from darc.proxy.i2p import I2P_PORT, I2P_SELENIUM_PROXY
from darc.proxy.tor import TOR_PORT, TOR_SELENIUM_PROXY


def request_driver(link: Link) -> typing.Driver:
    """Get selenium driver.

    Args:
        link: Link requesting for |Chrome|_.

    Returns:
        |Chrome|_: The web driver object with corresponding proxy settings.

    Raises:
        :exc:`UnsupportedLink`: If the proxy type of ``link``
            if not specified in the :data:`~darc.proxy.LINK_MAP`.

    See Also:
        * :data:`darc.proxy.LINK_MAP`

    """
    from darc.proxy import LINK_MAP  # pylint: disable=import-outside-toplevel

    _, driver = LINK_MAP[link.proxy]
    if driver is None:
        raise UnsupportedLink(link.url)
    return driver()


def get_options(type: str = 'null') -> typing.Options:  # pylint: disable=redefined-builtin
    """Generate options.

    Args:
        type: Proxy type for options.

    Returns:
        |Options|_: The options for the web driver |Chrome|_.

    Raises:
        :exc:`UnsupportedPlatform`: If the operation system is **NOT**
            macOS or Linux.
        :exc:`UnsupportedProxy`: If the proxy type is **NOT**
            ``null``, ``tor`` or ``i2p``.

    See Also:
        * :data:`darc.proxy.tor.TOR_PORT`
        * :data:`darc.proxy.i2p.I2P_PORT`

    References:
        * `Google Chrome command line switches <https://peter.sh/experiments/chromium-command-line-switches/>`__
        * Disable sandbox (``--no-sandbox``) when running as ``root`` user

          - https://crbug.com/638180
          - https://stackoverflow.com/a/50642913/7218152

        * Disable usage of ``/dev/shm``

          - http://crbug.com/715363

        * `Using Socks proxy <https://www.chromium.org/developers/design-documents/network-stack/socks-proxy>`__

    """
    _system = platform.system()

    # initiate options
    options = selenium.webdriver.ChromeOptions()

    # https://peter.sh/experiments/chromium-command-line-switches/
    if _system == 'Darwin':
        options.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

        if not DEBUG:
            options.add_argument('--headless')
    elif _system == 'Linux':
        options.binary_location = shutil.which('google-chrome')
        options.add_argument('--headless')

        # c.f. https://crbug.com/638180; https://stackoverflow.com/a/50642913/7218152
        if getpass.getuser() == 'root':
            options.add_argument('--no-sandbox')

        # c.f. http://crbug.com/715363
        options.add_argument('--disable-dev-shm-usage')
    else:
        raise UnsupportedPlatform(f'unsupported system: {_system}')

    if type != 'null':
        if type == 'tor':
            port = TOR_PORT
        elif type == 'i2p':
            port = I2P_PORT
        else:
            raise UnsupportedProxy(f'unsupported proxy: {type}')

        # c.f. https://www.chromium.org/developers/design-documents/network-stack/socks-proxy
        options.add_argument(f'--proxy-server=socks5://localhost:{port}')
        options.add_argument('--host-resolver-rules="MAP * ~NOTFOUND , EXCLUDE localhost"')
    return options


def get_capabilities(type: str = 'null') -> dict:  # pylint: disable=redefined-builtin
    """Generate desied capabilities.

    Args:
        type: Proxy type for capabilities.

    Returns:
        The desied capabilities for the web driver |Chrome|_.

    Raises:
        :exc:`UnsupportedProxy`: If the proxy type is **NOT**
            ``null``, ``tor`` or ``i2p``.

    See Also:
        * :data:`darc.proxy.tor.TOR_SELENIUM_PROXY`
        * :data:`darc.proxy.i2p.I2P_SELENIUM_PROXY`

    """
    # do not modify source dict
    capabilities = selenium.webdriver.DesiredCapabilities.CHROME.copy()

    if type == 'null':
        pass
    elif type == 'tor':
        TOR_SELENIUM_PROXY.add_to_capabilities(capabilities)
    elif type == 'i2p':
        I2P_SELENIUM_PROXY.add_to_capabilities(capabilities)
    else:
        raise UnsupportedProxy(f'unsupported proxy: {type}')
    return capabilities


def i2p_driver() -> typing.Driver:
    """I2P (.i2p) driver.

    Returns:
        |Chrome|_: The web driver object with I2P proxy settings.

    See Also:
        * :func:`darc.selenium.get_options`
        * :func:`darc.selenium.get_capabilities`

    """
    options = get_options('i2p')
    capabilities = get_capabilities('i2p')

    # initiate driver
    driver = selenium.webdriver.Chrome(options=options,
                                       desired_capabilities=capabilities)
    return driver


def tor_driver() -> typing.Driver:
    """Tor (.onion) driver.

    Returns:
        |Chrome|_: The web driver object with Tor proxy settings.

    See Also:
        * :func:`darc.selenium.get_options`
        * :func:`darc.selenium.get_capabilities`

    """
    options = get_options('tor')
    capabilities = get_capabilities('tor')

    # initiate driver
    driver = selenium.webdriver.Chrome(options=options,
                                       desired_capabilities=capabilities)
    return driver


def null_driver() -> typing.Driver:
    """No proxy driver.

    Returns:
        |Chrome|_: The web driver object with no proxy settings.

    See Also:
        * :func:`darc.selenium.get_options`
        * :func:`darc.selenium.get_capabilities`

    """
    options = get_options('null')
    capabilities = get_capabilities('null')

    # initiate driver
    driver = selenium.webdriver.Chrome(options=options,
                                       desired_capabilities=capabilities)
    return driver
