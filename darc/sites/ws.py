# -*- coding: utf-8 -*-
# pylint: disable=ungrouped-imports
"""WebSocket Address
=======================

The :mod:`darc.sites.ws` module is customised to
handle WebSocket addresses.

"""

from typing import TYPE_CHECKING

from darc.error import LinkNoReturn
from darc.proxy.ws import save_ws
from darc.sites._abc import BaseSite

if TYPE_CHECKING:
    from typing import NoReturn

    from requests import Session
    from selenium.webdriver import Chrome as Driver

    import darc.link as darc_link  # Link
    from darc._compat import datetime


class WebSocket(BaseSite):
    """WebSocket addresses."""

    @staticmethod
    def crawler(timestamp: 'datetime', session: 'Session', link: 'darc_link.Link') -> 'NoReturn':  # pylint: disable=unused-argument
        """Crawler hook for WebSocket addresses.

        Args:
            timestamp: Timestamp of the worker node reference.
            session (:class:`requests.Session`): Session object with proxy settings.
            link: Link object to be crawled.

        Raises:
            LinkNoReturn: This link has no return response.

        """
        save_ws(link)
        raise LinkNoReturn(link)

    @staticmethod
    def loader(timestamp: 'datetime', driver: 'Driver', link: 'darc_link.Link') -> 'NoReturn':  # pylint: disable=unused-argument
        """Not implemented.

        Raises:
            LinkNoReturn: This hook is not implemented.

        """
        raise LinkNoReturn(link)
