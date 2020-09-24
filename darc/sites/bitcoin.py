# -*- coding: utf-8 -*-
"""Bitcoin Addresses
=======================

The :mod:`darc.sites.bitcoin` module is customised to
handle bitcoin addresses.

"""

import darc.typing as typing
from darc.error import LinkNoReturn
from darc.link import Link
from darc.proxy.bitcoin import save_bitcoin
from darc.sites._abc import BaseSite


class Bitcoin(BaseSite):
    """Bitcoin addresses."""

    @staticmethod
    def crawler(session: typing.Session, link: Link) -> typing.NoReturn:  # pylint: disable=unused-argument
        """Crawler hook for bitcoin addresses.

        Args:
            session (:class:`requests.Session`): Session object with proxy settings.
            link: Link object to be crawled.

        Raises:
            LinkNoReturn: This link has no return response.

        """
        save_bitcoin(link)
        raise LinkNoReturn

    @staticmethod
    def loader(driver: typing.Driver, link: Link) -> typing.NoReturn:  # pylint: disable=unused-argument
        """Not implemented.

        Raises:
            LinkNoReturn: This hook is not implemented.

        """
        raise LinkNoReturn
