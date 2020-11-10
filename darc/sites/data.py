# -*- coding: utf-8 -*-
"""Data URI Schemes
======================

The :mod:`darc.sites.data` module is customised to
handle data URI schemes.

"""

import sys

import stem

import darc.typing as typing
from darc.error import LinkNoReturn, render_error
from darc.link import Link
from darc.proxy.data import save_data
from darc.sites._abc import BaseSite


class DataURI(BaseSite):
    """Data URI schemes."""

    @staticmethod
    def crawler(timestamp: typing.Datetime, session: typing.Session, link: Link) -> typing.NoReturn:  # pylint: disable=unused-argument
        """Crawler hook for data URIs.

        Args:
            timestamp: Timestamp of the worker node reference.
            session (:class:`requests.Session`): Session object with proxy settings.
            link: Link object to be crawled.

        Raises:
            LinkNoReturn: This link has no return response.

        """
        try:
            save_data(link)
        except ValueError as error:
            print(render_error(f'[REQUESTS] Failed to save data URI from {link.url} <{error}>',
                            stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
        raise LinkNoReturn(link)

    @staticmethod
    def loader(timestamp: typing.Datetime, driver: typing.Driver, link: Link) -> typing.NoReturn:  # pylint: disable=unused-argument
        """Not implemented.

        Raises:
            LinkNoReturn: This hook is not implemented.

        """
        raise LinkNoReturn(link)
