# -*- coding: utf-8 -*-
# pylint: disable=ungrouped-imports
"""Data URI Schemes
======================

The :mod:`darc.sites.data` module is customised to
handle data URI schemes.

"""

import sys
from typing import TYPE_CHECKING

import stem.util.term as stem_term

from darc.error import LinkNoReturn, render_error
from darc.proxy.data import save_data
from darc.sites._abc import BaseSite

if TYPE_CHECKING:
    from typing import NoReturn

    from requests import Session
    from selenium.webdriver import Chrome as Driver

    import darc.link as darc_link  # Link
    from darc._compat import datetime


class DataURI(BaseSite):
    """Data URI schemes."""

    @staticmethod
    def crawler(timestamp: 'datetime', session: 'Session', link: 'darc_link.Link') -> 'NoReturn':  # pylint: disable=unused-argument
        """Crawler hook for data URIs.

        Args:
            timestamp: Timestamp of the worker node reference.
            session (:class:`requests.Session`): Session object with proxy settings.
            link: Link object to be crawled.

        Raises:
            LinkNoReturn: This link has no return response.

        """
        try:
            save_data(link)
        except ValueError as error:
            print(render_error(f'[REQUESTS] Failed to save data URI from {link.url} <{error}>',
                               stem_term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
        raise LinkNoReturn(link)

    @staticmethod
    def loader(timestamp: 'datetime', driver: 'Driver', link: 'darc_link.Link') -> 'NoReturn':  # pylint: disable=unused-argument
        """Not implemented.

        Raises:
            LinkNoReturn: This hook is not implemented.

        """
        raise LinkNoReturn(link)
