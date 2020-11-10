# -*- coding: utf-8 -*-
"""Telephone Numbers
=======================

The :mod:`darc.sites.tel` module is customised to
handle telephone numbers.

"""

import darc.typing as typing
from darc.error import LinkNoReturn
from darc.link import Link
from darc.proxy.tel import save_tel
from darc.sites._abc import BaseSite


class Tel(BaseSite):
    """Telephone numbers."""

    @staticmethod
    def crawler(timestamp: typing.Datetime, session: typing.Session, link: Link) -> typing.NoReturn:  # pylint: disable=unused-argument
        """Crawler hook for telephone numbers.

        Args:
            timestamp: Timestamp of the worker node reference.
            session (:class:`requests.Session`): Session object with proxy settings.
            link: Link object to be crawled.

        Raises:
            LinkNoReturn: This link has no return response.

        """
        save_tel(link)
        raise LinkNoReturn(link)

    @staticmethod
    def loader(timestamp: typing.Datetime, driver: typing.Driver, link: Link) -> typing.NoReturn:  # pylint: disable=unused-argument
        """Not implemented.

        Raises:
            LinkNoReturn: This hook is not implemented.

        """
        raise LinkNoReturn(link)
