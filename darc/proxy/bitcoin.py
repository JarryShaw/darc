# -*- coding: utf-8 -*-
"""Bitcoin Addresses
=======================

The :mod:`darc.proxy.bitcoin` module contains the auxiliary functions
around managing and processing the bitcoin addresses.

Currently, the :mod:`darc` project directly save the bitcoin
addresses extracted to the data storage file
:data:`~darc.proxy.bitcoin.PATH` without further processing.

"""

import multiprocessing
import os

from darc.const import PATH_MISC
from darc.link import Link

PATH = os.path.join(PATH_MISC, 'bitcoin.txt')
LOCK = multiprocessing.Lock()


def save_bitcoin(link: Link):
    """Save bitcoin address.

    The function will save bitcoin address to the file
    as defined in :data:`~darc.proxy.bitcoin.PATH`.

    Args:
        link: Link object representing the bitcoin address.

    """
    with LOCK:
        with open(PATH, 'a') as file:
            print(link.url_parse.path, file=file)
