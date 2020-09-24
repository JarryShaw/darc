# -*- coding: utf-8 -*-
"""ED2K Magnet Links
=======================

The :mod:`darc.sites.ed2k` module is customised to
handle ED2K magnet links.

"""

import darc.typing as typing
from darc.error import LinkNoReturn
from darc.link import Link
from darc.proxy.ed2k import save_ed2k
from darc.sites._abc import BaseSite


class ED2K(BaseSite):
    """ED2K magnet links."""

    @staticmethod
    def crawler(session: typing.Session, link: Link) -> typing.NoReturn:  # pylint: disable=unused-argument
        """Crawler hook for ED2K magnet links.

        Args:
            session (:class:`requests.Session`): Session object with proxy settings.
            link: Link object to be crawled.

        Raises:
            LinkNoReturn: This link has no return response.

        """
        save_ed2k(link)
        raise LinkNoReturn

    @staticmethod
    def loader(driver: typing.Driver, link: Link) -> typing.NoReturn:  # pylint: disable=unused-argument
        """Not implemented.

        Raises:
            LinkNoReturn: This hook is not implemented.

        """
        raise LinkNoReturn
