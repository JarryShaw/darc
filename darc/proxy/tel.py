# -*- coding: utf-8 -*-
"""Telephone Numbers
=======================

The :mod:`darc.proxy.tel` module contains the auxiliary functions
around managing and processing the telephone numbers.

Currently, the :mod:`darc` project directly save the telephone
numbers extracted to the data storage file
:data:`~darc.proxy.tel.PATH` without further processing.

"""

import os

from darc.const import PATH_MISC, get_lock
from darc.link import Link

PATH = os.path.join(PATH_MISC, 'tel.txt')
LOCK = get_lock()


def save_tel(link: Link) -> None:
    """Save telephone number.

    The function will save telephone number to the file
    as defined in :data:`~darc.proxy.tel.PATH`.

    Args:
        link: Link object representing the telephone number.

    """
    with LOCK:  # type: ignore
        with open(PATH, 'a') as file:
            print(link.url, file=file)
