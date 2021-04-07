# -*- coding: utf-8 -*-
# pylint: disable=ungrouped-imports
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

from typing import TYPE_CHECKING

from darc.error import LinkNoReturn

if TYPE_CHECKING:
    from typing import List, NoReturn, Optional, Union

    from requests import Response, Session
    from selenium.webdriver import Chrome as Driver

    import darc.link as darc_link  # Link
    from darc._compat import datetime


class BaseSite:
    """Abstract base class for sites customisation."""

    #: Hostnames (**case insensitive**) the sites customisation is designed for.
    hostname = None  # type: Optional[List[str]]

    @staticmethod
    def crawler(timestamp: 'datetime', session: 'Session', link: 'darc_link.Link') -> 'Union[NoReturn, Response]':  # pylint: disable=unused-argument
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
    def loader(timestamp: 'datetime', driver: 'Driver', link: 'darc_link.Link') -> 'Union[NoReturn, Driver]':  # pylint: disable=unused-argument
        """Loader hook for my site.

        Args:
            timestamp: Timestamp of the worker node reference.
            driver (selenium.webdriver.Chrome): Web driver object with proxy settings.
            link: Link object to be loaded.

        Raises:
            LinkNoReturn: This link has no return response.

        """
        raise LinkNoReturn(link)
