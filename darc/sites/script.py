# -*- coding: utf-8 -*-
"""JavaScript Links
======================

The :mod:`darc.sites.script` module is customised to
handle JavaScript links.

"""

import darc.typing as typing
from darc.error import LinkNoReturn
from darc.link import Link
from darc.proxy.script import save_script
from darc.sites._abc import BaseSite


class Script(BaseSite):
    """JavaScript links."""

    @staticmethod
    def crawler(timestamp: typing.Datetime, session: typing.Session, link: Link) -> typing.NoReturn:  # pylint: disable=unused-argument
        """Crawler hook for JavaScript links.

        Args:
            timestamp: Timestamp of the worker node reference.
            session (:class:`requests.Session`): Session object with proxy settings.
            link: Link object to be crawled.

        Raises:
            LinkNoReturn: This link has no return response.

        """
        save_script(link)
        raise LinkNoReturn(link)

    @staticmethod
    def loader(timestamp: typing.Datetime, driver: typing.Driver, link: Link) -> typing.NoReturn:  # pylint: disable=unused-argument
        """Not implemented.

        Raises:
            LinkNoReturn: This hook is not implemented.

        """
        raise LinkNoReturn(link)
