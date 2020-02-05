# -*- coding: utf-8 -*-
"""Proxy utilities."""

import darc.typing as typing
from darc.requests import i2p_session, norm_session, tor_session
from darc.selenium import i2p_driver, norm_driver, tor_driver

# link regex mapping
LINK_MAP: typing.LinkMap = dict(
    norm=(norm_session, norm_driver),
    tor=(tor_session, tor_driver),
    i2p=(i2p_session, i2p_driver),
)
