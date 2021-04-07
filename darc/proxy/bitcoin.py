# -*- coding: utf-8 -*-
"""Bitcoin Addresses
=======================

The :mod:`darc.proxy.bitcoin` module contains the auxiliary functions
around managing and processing the bitcoin addresses.

Currently, the :mod:`darc` project directly save the bitcoin
addresses extracted to the data storage file
:data:`~darc.proxy.bitcoin.PATH` without further processing.

"""

import json
import os
from typing import TYPE_CHECKING

from darc.const import PATH_MISC, get_lock

if TYPE_CHECKING:
    import darc.link as darc_link  # Link

PATH = os.path.join(PATH_MISC, 'bitcoin.txt')
LOCK = get_lock()


def save_bitcoin(link: 'darc_link.Link') -> None:
    """Save bitcoin address.

    The function will save bitcoin address to the file
    as defined in :data:`~darc.proxy.bitcoin.PATH`.

    Args:
        link: Link object representing the bitcoin address.

    """
    with LOCK:  # type: ignore[union-attr]
        with open(PATH, 'a') as file:
            print(json.dumps({
                'src': backref.url if (backref := link.url_backref) is not None else None,  # pylint: disable=used-before-assignment
                'url': link.url_parse.path,
            }), file=file)
