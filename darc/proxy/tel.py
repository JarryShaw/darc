# -*- coding: utf-8 -*-
"""Telephone Numbers
=======================

The :mod:`darc.proxy.tel` module contains the auxiliary functions
around managing and processing the telephone numbers.

Currently, the :mod:`darc` project directly save the telephone
numbers extracted to the data storage file
:data:`~darc.proxy.tel.PATH` without further processing.

"""

import json
import os
from typing import TYPE_CHECKING

from darc.const import PATH_MISC, get_lock

if TYPE_CHECKING:
    import darc.link as darc_link  # Link

PATH = os.path.join(PATH_MISC, 'tel.txt')
LOCK = get_lock()


def save_tel(link: 'darc_link.Link') -> None:
    """Save telephone number.

    The function will save telephone number to the file
    as defined in :data:`~darc.proxy.tel.PATH`.

    Args:
        link: Link object representing the telephone number.

    """
    with LOCK:  # type: ignore[union-attr]
        with open(PATH, 'a') as file:
            print(json.dumps({
                'src': backref.url if (backref := link.url_backref) is not None else None,  # pylint: disable=used-before-assignment
                'url': link.url,
            }), file=file)
