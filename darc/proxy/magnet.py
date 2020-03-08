# -*- coding: utf-8 -*-
"""Magnet Links
==================

The :mod:`darc.proxy.magnet` module contains the auxiliary functions
around managing and processing the magnet links.

Currently, the :mod:`darc` project directly save the magnet
links extracted to the data storage file
:data:`~darc.proxy.magnet.PATH` without further processing.

"""

import multiprocessing
import os

from darc.const import PATH_MISC
from darc.link import Link

PATH = os.path.join(PATH_MISC, 'magnet.txt')
LOCK = multiprocessing.Lock()


def save_magnet(link: Link):
    """Save magnet link.

    The function will save magnet link to the file
    as defined in :data:`~darc.proxy.magnet.PATH`.

    Args:
        link: Link object representing the magnet link

    """
    with LOCK:
        with open(PATH, 'a') as file:
            print(link.url, file=file)
