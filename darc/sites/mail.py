# -*- coding: utf-8 -*-
# pylint: disable=ungrouped-imports
"""Email Addresses
=====================

The :mod:`darc.sites.mail` module is customised to
handle email addresses.

"""

from typing import TYPE_CHECKING

from darc.error import LinkNoReturn
from darc.proxy.mail import save_mail
from darc.sites._abc import BaseSite

if TYPE_CHECKING:
    from typing import NoReturn

    from requests import Session
    from selenium.webdriver import Chrome as Driver

    import darc.link as darc_link  # Link
    from darc._compat import datetime


class Email(BaseSite):
    """Email addresses."""

    @staticmethod
    def crawler(timestamp: 'datetime', session: 'Session', link: 'darc_link.Link') -> 'NoReturn':  # pylint: disable=unused-argument
        """Crawler hook for email addresses.

        Args:
            timestamp: Timestamp of the worker node reference.
            session (:class:`requests.Session`): Session object with proxy settings.
            link: Link object to be crawled.

        Raises:
            LinkNoReturn: This link has no return response.

        """
        save_mail(link)
        raise LinkNoReturn(link)

    @staticmethod
    def loader(timestamp: 'datetime', driver: 'Driver', link: 'darc_link.Link') -> 'NoReturn':  # pylint: disable=unused-argument
        """Not implemented.

        Raises:
            LinkNoReturn: This hook is not implemented.

        """
        raise LinkNoReturn(link)
