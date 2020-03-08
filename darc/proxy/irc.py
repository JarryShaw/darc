# -*- coding: utf-8 -*-
"""IRC Addresses
===================

The :mod:`darc.proxy.irc` module contains the auxiliary functions
around managing and processing the IRC addresses.

Currently, the :mod:`darc` project directly save the IRC
addresses extracted to the data storage file
:data:`~darc.proxy.irc.PATH` without further processing.

"""

import multiprocessing
import os

from darc.const import PATH_MISC
from darc.link import Link

PATH = os.path.join(PATH_MISC, 'irc.txt')
LOCK = multiprocessing.Lock()


def save_irc(link: Link):
    """Save IRC address.

    The function will save IRC address to the file
    as defined in :data:`~darc.proxy.irc.PATH`.

    Args:
        link: Link object representing the IRC address.

    """
    with LOCK:
        with open(PATH, 'a') as file:
            print(link.url, file=file)
