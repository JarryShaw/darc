# -*- coding: utf-8 -*-
"""Magnet Links
==================

The :mod:`darc.sites.magnet` module is customised to
handle magnet links.

"""

import darc.typing as typing
from darc.error import LinkNoReturn
from darc.link import Link
from darc.proxy.magnet import save_magnet
from darc.sites._abc import BaseSite


class Magnet(BaseSite):
    """Magnet links."""

    @staticmethod
    def crawler(session: typing.Session, link: Link) -> typing.NoReturn:  # pylint: disable=unused-argument
        """Crawler hook for magnet links.

        Args:
            session (:class:`requests.Session`): Session object with proxy settings.
            link: Link object to be crawled.

        Raises:
            LinkNoReturn: This link has no return response.

        """
        save_magnet(link)
        raise LinkNoReturn

    @staticmethod
    def loader(driver: typing.Driver, link: Link) -> typing.NoReturn:  # pylint: disable=unused-argument
        """Not implemented.

        Raises:
            LinkNoReturn: This hook is not implemented.

        """
        raise LinkNoReturn
