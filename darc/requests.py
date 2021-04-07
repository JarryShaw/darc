# -*- coding: utf-8 -*-
# pylint: disable=ungrouped-imports
"""Requests Wrapper
======================

The :mod:`darc.requests` module wraps around the :mod:`requests`
module, and provides some simple interface for the :mod:`darc`
project.

"""

from typing import TYPE_CHECKING

import requests
import requests_futures.sessions as requests_futures_sessions

from darc.const import DARC_CPU
from darc.error import UnsupportedLink
from darc.proxy.i2p import I2P_REQUESTS_PROXY
from darc.proxy.tor import TOR_REQUESTS_PROXY

if TYPE_CHECKING:
    from typing import Optional, Union

    from requests import Session
    from requests_futures.sessions import FuturesSession

    import darc.link as darc_link  # Link


def default_user_agent(name: str = 'python-darc', proxy: 'Optional[str]' = None) -> str:
    """Generates the default user agent.

    Args:
        name: Base name.
        proxy: Proxy type.

    Returns:
        User agent in format of ``{name}/{darc.__version__} ({proxy} Proxy)``.

    """
    from darc import __version__  # pylint: disable=import-outside-toplevel

    if proxy is None:
        ua = f'{name}/{__version__}'
    else:
        ua = f'{name}/{__version__} ({proxy} Proxy)'
    return ua


def request_session(link: 'darc_link.Link', futures: bool = False) -> 'Union[Session, FuturesSession]':
    """Get requests session.

    Args:
        link: Link requesting for requests.Session.
        futures: If returns a :class:`requests_futures.FuturesSession`.

    Returns:
        Union[requests.Session, requests_futures.FuturesSession]:
        The session object with corresponding proxy settings.

    Raises:
        :exc:`UnsupportedLink`: If the proxy type of ``link``
            if not specified in the :data:`~darc.proxy.LINK_MAP`.

    See Also:
        * :data:`darc.proxy.LINK_MAP`

    """
    from darc.proxy import LINK_MAP  # pylint: disable=import-outside-toplevel

    factory, _ = LINK_MAP[link.proxy]
    if factory is None:
        raise UnsupportedLink(link.url)

    return factory(futures=futures)  # type: ignore


def i2p_session(futures: bool = False) -> 'Union[Session, FuturesSession]':
    """I2P (.i2p) session.

    Args:
        futures: If returns a :class:`requests_futures.FuturesSession`.

    Returns:
        Union[requests.Session, requests_futures.FuturesSession]:
        The session object with I2P proxy settings.

    See Also:
        * :data:`darc.proxy.i2p.I2P_REQUESTS_PROXY`

    """
    if futures:
        session = requests_futures_sessions.FuturesSession(max_workers=DARC_CPU)
    else:
        session = requests.Session()

    session.headers['User-Agent'] = default_user_agent(proxy='I2P')
    session.proxies.update(I2P_REQUESTS_PROXY)
    return session


def tor_session(futures: bool = False) -> 'Union[Session, FuturesSession]':
    """Tor (.onion) session.

    Args:
        futures: If returns a :class:`requests_futures.FuturesSession`.

    Returns:
        Union[requests.Session, requests_futures.FuturesSession]:
        The session object with Tor proxy settings.

    See Also:
        * :data:`darc.proxy.tor.TOR_REQUESTS_PROXY`

    """
    if futures:
        session = requests_futures_sessions.FuturesSession(max_workers=DARC_CPU)
    else:
        session = requests.Session()

    session.headers['User-Agent'] = default_user_agent(proxy='Tor')
    session.proxies.update(TOR_REQUESTS_PROXY)
    return session


def null_session(futures: bool = False) -> 'Union[Session, FuturesSession]':
    """No proxy session.

    Args:
        futures: If returns a :class:`requests_futures.FuturesSession`.

    Returns:
        Union[requests.Session, requests_futures.FuturesSession]:
        The session object with no proxy settings.

    """
    if futures:
        session = requests_futures_sessions.FuturesSession(max_workers=DARC_CPU)
    else:
        session = requests.Session()

    session.headers['User-Agent'] = default_user_agent()
    return session
