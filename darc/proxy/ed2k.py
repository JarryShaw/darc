# -*- coding: utf-8 -*-
"""ED2K Magnet Links
=======================

The :mod:`darc.proxy.ed2k` module contains the auxiliary functions
around managing and processing the ED2K magnet links.

Currently, the :mod:`darc` project directly save the ED2K magnet
links extracted to the data storage file
:data:`~darc.proxy.ed2k.PATH` without further processing.

"""

import os

from darc.const import PATH_MISC, get_lock
from darc.link import Link

PATH = os.path.join(PATH_MISC, 'ed2k.txt')
LOCK = get_lock()


def save_ed2k(link: Link) -> None:
    """Save ed2k magnet link.

    The function will save ED2K magnet link to the file
    as defined in :data:`~darc.proxy.ed2k.PATH`.

    Args:
        link: Link object representing the ED2K magnet links.

    """
    with LOCK:  # type: ignore
        with open(PATH, 'a') as file:
            print(link.url, file=file)
