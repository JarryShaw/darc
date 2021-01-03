# -*- coding: utf-8 -*-
"""WebSocket Addresses
=========================

The :mod:`darc.proxy.ws` module contains the auxiliary functions
around managing and processing the WebSocket addresses.

Currently, the :mod:`darc` project directly save the WebSocket
addresses extracted to the data storage file
:data:`~darc.proxy.ws.PATH` without further processing.

"""

import os
from typing import TYPE_CHECKING

from darc.const import PATH_MISC, get_lock

if TYPE_CHECKING:
    from darc.link import Link

PATH = os.path.join(PATH_MISC, 'ws.txt')
LOCK = get_lock()


def save_ws(link: 'Link') -> None:
    """Save WebSocket addresses.

    The function will save WebSocket address to the file
    as defined in :data:`~darc.proxy.tel.PATH`.

    Args:
        link: Link object representing the WebSocket address.

    """
    with LOCK:  # type: ignore[union-attr]
        with open(PATH, 'a') as file:
            print(link.url, file=file)
