# -*- coding: utf-8 -*-
"""Default hooks."""

import time

import darc.typing as typing
from darc.const import SE_WAIT
from darc.link import Link


def crawler(session: typing.Session, link: Link) -> typing.Response:
    """Default crawler hook."""
    response = session.get(link.url)
    return response


def loader(driver: typing.Driver, link: Link) -> typing.Driver:
    """Default loader hook."""
    driver.get(link.url)

    # wait for page to finish loading
    if SE_WAIT is not None:
        time.sleep(SE_WAIT)

    return driver
