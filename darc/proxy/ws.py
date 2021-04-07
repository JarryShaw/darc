# -*- coding: utf-8 -*-
"""WebSocket Addresses
=========================

The :mod:`darc.proxy.ws` module contains the auxiliary functions
around managing and processing the WebSocket addresses.

Currently, the :mod:`darc` project directly save the WebSocket
addresses extracted to the data storage file
:data:`~darc.proxy.ws.PATH` without further processing.

"""

import json
import os
from typing import TYPE_CHECKING

from darc.const import PATH_MISC, get_lock

if TYPE_CHECKING:
    import darc.link as darc_link  # Link

PATH = os.path.join(PATH_MISC, 'ws.txt')
LOCK = get_lock()


def save_ws(link: 'darc_link.Link') -> None:
    """Save WebSocket addresses.

    The function will save WebSocket address to the file
    as defined in :data:`~darc.proxy.tel.PATH`.

    Args:
        link: Link object representing the WebSocket address.

    """
    with LOCK:  # type: ignore[union-attr]
        with open(PATH, 'a') as file:
            print(json.dumps({
                'src': backref.url if (backref := link.url_backref) is not None else None,  # pylint: disable=used-before-assignment
                'url': link.url,
            }), file=file)
