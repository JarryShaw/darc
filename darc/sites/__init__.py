# -*- coding: utf-8 -*-
"""Site specific customisation."""

import importlib
import warnings

import darc.typing as typing
from darc.error import SiteNotFoundWarning
from darc.link import Link

SITEMAP = {
    # 'www.sample.com': 'sample',  # darc.sites.sample
}


def _get_spec(link: Link) -> typing.ModuleType:
    """Load spec if any."""
    spec = SITEMAP.get(link.host, 'default')
    try:
        return importlib.import_module(f'darc.sites.{spec}')
    except ImportError:
        warnings.warn(f'site customisation not found: {spec}', SiteNotFoundWarning)
        return importlib.import_module(f'darc.sites.default')


def crawler_hook(link: Link, session: typing.Session) -> typing.Response:
    """Customisation as to requests sessions."""
    spec = _get_spec(link)
    return spec.crawler(session, link)


def loader_hook(link: Link, driver: typing.Driver) -> typing.Driver:
    """Customisation as to selenium drivers."""
    spec = _get_spec(link)
    return spec.loader(driver, link)
