# -*- coding: utf-8 -*-
"""Selenium wrapper."""

import getpass
import platform
import shutil

import selenium

import darc.typing as typing
from darc.const import DEBUG
from darc.error import UnsupportedPlatform, UnsupportedProxy
from darc.proxy.i2p import I2P_PORT, I2P_SELENIUM_PROXY
from darc.proxy.tor import TOR_PORT, TOR_SELENIUM_PROXY


def get_options(type: str = 'norm') -> typing.Options:  # pylint: disable=redefined-builtin
    """Generate options."""
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

    if type != 'norm':
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


def get_capabilities(type: str = 'norm') -> dict:  # pylint: disable=redefined-builtin
    """Generate desied capabilities."""
    # do not modify source dict
    capabilities = selenium.webdriver.DesiredCapabilities.CHROME.copy()

    if type == 'norm':
        pass
    elif type == 'tor':
        TOR_SELENIUM_PROXY.add_to_capabilities(capabilities)
    elif type == 'i2p':
        I2P_SELENIUM_PROXY.add_to_capabilities(capabilities)
    else:
        raise UnsupportedProxy(f'unsupported proxy: {type}')
    return capabilities


def i2p_driver() -> typing.Driver:
    """I2P (.i2p) driver."""
    options = get_options('i2p')
    capabilities = get_capabilities('i2p')

    # initiate driver
    driver = selenium.webdriver.Chrome(options=options,
                                       desired_capabilities=capabilities)
    return driver


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
