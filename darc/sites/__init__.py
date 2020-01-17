# -*- coding: utf-8 -*-
"""Site specific customisation."""

import importlib

import darc.typing as typing
from darc.link import Link

SITEMAP = {
    # 'www.sample.com': 'sample',  # darc.sites.sample
}


def _get_spec(link: Link) -> typing.ModuleType:
    """Load spec if any."""
    spec = SITEMAP.get(link.host, 'default')
    return importlib.import_module(f'darc.sites.{spec}')


def crawler_hook(link: Link, session: typing.Session) -> typing.Response:
    """Customisation as to requests sessions."""
    spec = _get_spec(link)
    return spec.crawler(session, link)


def loader_hook(link: Link, driver: typing.Driver) -> typing.Driver:
    """Customisation as to selenium drivers."""
    spec = _get_spec(link)
    return spec.loader(driver, link)
