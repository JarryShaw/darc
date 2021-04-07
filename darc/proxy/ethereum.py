# -*- coding: utf-8 -*-
"""Ethereum Addresses
=======================

The :mod:`darc.proxy.ethereum` module contains the auxiliary functions
around managing and processing the ethereum addresses.

Currently, the :mod:`darc` project directly save the ethereum
addresses extracted to the data storage file
:data:`~darc.proxy.ethereum.PATH` without further processing.

"""

import json
import os
from typing import TYPE_CHECKING

from darc.const import PATH_MISC, get_lock

if TYPE_CHECKING:
    import darc.link as darc_link  # Link

PATH = os.path.join(PATH_MISC, 'ethereum.txt')
LOCK = get_lock()


def save_ethereum(link: 'darc_link.Link') -> None:
    """Save ethereum address.

    The function will save ethereum address to the file
    as defined in :data:`~darc.proxy.ethereum.PATH`.

    Args:
        link: Link object representing the ethereum address.

    """
    with LOCK:  # type: ignore[union-attr]
        with open(PATH, 'a') as file:
            print(json.dumps({
                'src': backref.url if (backref := link.url_backref) is not None else None,  # pylint: disable=used-before-assignment
                'url': link.url_parse.path,
            }), file=file)
