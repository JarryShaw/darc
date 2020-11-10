# -*- coding: utf-8 -*-
"""Base Sites Customisation
==============================

The :mod:`darc.sites._abc` module provides the *abstract base class*
for sites customisation implementation. All sites customisation **must**
inherit from the :class:`~darc.sites._abc.BaseSite` exclusively.

Important:
    The :class:`~darc.sites._abc.BaseSite` class is **NOT** intended to
    be used directly from the :mod:`darc.sites._abc` module. Instead,
    you are recommended to import it from :mod:`darc.sites` respectively.

"""

import darc.typing as typing
from darc.error import LinkNoReturn
from darc.link import Link


class BaseSite:
    """Abstract base class for sites customisation."""

    #: Hostnames (**case insensitive**) the sites customisation is designed for.
    hostname: typing.List[str] = None  # type: ignore

    @staticmethod
    def crawler(timestamp: typing.Datetime, session: typing.Session, link: Link) -> typing.Union[typing.NoReturn, typing.Response]:  # pylint: disable=unused-argument,line-too-long
        """Crawler hook for my site.

        Args:
            timestamp: Timestamp of the worker node reference.
            session: Session object with proxy settings.
            link: Link object to be crawled.

        Raises:
            LinkNoReturn: This link has no return response.

        """
        raise LinkNoReturn(link)

    @staticmethod
    def loader(timestamp: typing.Datetime, driver: typing.Driver, link: Link) -> typing.Union[typing.NoReturn, typing.Driver]:  # pylint: disable=unused-argument,line-too-long
        """Loader hook for my site.

        Args:
            timestamp: Timestamp of the worker node reference.
            driver (selenium.webdriver.Chrome): Web driver object with proxy settings.
            link: Link object to be loaded.

        Raises:
            LinkNoReturn: This link has no return response.

        """
        raise LinkNoReturn(link)
