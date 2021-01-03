# -*- coding: utf-8 -*-
# pylint: disable=ungrouped-imports,unsubscriptable-object
"""Proxy Utilities
=====================

The :mod:`darc.proxy` module provides various proxy support
to the :mod:`darc` project.

"""

import collections
from typing import TYPE_CHECKING

from darc.requests import i2p_session, null_session, tor_session
from darc.selenium import i2p_driver, null_driver, tor_driver

if TYPE_CHECKING:
    from typing import Callable, DefaultDict, Tuple, Union

    from requests import Session
    from requests_futures.sessions import FuturesSession
    from selenium.webdriver import Chrome as Driver

    SessionFactory = Callable[[bool], Union[Session, FuturesSession]]
    DriverFactory = Callable[[], Driver]
    LinkMap = DefaultDict[str, Tuple[SessionFactory, DriverFactory]]

# link proxy mapping
LINK_MAP = collections.defaultdict(
    lambda: (null_session, null_driver),
    {
        'tor': (tor_session, tor_driver),
        'i2p': (i2p_session, i2p_driver),
    }
)  # type: LinkMap


def register(proxy: str, session: 'SessionFactory' = null_session,
             driver: 'DriverFactory' = null_driver) -> None:
    """Register new proxy type.

    Args:
        proxy: Proxy type.
        session: Session factory function, c.f.
            :func:`darc.requests.null_session`.
        driver: Driver factory function, c.f.
            :func:`darc.selenium.null_driver`.

    """
    LINK_MAP[proxy] = (session, driver)
