# -*- coding: utf-8 -*-
"""Proxy utilities."""

from darc.requests import norm_session, tor_session
from darc.selenium import norm_driver, tor_driver

# link regex mapping
LINK_MAP = [
    (r'.*?\.onion', tor_session, tor_driver),
    (r'.*', norm_session, norm_driver),
]
