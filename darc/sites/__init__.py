# -*- coding: utf-8 -*-
"""Sites Customisation
=========================

As websites may have authentication requirements, etc., over
its content, the :mod:`darc.sites` module provides site
customisation hooks to both |requests|_ and |selenium|_
crawling processes.

"""

import collections

import importlib
import warnings

import darc.typing as typing
from darc.error import SiteNotFoundWarning
from darc.link import Link

SITEMAP = collections.defaultdict(lambda: 'default', {
    # 'www.sample.com': 'sample',  # darc.sites.sample
})


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
        return importlib.import_module(f'darc.sites.{spec}')
    except ImportError:
        warnings.warn(f'site customisation not found: {spec}', SiteNotFoundWarning)
        return importlib.import_module(f'darc.sites.default')


def crawler_hook(link: Link, session: typing.Session) -> typing.Response:
    """Customisation as to |requests|_ sessions.

    Args:
        link: Link object to be crawled.
        session (|Session|_): Session object with proxy settings.

    Returns:
        |Response|_: The final response object with crawled data.

    See Also:
        * :data:`darc.sites.SITE_MAP`
        * :func:`darc.sites._get_spec`
        * :func:`darc.crawl.crawler`

    """
    spec = _get_spec(link)
    return spec.crawler(session, link)


def loader_hook(link: Link, driver: typing.Driver) -> typing.Driver:
    """Customisation as to |selenium|_ drivers.

    Args:
        link: Link object to be loaded.
        driver (|Chrome|_): Web driver object with proxy settings.

    Returns:
        |Chrome|_: The web driver object with loaded data.

    See Also:
        * :data:`darc.sites.SITE_MAP`
        * :func:`darc.sites._get_spec`
        * :func:`darc.crawl.loader`

    """
    spec = _get_spec(link)
    return spec.loader(driver, link)
