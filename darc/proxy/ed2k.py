# -*- coding: utf-8 -*-
"""ED2K Magnet Links
=======================

The :mod:`darc.proxy.ed2k` module contains the auxiliary functions
around managing and processing the ED2K magnet links.

Currently, the :mod:`darc` project directly save the ED2K magnet
links extracted to the data storage file
:data:`~darc.proxy.ed2k.PATH` without further processing.

"""

import multiprocessing
import os

from darc.const import PATH_MISC
from darc.link import Link

PATH = os.path.join(PATH_MISC, 'ed2k.txt')
LOCK = multiprocessing.Lock()


def save_ed2k(link: Link):
    """Save ed2k magnet link.

    The function will save ED2K magnet link to the file
    as defined in :data:`~darc.proxy.ed2k.PATH`.

    Args:
        link: Link object representing the ED2K magnet links.

    """
    with LOCK:
        with open(PATH, 'a') as file:
            print(link.url, file=file)
