# -*- coding: utf-8 -*-
"""Proxy utilities."""

import collections

import darc.typing as typing
from darc.requests import i2p_session, null_session, tor_session
from darc.selenium import i2p_driver, null_driver, tor_driver

# link regex mapping
LINK_MAP: typing.LinkMap = collections.defaultdict(
    lambda: (null_session, null_driver),
    dict(
        tor=(tor_session, tor_driver),
        i2p=(i2p_session, i2p_driver),
    )
)
