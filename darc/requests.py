# -*- coding: utf-8 -*-
"""Requests wrapper."""
# pylint: disable=unused-wildcard-import

import requests

import darc.typing as typing
from darc.proxy.tor import TOR_REQUESTS_PROXY
from darc.proxy.i2p import I2P_REQUESTS_PROXY


def i2p_session() -> typing.Session:
    """I2P (.i2p) session."""
    session = requests.Session()
    session.proxies.update(I2P_REQUESTS_PROXY)
    return session


def tor_session() -> typing.Session:
    """Tor (.onion) session."""
    session = requests.Session()
    session.proxies.update(TOR_REQUESTS_PROXY)
    return session


def norm_session() -> typing.Session:
    """Normal session"""
    return requests.Session()
