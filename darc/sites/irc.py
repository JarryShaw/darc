# -*- coding: utf-8 -*-
"""IRC Addresses
===================

The :mod:`darc.sites.script` module is customised to
handle IRC addresses.

"""

import darc.typing as typing
from darc.error import LinkNoReturn
from darc.link import Link
from darc.proxy.irc import save_irc


def crawler(session: typing.Session, link: Link) -> typing.NoReturn:  # pylint: disable=unused-argument
    """Crawler hook for IRC addresses.

    Args:
        session (:class:`requests.Session`): Session object with proxy settings.
        link: Link object to be crawled.

    Raises:
        LinkNoReturn: This link has no return response.

    """
    save_irc(link)
    raise LinkNoReturn


def loader(driver: typing.Driver, link: Link) -> typing.NoReturn:  # pylint: disable=unused-argument
    """Not implemented.

    Raises:
        LinkNoReturn: This hook is not implemented.

    """
    raise LinkNoReturn
