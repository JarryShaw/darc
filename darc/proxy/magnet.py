# -*- coding: utf-8 -*-
"""Magnet Links
==================

The :mod:`darc.proxy.magnet` module contains the auxiliary functions
around managing and processing the magnet links.

Currently, the :mod:`darc` project directly save the magnet
links extracted to the data storage file
:data:`~darc.proxy.magnet.PATH` without further processing.

"""

import json
import os
from typing import TYPE_CHECKING

from darc.const import PATH_MISC, get_lock

if TYPE_CHECKING:
    import darc.link as darc_link  # Link

PATH = os.path.join(PATH_MISC, 'magnet.txt')
LOCK = get_lock()


def save_magnet(link: 'darc_link.Link') -> None:
    """Save magnet link.

    The function will save magnet link to the file
    as defined in :data:`~darc.proxy.magnet.PATH`.

    Args:
        link: Link object representing the magnet link

    """
    with LOCK:  # type: ignore[union-attr]
        with open(PATH, 'a') as file:
            print(json.dumps({
                'src': backref.url if (backref := link.url_backref) is not None else None,  # pylint: disable=used-before-assignment
                'url': link.url,
            }), file=file)
