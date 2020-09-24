# -*- coding: utf-8 -*-
"""Email Addresses
=====================

The :mod:`darc.sites.mail` module is customised to
handle email addresses.

"""

import darc.typing as typing
from darc.error import LinkNoReturn
from darc.link import Link
from darc.proxy.mail import save_mail
from darc.sites._abc import BaseSite


class Email(BaseSite):
    """Email addresses."""

    @staticmethod
    def crawler(session: typing.Session, link: Link) -> typing.NoReturn:  # pylint: disable=unused-argument
        """Crawler hook for email addresses.

        Args:
            session (:class:`requests.Session`): Session object with proxy settings.
            link: Link object to be crawled.

        Raises:
            LinkNoReturn: This link has no return response.

        """
        save_mail(link)
        raise LinkNoReturn

    @staticmethod
    def loader(driver: typing.Driver, link: Link) -> typing.NoReturn:  # pylint: disable=unused-argument
        """Not implemented.

        Raises:
            LinkNoReturn: This hook is not implemented.

        """
        raise LinkNoReturn
