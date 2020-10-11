# -*- coding: utf-8 -*-
"""Proxy Utilities
=====================

The :mod:`darc.proxy` module provides various proxy support
to the :mod:`darc` project.

"""

import collections

import darc.typing as typing
from darc.requests import i2p_session, null_session, tor_session
from darc.selenium import i2p_driver, null_driver, tor_driver

# link proxy mapping
LINK_MAP: typing.LinkMap = collections.defaultdict(
    lambda: (null_session, null_driver),
    dict(
        tor=(tor_session, tor_driver),
        i2p=(i2p_session, i2p_driver),
    )
)


def register(proxy: str, session: typing.Callable[[bool], typing.Session] = null_session,
             driver: typing.Callable[[], typing.Driver] = null_driver) -> None:
    """Register new proxy type.

    Args:
        proxy: Proxy type.
        session: Session factory function, c.f.
            :func:`darc.requests.null_session`.
        driver: Driver factory function, c.f.
            :func:`darc.selenium.null_driver`.

    """
    LINK_MAP[proxy] = (session, driver)
