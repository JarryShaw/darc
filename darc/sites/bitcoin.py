# -*- coding: utf-8 -*-
# pylint: disable=ungrouped-imports
"""Bitcoin Addresses
=======================

The :mod:`darc.sites.bitcoin` module is customised to
handle bitcoin addresses.

"""

from typing import TYPE_CHECKING

from darc.error import LinkNoReturn
from darc.proxy.bitcoin import save_bitcoin
from darc.sites._abc import BaseSite

if TYPE_CHECKING:
    from typing import NoReturn

    from requests import Session
    from selenium.webdriver import Chrome as Driver

    from darc._compat import datetime
    from darc.link import Link


class Bitcoin(BaseSite):
    """Bitcoin addresses."""

    @staticmethod
    def crawler(timestamp: 'datetime', session: 'Session', link: 'Link') -> 'NoReturn':  # pylint: disable=unused-argument
        """Crawler hook for bitcoin addresses.

        Args:
            timestamp: Timestamp of the worker node reference.
            session (:class:`requests.Session`): Session object with proxy settings.
            link: Link object to be crawled.

        Raises:
            LinkNoReturn: This link has no return response.

        """
        save_bitcoin(link)
        raise LinkNoReturn(link)

    @staticmethod
    def loader(timestamp: 'datetime', driver: 'Driver', link: 'Link') -> 'NoReturn':  # pylint: disable=unused-argument
        """Not implemented.

        Raises:
            LinkNoReturn: This hook is not implemented.

        """
        raise LinkNoReturn(link)
