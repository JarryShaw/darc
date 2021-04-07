# -*- coding: utf-8 -*-
# pylint: disable=ungrouped-imports
"""Sites Customisation
=========================

As websites may have authentication requirements, etc., over
its content, the :mod:`darc.sites` module provides site
customisation hooks to both :mod:`requests` and :mod:`selenium`
crawling processes.

Important:
    To create a sites customisation, define your class by inheriting
    :class:`darc.sites.BaseSite` and register it to the :mod:`darc`
    module through :func:`darc.sites.register`.

"""

import collections
import warnings
from typing import TYPE_CHECKING, cast

from darc.error import SiteNotFoundWarning
from darc.sites._abc import BaseSite
from darc.sites.bitcoin import Bitcoin
from darc.sites.data import DataURI
from darc.sites.default import DefaultSite
from darc.sites.ed2k import ED2K
from darc.sites.ethereum import Ethereum
from darc.sites.irc import IRC
from darc.sites.magnet import Magnet
from darc.sites.mail import Email
from darc.sites.script import Script
from darc.sites.tel import Tel
from darc.sites.ws import WebSocket

if TYPE_CHECKING:
    from typing import DefaultDict, List, Type

    from requests import Response, Session
    from selenium.webdriver import Chrome as Driver

    import darc.link as darc_link  # Link
    from darc._compat import datetime


SITEMAP = collections.defaultdict(lambda: DefaultSite, {
    # misc/special links
    '(data)': DataURI,
    '(script)': Script,
    '(bitcoin)': Bitcoin,
    '(ed2k)': ED2K,
    '(magnet)': Magnet,
    '(mail)': Email,
    '(tel)': Tel,
    '(irc)': IRC,
    '(ws)': WebSocket,
    '(ethereum)': Ethereum,
})  # type: DefaultDict[str, Type[BaseSite]]


def register(site: 'Type[BaseSite]', *hostname: str) -> None:
    """Register new site map.

    Args:
        site: Sites customisation class inherited from
            :class:`~darc.sites._abc.BaseSite`.
        *hostname (Tuple[str]): Optional list of hostnames the sites
            customisation should be registered with.
            By default, we use :attr:`site.hostname`.

    """
    if site.hostname is None:
        site.hostname = cast('List[str]', hostname)

    for domain in hostname:
        SITEMAP[domain.casefold()] = site


def _get_site(link: 'darc_link.Link') -> 'Type[BaseSite]':
    """Load sites customisation if any.

    If the sites customisation does not exist, it will
    fallback to the default hooks, :class:`~darc.sites.default.DefaultSite`.

    Args:
        link: Link object to fetch sites customisation class.

    Returns:
        The sites customisation class.

    See Also:
        * :data:`darc.sites.SITEMAP`

    """
    host = (link.host or '<null>').casefold()
    site = SITEMAP.get(host)
    if site is None:
        site = DefaultSite

        warnings.warn(f'sites customisation not found: {host}', SiteNotFoundWarning)
        SITEMAP[host] = site  # set for cache
    return site


def crawler_hook(timestamp: 'datetime', session: 'Session', link: 'darc_link.Link') -> 'Response':
    """Customisation as to :mod:`requests` sessions.

    Args:
        timestamp: Timestamp of the worker node reference.
        session (requests.Session): Session object with proxy settings.
        link: Link object to be crawled.

    Returns:
        requests.Response: The final response object with crawled data.

    See Also:
        * :data:`darc.sites.SITE_MAP`
        * :func:`darc.sites._get_site`
        * :func:`darc.crawl.crawler`

    """
    site = _get_site(link)
    return site.crawler(timestamp, session, link)


def loader_hook(timestamp: 'datetime', driver: 'Driver', link: 'darc_link.Link') -> 'Driver':
    """Customisation as to :mod:`selenium` drivers.

    Args:
        timestamp: Timestamp of the worker node reference.
        driver (selenium.webdriver.Chrome): Web driver object with proxy settings.
        link: Link object to be loaded.

    Returns:
        selenium.webdriver.Chrome: The web driver object with loaded data.

    See Also:
        * :data:`darc.sites.SITE_MAP`
        * :func:`darc.sites._get_site`
        * :func:`darc.crawl.loader`

    """
    site = _get_site(link)
    return site.loader(timestamp, driver, link)
