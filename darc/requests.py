# -*- coding: utf-8 -*-
"""Requests Wrapper
======================

The :mod:`darc.requests` module wraps around the |requests|_
module, and provides some simple interface for the :mod:`darc`
project.

"""

import requests
import requests_futures.sessions

import darc.typing as typing
from darc.const import DARC_CPU
from darc.error import UnsupportedLink
from darc.link import Link
from darc.proxy.i2p import I2P_REQUESTS_PROXY
from darc.proxy.tor import TOR_REQUESTS_PROXY


def request_session(link: Link, futures: bool = False) -> typing.Union[typing.Session, typing.FuturesSession]:
    """Get requests session.

    Args:
        link: Link requesting for |Session|_.
        futures: If returns a |FuturesSession|_.

    Returns:
        Union[|Session|_, |FuturesSession|_]: The session object with corresponding proxy settings.

    Raises:
        :exc:`UnsupportedLink`: If the proxy type of ``link``
            if not specified in the :data:`~darc.proxy.LINK_MAP`.

    See Also:
        * :data:`darc.proxy.LINK_MAP`

    """
    from darc.proxy import LINK_MAP  # pylint: disable=import-outside-toplevel

    session, _ = LINK_MAP[link.proxy]
    if session is None:
        raise UnsupportedLink(link.url)
    return session(futures=futures)


def i2p_session(futures: bool = False) -> typing.Union[typing.Session, typing.FuturesSession]:
    """I2P (.i2p) session.

    Args:
        futures: If returns a |FuturesSession|_.

    Returns:
        Union[|Session|_, |FuturesSession|_]: The session object with I2P proxy settings.

    See Also:
        * :data:`darc.proxy.i2p.I2P_REQUESTS_PROXY`

    """
    if futures:
        session = requests_futures.sessions.FuturesSession(max_workers=DARC_CPU)
    else:
        session = requests.Session()
    session.proxies.update(I2P_REQUESTS_PROXY)
    return session


def tor_session(futures: bool = False) -> typing.Union[typing.Session, typing.FuturesSession]:
    """Tor (.onion) session.

    Args:
        futures: If returns a |FuturesSession|_.

    Returns:
        Union[|Session|_, |FuturesSession|_]: The session object with Tor proxy settings.

    See Also:
        * :data:`darc.proxy.tor.TOR_REQUESTS_PROXY`

    """
    if futures:
        session = requests_futures.sessions.FuturesSession(max_workers=DARC_CPU)
    else:
        session = requests.Session()
    session.proxies.update(TOR_REQUESTS_PROXY)
    return session


def null_session(futures: bool = False) -> typing.Union[typing.Session, typing.FuturesSession]:
    """No proxy session.

    Args:
        futures: If returns a |FuturesSession|_.

    Returns:
        Union[|Session|_, |FuturesSession|_]: The session object with no proxy settings.

    """
    if futures:
        session = requests_futures.sessions.FuturesSession(max_workers=DARC_CPU)
    else:
        session = requests.Session()
    return session
