# -*- coding: utf-8 -*-
# pylint: disable=ungrouped-imports
"""ED2K Magnet Links
=======================

The :mod:`darc.sites.ed2k` module is customised to
handle ED2K magnet links.

"""

from typing import TYPE_CHECKING

from darc.error import LinkNoReturn
from darc.proxy.ed2k import save_ed2k
from darc.sites._abc import BaseSite

if TYPE_CHECKING:
    from typing import NoReturn

    from requests import Session
    from selenium.webdriver import Chrome as Driver

    import darc.link as darc_link  # Link
    from darc._compat import datetime


class ED2K(BaseSite):
    """ED2K magnet links."""

    @staticmethod
    def crawler(timestamp: 'datetime', session: 'Session', link: 'darc_link.Link') -> 'NoReturn':  # pylint: disable=unused-argument
        """Crawler hook for ED2K magnet links.

        Args:
            timestamp: Timestamp of the worker node reference.
            session (:class:`requests.Session`): Session object with proxy settings.
            link: Link object to be crawled.

        Raises:
            LinkNoReturn: This link has no return response.

        """
        save_ed2k(link)
        raise LinkNoReturn(link)

    @staticmethod
    def loader(timestamp: 'datetime', driver: 'Driver', link: 'darc_link.Link') -> 'NoReturn':  # pylint: disable=unused-argument
        """Not implemented.

        Raises:
            LinkNoReturn: This hook is not implemented.

        """
        raise LinkNoReturn(link)
