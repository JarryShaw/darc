# -*- coding: utf-8 -*-
"""Sample file."""


def crawler(session, link):
    """Sample crawler hook."""
    print(f'Crawler hook: {session} - {link}')
    return session


def loader(driver, link):
    """Sample loader hook."""
    print(f'Loader hook: {driver} - {link}')
    return driver
