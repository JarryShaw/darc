# -*- coding: utf-8 -*-
"""Requests wrapper."""
# pylint: disable=unused-wildcard-import

import requests

import darc.typing as typing
from darc.const import TOR_PORT


def tor_session() -> typing.Session:
    """Tor (.onion) session."""
    session = requests.Session()
    session.proxies.update({
        # c.f. https://stackoverflow.com/a/42972942
        'http':  f'socks5h://localhost:{TOR_PORT}',
        'https': f'socks5h://localhost:{TOR_PORT}'
    })
    return session


def norm_session() -> typing.Session:
    """Normal session"""
    return requests.Session()
