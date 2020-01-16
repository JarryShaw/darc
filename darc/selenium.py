# -*- coding: utf-8 -*-
"""Selenium wrapper."""

import getpass
import platform
import shutil

import selenium

import darc.typing as typing
from darc.const import DEBUG, TOR_PORT
from darc.error import UnsupportedPlatform


def get_options(type: str = 'norm') -> typing.Options:  # pylint: disable=redefined-builtin
    """Generate options."""
    _system = platform.system()

    # initiate options
    options = selenium.webdriver.ChromeOptions()

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

    if type == 'tor':
        # c.f. https://www.chromium.org/developers/design-documents/network-stack/socks-proxy
        options.add_argument(f'--proxy-server=socks5://localhost:{TOR_PORT}')
        options.add_argument('--host-resolver-rules="MAP * ~NOTFOUND , EXCLUDE localhost"')
    return options


def get_capabilities(type: str = 'norm') -> dict:  # pylint: disable=redefined-builtin
    """Generate desied capabilities."""
    # do not modify source dict
    capabilities = selenium.webdriver.DesiredCapabilities.CHROME.copy()

    if type == 'tor':
        proxy = selenium.webdriver.Proxy()
        proxy.proxyType = selenium.webdriver.common.proxy.ProxyType.MANUAL
        proxy.http_proxy = f'socks5://localhost:{TOR_PORT}'
        proxy.ssl_proxy = f'socks5://localhost:{TOR_PORT}'
        proxy.add_to_capabilities(capabilities)
    return capabilities


def tor_driver() -> typing.Driver:
    """Tor (.onion) driver."""
    options = get_options('tor')
    capabilities = get_capabilities('tor')

    # initiate driver
    driver = selenium.webdriver.Chrome(options=options,
                                       desired_capabilities=capabilities)
    return driver


def norm_driver() -> typing.Driver:
    """Normal driver."""
    options = get_options('norm')
    capabilities = get_capabilities('norm')

    # initiate driver
    driver = selenium.webdriver.Chrome(options=options,
                                       desired_capabilities=capabilities)
    return driver
