# -*- coding: utf-8 -*-
"""IRC Addresses
===================

The :mod:`darc.proxy.irc` module contains the auxiliary functions
around managing and processing the IRC addresses.

Currently, the :mod:`darc` project directly save the IRC
addresses extracted to the data storage file
:data:`~darc.proxy.irc.PATH` without further processing.

"""

import os

from darc.const import PATH_MISC, get_lock
from darc.link import Link

PATH = os.path.join(PATH_MISC, 'irc.txt')
LOCK = get_lock()


def save_irc(link: Link) -> None:
    """Save IRC address.

    The function will save IRC address to the file
    as defined in :data:`~darc.proxy.irc.PATH`.

    Args:
        link: Link object representing the IRC address.

    """
    with LOCK:  # type: ignore
        with open(PATH, 'a') as file:
            print(link.url, file=file)
