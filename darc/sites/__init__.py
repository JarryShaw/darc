# -*- coding: utf-8 -*-
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

import darc.typing as typing
from darc.error import SiteNotFoundWarning
from darc.link import Link
from darc.sites._abc import BaseSite
from darc.sites.bitcoin import Bitcoin
from darc.sites.data import DataURI
from darc.sites.default import DefaultSite
from darc.sites.ed2k import ED2K
from darc.sites.irc import IRC
from darc.sites.magnet import Magnet
from darc.sites.mail import Email
from darc.sites.script import Script
from darc.sites.tel import Tel
from darc.sites.ws import WebSocket

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
})  # type: typing.DefaultDict[str, typing.Type[BaseSite]]


def register(site: typing.Type[BaseSite], *hostname) -> None:  # type: ignore
    """Register new site map.

    Args:
        site: Sites customisation class inherited from
            :class:`~darc.sites._abc.BaseSite`.
        *hostname (Tuple[str]): Optional list of hostnames the sites
            customisation should be registered with.
            By default, we use :attr:`site.hostname`.

    """
    if site.hostname is None:
        site.hostname = hostname   # type: ignore

    for domain in hostname:
        SITEMAP[domain.casefold()] = site


def _get_site(link: Link) -> typing.Type[BaseSite]:
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
    host = link.host.casefold()
    site = SITEMAP.get(host)
    if site is None:
        site = DefaultSite

        warnings.warn(f'sites customisation not found: {host}', SiteNotFoundWarning)
        SITEMAP[host] = site  # set for cache
    return site


def crawler_hook(link: Link, session: typing.Session) -> typing.Response:
    """Customisation as to :mod:`requests` sessions.

    Args:
        link: Link object to be crawled.
        session (requests.Session): Session object with proxy settings.

    Returns:
        requests.Response: The final response object with crawled data.

    See Also:
        * :data:`darc.sites.SITE_MAP`
        * :func:`darc.sites._get_site`
        * :func:`darc.crawl.crawler`

    """
    site = _get_site(link)
    return site.crawler(session, link)


def loader_hook(link: Link, driver: typing.Driver) -> typing.Driver:
    """Customisation as to :mod:`selenium` drivers.

    Args:
        link: Link object to be loaded.
        driver (selenium.webdriver.Chrome): Web driver object with proxy settings.

    Returns:
        selenium.webdriver.Chrome: The web driver object with loaded data.

    See Also:
        * :data:`darc.sites.SITE_MAP`
        * :func:`darc.sites._get_site`
        * :func:`darc.crawl.loader`

    """
    site = _get_site(link)
    return site.loader(driver, link)
