# -*- coding: utf-8 -*-
"""Selenium Wrapper
======================

The :mod:`darc.selenium` module wraps around the :mod:`selenium`
module, and provides some simple interface for the :mod:`darc`
project.

"""

import getpass
import os
import platform
import shutil

import selenium.webdriver

import darc.typing as typing
from darc.const import DEBUG
from darc.error import UnsupportedLink, UnsupportedPlatform, UnsupportedProxy
from darc.link import Link
from darc.proxy.i2p import I2P_PORT, I2P_SELENIUM_PROXY
from darc.proxy.tor import TOR_PORT, TOR_SELENIUM_PROXY

# Google Chrome binary location.
BINARY_LOCATION = os.getenv('CHROME_BINARY_LOCATION')
if BINARY_LOCATION is None:
    _system = platform.system()

    if _system == 'Darwin':
        BINARY_LOCATION = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    elif _system == 'Linux':
        BINARY_LOCATION = shutil.which('google-chrome')
    del _system


def request_driver(link: Link) -> typing.Driver:
    """Get selenium driver.

    Args:
        link: Link requesting for :class:`~selenium.webdriver.Chrome`.

    Returns:
        selenium.webdriver.Chrome: The web driver object with corresponding proxy settings.

    Raises:
        UnsupportedLink: If the proxy type of ``link``
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
        selenium.webdriver.ChromeOptions: The options for the web driver :class:`~selenium.webdriver.Chrome`.

    Raises:
        UnsupportedPlatform: If the operation system is **NOT**
            macOS or Linux and :envvar:`CHROME_BINARY_LOCATION`
            is **NOT** set.
        UnsupportedProxy: If the proxy type is **NOT**
            ``null``, ``tor`` or ``i2p``.

    Important:
        The function raises :exc:`UnsupportedPlatform` in cases where
        :data:`~darc.selenium.BINARY_LOCATION` is :data:`None`.

        Please provide :envvar:`CHROME_BINARY_LOCATION` when running
        :mod:`darc` in ``loader`` mode on non *macOS* and/or *Linux*
        systems.

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
    if BINARY_LOCATION is None:
        raise UnsupportedPlatform(f'unsupported system: {_system}')
    options.binary_location = BINARY_LOCATION

    # https://peter.sh/experiments/chromium-command-line-switches/
    if not DEBUG:
        options.add_argument('--headless')
    if _system == 'Linux':
        if os.path.isfile('/.dockerenv'):  # check if in Docker
            options.headless = True  # force headless option in Docker environment

        # c.f. https://crbug.com/638180; https://stackoverflow.com/a/50642913/7218152
        if getpass.getuser() == 'root':
            options.add_argument('--no-sandbox')

        # c.f. http://crbug.com/715363
        options.add_argument('--disable-dev-shm-usage')

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
        The desied capabilities for the web driver :class:`~selenium.webdriver.Chrome`.

    Raises:
        UnsupportedProxy: If the proxy type is **NOT**
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
    """I2P (``.i2p``) driver.

    Returns:
        selenium.webdriver.Chrome: The web driver object with I2P proxy settings.

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
    """Tor (``.onion``) driver.

    Returns:
        selenium.webdriver.Chrome: The web driver object with Tor proxy settings.

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
        selenium.webdriver.Chrome: The web driver object with no proxy settings.

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
