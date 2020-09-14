# -*- coding: utf-8 -*-
"""Sites Customisation
=========================

As websites may have authentication requirements, etc., over
its content, the :mod:`darc.sites` module provides site
customisation hooks to both :mod:`requests` and :mod:`selenium`
crawling processes.

"""

import collections

import importlib
import warnings

import darc.typing as typing
import darc.sites.default as default  # import as cache
from darc.error import SiteNotFoundWarning
from darc.link import Link

SITEMAP = collections.defaultdict(lambda: default, {
    # misc/special links
    '(data)': 'darc.sites.data',
    '(script)': 'darc.sites.script',
    '(bitcoin)': 'darc.sites.bitcoin',
    '(ed2k)': 'darc.sites.ed2k',
    '(magnet)': 'darc.sites.magnet',
    '(mail)': 'darc.sites.mail',
    '(tel)': 'darc.sites.tel',
    '(irc)': 'darc.sites.irc',

    # 'www.sample.com': 'sample',  # local customised module
})  # type: typing.DefaultDict[str, typing.Union[str, typing.ModuleType]]


def register(domain: str, module: typing.Union[str, typing.ModuleType]):
    """Register new site map.

    Args:
        domain: Domain name (case insensitive).
        module: Full qualified module name.

    Raises:
        ImportError: If failed to import the specified module name.

    """
    if isinstance(module, str):
        module = importlib.import_module(module)
    SITEMAP[domain.casefold()] = module


def _get_module(link: Link) -> typing.ModuleType:
    """Load module if any.

    If the sites customisation failed to import, it will
    fallback to the default hooks, :mod:`~darc.sites.default`.

    Args:
        link: Link object to fetch sites customisation module.

    Returns:
        types.ModuleType: The sites customisation module.

    Warns:
        SiteNotFoundWarning: If the sites customisation failed to import.

    See Also:
        * :data:`darc.sites.SITEMAP`

    """
    domain = link.host.casefold()
    module = SITEMAP[domain]
    if isinstance(module, str):
        try:
            module = importlib.import_module(module)
        except ImportError:
            warnings.warn(f'site customisation not found: {module}', SiteNotFoundWarning)
            module = default
        SITEMAP[domain] = module  # set for cache
    return module


def crawler_hook(link: Link, session: typing.Session) -> typing.Response:
    """Customisation as to :mod:`requests` sessions.

    Args:
        link: Link object to be crawled.
        session (requests.Session): Session object with proxy settings.

    Returns:
        requests.Response: The final response object with crawled data.

    See Also:
        * :data:`darc.sites.SITE_MAP`
        * :func:`darc.sites._get_module`
        * :func:`darc.crawl.crawler`

    """
    module = _get_module(link)
    return module.crawler(session, link)  # type: ignore


def loader_hook(link: Link, driver: typing.Driver) -> typing.Driver:
    """Customisation as to :mod:`selenium` drivers.

    Args:
        link: Link object to be loaded.
        driver (selenium.webdriver.Chrome): Web driver object with proxy settings.

    Returns:
        selenium.webdriver.Chrome: The web driver object with loaded data.

    See Also:
        * :data:`darc.sites.SITE_MAP`
        * :func:`darc.sites._get_module`
        * :func:`darc.crawl.loader`

    """
    module = _get_module(link)
    return module.loader(driver, link)  # type: ignore
