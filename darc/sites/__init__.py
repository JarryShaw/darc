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
from darc.error import SiteNotFoundWarning
from darc.link import Link

SITEMAP = collections.defaultdict(lambda: 'default', {
    # misc/special links
    '(data)': 'data',
    '(script)': 'script',
    '(bitcoin)': 'bitcoin',
    '(ed2k)': 'ed2k',
    '(magnet)': 'magnet',
    '(mail)': 'mail',
    '(tel)': 'tel',
    '(irc)': 'irc',

    # 'www.sample.com': 'sample',  # darc.sites.sample
})


def register(domain: str, module: str):
    """Register new site map.

    Args:
        domain: Domain name (case insensitive).
        module: Full qualified module name.

    """
    SITEMAP[domain.casefold()] = module


def _get_spec(link: Link) -> typing.ModuleType:
    """Load spec if any.

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
    spec = SITEMAP[link.host.casefold()]
    try:
        try:
            return importlib.import_module(f'darc.sites.{spec}')
        except ImportError:
            return importlib.import_module(spec)
    except ImportError:
        warnings.warn(f'site customisation not found: {spec}', SiteNotFoundWarning)
        return importlib.import_module('darc.sites.default')


def crawler_hook(link: Link, session: typing.Session) -> typing.Response:
    """Customisation as to :mod:`requests` sessions.

    Args:
        link: Link object to be crawled.
        session (requests.Session): Session object with proxy settings.

    Returns:
        requests.Response: The final response object with crawled data.

    See Also:
        * :data:`darc.sites.SITE_MAP`
        * :func:`darc.sites._get_spec`
        * :func:`darc.crawl.crawler`

    """
    spec = _get_spec(link)
    return spec.crawler(session, link)


def loader_hook(link: Link, driver: typing.Driver) -> typing.Driver:
    """Customisation as to :mod:`selenium` drivers.

    Args:
        link: Link object to be loaded.
        driver (selenium.webdriver.Chrome): Web driver object with proxy settings.

    Returns:
        selenium.webdriver.Chrome: The web driver object with loaded data.

    See Also:
        * :data:`darc.sites.SITE_MAP`
        * :func:`darc.sites._get_spec`
        * :func:`darc.crawl.loader`

    """
    spec = _get_spec(link)
    return spec.loader(driver, link)
